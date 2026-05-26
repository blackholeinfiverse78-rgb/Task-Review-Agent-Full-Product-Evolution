import sqlite3
import os
import json
import hashlib
import uuid
import queue
import threading
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from canonical_db.contracts import GovernanceEnvelope, ENTITY_SCHEMAS, canonical_json

# Primary keys for read model indexing
PRIMARY_KEYS = {
    "candidate_profiles": "candidate_id",
    "task_lineage": "task_id",
    "review_history": "review_id",
    "assignment_history": "assignment_id",
    "reasoning_artifacts": "artifact_id",
    "ecosystem_dependency_context": "dependency_id",
    "product_mapping": "mapping_id",
    "strategic_notes": "note_id",
    "learning_signals": "signal_id"
}

GENESIS_HASH = "0" * 64

class SingleWriterQueue:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.lock = threading.Lock()

    def submit(self, db_instance, envelope: GovernanceEnvelope, actor: str) -> Dict[str, Any]:
        # Mutex protection to serialize writes, enforcing deterministic commit ordering
        with self.lock:
            return db_instance._append_event_sync(envelope, actor)

_writer_queues = {}
_queues_lock = threading.Lock()

def get_writer_queue(db_path: str) -> SingleWriterQueue:
    abs_path = os.path.abspath(db_path)
    with _queues_lock:
        if abs_path not in _writer_queues:
            _writer_queues[abs_path] = SingleWriterQueue(abs_path)
        return _writer_queues[abs_path]

class CanonicalDB:
    def __init__(self, db_path: str = "storage/canonical_db.sqlite"):
        self.db_path = db_path
        # Ensure directories exist
        os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        
        # Enforce WAL mode at boot
        self.conn.execute("PRAGMA journal_mode=WAL;")
        self.conn.execute("PRAGMA synchronous=NORMAL;")
        
        try:
            self._init_db()
            self.scan_and_verify()
        except Exception:
            self.conn.close()
            raise

    def _init_db(self):
        cursor = self.conn.cursor()
        # Create events table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT UNIQUE NOT NULL,
                trace_id TEXT NOT NULL,
                schema_version TEXT NOT NULL,
                actor TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                event_type TEXT NOT NULL,
                lineage_reference TEXT,
                payload TEXT NOT NULL,
                parent_event_hash TEXT NOT NULL,
                event_hash TEXT NOT NULL,
                checksum TEXT NOT NULL
            );
        """)
        # Triggers to prevent UPDATE and DELETE
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS prevent_update_events
            BEFORE UPDATE ON events
            BEGIN
                SELECT RAISE(FAIL, 'UPDATE operation not allowed on append-only event journal');
            END;
        """)
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS prevent_delete_events
            BEFORE DELETE ON events
            BEGIN
                SELECT RAISE(FAIL, 'DELETE operation not allowed on append-only event journal');
            END;
        """)
        self.conn.commit()

    def append_event(self, envelope: GovernanceEnvelope, actor: str) -> Dict[str, Any]:
        queue_instance = get_writer_queue(self.db_path)
        return queue_instance.submit(self, envelope, actor)

    def _append_event_sync(self, envelope: GovernanceEnvelope, actor: str) -> Dict[str, Any]:
        # Called only from SingleWriterQueue.submit() which holds threading.Lock.
        # No additional file lock needed — the threading.Lock already serializes all writes.
        envelope.validate_payload()

        from canonical_db.pipeline import AUTHORIZED_GOVERNORS
        from canonical_db.contracts import AutonomousReleaseBlocked

        approval_state = "HUMAN_APPROVED" if envelope.authorized_by in AUTHORIZED_GOVERNORS else "PENDING"
        if envelope.event_type == "assignment_history" or envelope.authorized_by == "AI_Orchestrator_Agent":
            if approval_state != "HUMAN_APPROVED":
                raise AutonomousReleaseBlocked("GOVERNANCE_REJECT: Autonomous release is blocked.")

        cursor = self.conn.cursor()
        cursor.execute("SELECT event_hash FROM events ORDER BY sequence DESC LIMIT 1")
        row = cursor.fetchone()
        parent_hash = row["event_hash"] if row else GENESIS_HASH

        if envelope.parent_event_hash and envelope.parent_event_hash != "0"*64 and envelope.parent_event_hash != parent_hash:
            raise ValueError(f"CHECKPOINT_MISMATCH: parent event hash mismatch. Expected {parent_hash}, got {envelope.parent_event_hash}")

        envelope.parent_event_hash = parent_hash

        event_id = f"evt-{uuid.uuid4().hex[:12]}"
        timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        checksum = envelope.compute_checksum()
        payload_str = canonical_json(envelope.payload)

        lineage_ref = envelope.lineage_reference or ""
        hash_input = (
            f"{event_id}|{envelope.trace_id}|{envelope.schema_version}|{actor}|"
            f"{timestamp}|{envelope.event_type}|{lineage_ref}|{payload_str}|{parent_hash}"
        )
        event_hash = hashlib.sha256(hash_input.encode('utf-8')).hexdigest()

        cursor.execute("""
            INSERT INTO events (
                event_id, trace_id, schema_version, actor, timestamp,
                event_type, lineage_reference, payload, parent_event_hash,
                event_hash, checksum
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            event_id, envelope.trace_id, envelope.schema_version, actor, timestamp,
            envelope.event_type, envelope.lineage_reference, payload_str, parent_hash,
            event_hash, checksum
        ))
        self.conn.commit()

        cursor.execute("SELECT * FROM events WHERE event_id = ?", (event_id,))
        new_row = cursor.fetchone()
        return dict(new_row)

    def get_last_event(self) -> Optional[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM events ORDER BY sequence DESC LIMIT 1")
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_all_events(self) -> List[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM events ORDER BY sequence ASC")
        return [dict(row) for row in cursor.fetchall()]

    def reconstruct_state(self, up_to_seq: Optional[int] = None) -> Dict[str, Dict[str, Any]]:
        """Reconstruct read model state up to sequence (rollback logic)"""
        state = {k: {} for k in PRIMARY_KEYS.keys()}
        cursor = self.conn.cursor()

        if up_to_seq is not None:
            cursor.execute("SELECT * FROM events WHERE sequence <= ? ORDER BY sequence ASC", (up_to_seq,))
        else:
            cursor.execute("SELECT * FROM events ORDER BY sequence ASC")

        for row in cursor.fetchall():
            event_type = row["event_type"]
            if event_type not in PRIMARY_KEYS:
                continue
            
            payload = json.loads(row["payload"])
            pk_field = PRIMARY_KEYS[event_type]
            pk_val = payload.get(pk_field)
            if pk_val:
                state[event_type][pk_val] = payload

        return state

    def scan_and_verify(self) -> bool:
        """Scan boot check. Verifies the SHA256 chain and checksums."""
        from canonical_db.integrity import IntegrityValidator
        validator = IntegrityValidator(self.db_path)
        scan = validator.run_full_scan()
        if not scan["valid"]:
            raise ValueError(f"STARTUP_SAFETY_GATE_BLOCKED: {scan['reason']}. Errors: {scan['errors']}")
        return True

    def close(self):
        self.conn.close()
