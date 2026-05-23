import os
import sqlite3
import json
from typing import Dict, Any, List, Optional
from canonical_db.db import CanonicalDB
from canonical_db.contracts import GovernanceEnvelope
from canonical_db.integrity import IntegrityValidator

class RecoveryTool:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def rollback_to_sequence(self, target_seq: int) -> Dict[str, Dict[str, Any]]:
        """
        Rollback state to a specific sequence number.
        Returns the reconstructed read model state.
        This does NOT mutate the event journal itself, preserving immutability.
        """
        db = CanonicalDB(self.db_path)
        try:
            # Reconstruct read model up to target_seq
            state = db.reconstruct_state(up_to_seq=target_seq)
            return state
        finally:
            db.close()

    def export_journal_to_jsonl(self, jsonl_path: str) -> int:
        """Exports the entire event journal to a raw JSONL file for forensic backup."""
        db = CanonicalDB(self.db_path)
        events = db.get_all_events()
        db.close()
        
        count = 0
        with open(jsonl_path, "w", encoding="utf-8") as f:
            for event in events:
                f.write(json.dumps(event) + "\n")
                count += 1
        return count

    def reconstruct_db_from_jsonl(self, jsonl_path: str, new_db_path: str) -> bool:
        """
        Reconstructs a new, clean SQLite database from a raw JSONL event journal.
        This verifies the integrity chain step-by-step and inserts them.
        """
        if os.path.exists(new_db_path):
            os.remove(new_db_path)

        # Initialize new db
        new_db = CanonicalDB(new_db_path)
        
        # Read and parse JSONL events
        events = []
        with open(jsonl_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    events.append(json.loads(line.strip()))

        # Sort by sequence to ensure proper order
        events = sorted(events, key=lambda x: x["sequence"])

        cursor = new_db.conn.cursor()
        
        # We append each event, verifying integrity
        # To preserve exact hashes, actors, event_ids, and timestamps from the original journal,
        # we insert them directly into the table, and then run scan_and_verify on the final database.
        for event in events:
            # Check schema validation on insert
            payload_dict = json.loads(event["payload"])
            envelope = GovernanceEnvelope(
                trace_id=event["trace_id"],
                schema_version=event["schema_version"],
                actor=event["actor"],
                actor_role=event.get("actor_role", "operator"),
                timestamp=event["timestamp"],
                lineage_reference=event.get("lineage_reference", "lineage-default"),
                event_type=event["event_type"],
                payload=payload_dict,
                approval_token=event.get("approval_token", "token-default-123"),
                payload_checksum=event.get("checksum") or event.get("payload_checksum"),
                parent_event_hash=event.get("parent_event_hash", "0"*64)
            )
            envelope.validate_payload()

            cursor.execute("""
                INSERT INTO events (
                    sequence, event_id, trace_id, schema_version, actor, timestamp,
                    event_type, lineage_reference, payload, parent_event_hash,
                    event_hash, checksum
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event["sequence"], event["event_id"], event["trace_id"], event["schema_version"],
                event["actor"], event["timestamp"], event["event_type"], event["lineage_reference"],
                event["payload"], event["parent_event_hash"], event["event_hash"], event["checksum"]
            ))
            
        new_db.conn.commit()
        
        # Run integrity scanner to verify the reconstructed db
        validator = IntegrityValidator(new_db_path)
        scan_result = validator.run_full_scan()
        new_db.close()
        
        if not scan_result["valid"]:
            if os.path.exists(new_db_path):
                os.remove(new_db_path)
            raise ValueError(f"Reconstructed database failed integrity verification: {scan_result['reason']}")

        return True
