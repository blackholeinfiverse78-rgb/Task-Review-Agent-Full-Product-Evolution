import sqlite3
import os
import json
import hashlib
from typing import Dict, Any, List
from canonical_db.contracts import ENTITY_SCHEMAS

class IntegrityValidator:
    def __init__(self, db_path: str, backup_dir: str = "storage/backups"):
        self.db_path = db_path
        self.backup_dir = backup_dir

    def run_full_scan(self) -> Dict[str, Any]:
        """Performs a comprehensive corruption scan, detecting the 6 core Gov-OS failure modes."""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM events ORDER BY sequence ASC")
            rows = cursor.fetchall()
        except sqlite3.OperationalError as e:
            return {
                "valid": False,
                "reason": f"Database file error or table missing: {e}",
                "errors": [f"BOOT_INTEGRITY_REJECTION: {e}"]
            }
        finally:
            conn.close()

        errors = []
        last_hash = "0" * 64
        seen_hashes = {"0" * 64}
        expected_seq = 1

        for row in rows:
            seq = row["sequence"]
            event_id = row["event_id"]
            trace_id = row["trace_id"]
            schema_version = row["schema_version"]
            actor = row["actor"]
            timestamp = row["timestamp"]
            event_type = row["event_type"]
            lineage_ref = row["lineage_reference"] or ""
            payload_str = row["payload"]
            parent_event_hash = row["parent_event_hash"]
            event_hash = row["event_hash"]
            checksum = row["checksum"]

            # 1. SEQUENCE_BREAK
            if seq != expected_seq:
                errors.append(f"SEQUENCE_BREAK: Expected sequence {expected_seq}, found {seq}")
                expected_seq = seq

            # 2. ORPHAN_EVENT
            if parent_event_hash not in seen_hashes:
                errors.append(f"ORPHAN_EVENT: Event seq {seq} ({event_id}) refers to unknown parent hash {parent_event_hash}")
            elif parent_event_hash != last_hash:
                errors.append(f"HASH_MISMATCH: Event seq {seq} ({event_id}) parent hash mismatch. Expected {last_hash}, found {parent_event_hash}")

            # 3. HASH_MISMATCH (payload checksum)
            from canonical_db.contracts import canonical_json
            try:
                payload_dict = json.loads(payload_str)
                # Compute checksum of canonical payload
                computed_checksum = hashlib.sha256(canonical_json(payload_dict).encode('utf-8')).hexdigest()
            except Exception:
                computed_checksum = hashlib.sha256(payload_str.encode('utf-8')).hexdigest()

            if computed_checksum != checksum:
                errors.append(f"HASH_MISMATCH: Event seq {seq} ({event_id}) checksum mismatch. Stored={checksum}, Computed={computed_checksum}")

            # 4. HASH_MISMATCH (chain integrity)
            hash_input = (
                f"{event_id}|{trace_id}|{schema_version}|{actor}|"
                f"{timestamp}|{event_type}|{lineage_ref}|{payload_str}|{parent_event_hash}"
            )
            computed_hash = hashlib.sha256(hash_input.encode('utf-8')).hexdigest()
            if computed_hash != event_hash:
                errors.append(f"HASH_MISMATCH: Event seq {seq} ({event_id}) hash mismatch. Stored={event_hash}, Computed={computed_hash}")

            # 5. SCHEMA_DRIFT
            if event_type not in ENTITY_SCHEMAS:
                errors.append(f"SCHEMA_DRIFT: Event seq {seq} has unknown event_type '{event_type}'")
            else:
                try:
                    ENTITY_SCHEMAS[event_type](**payload_dict)
                except Exception as e:
                    errors.append(f"SCHEMA_DRIFT: Event seq {seq} failed schema validation: {e}")

            seen_hashes.add(event_hash)
            last_hash = event_hash
            expected_seq += 1

        # 6. Checkpoint and Snapshot Verification (SNAPSHOT_DIVERGENCE, CHECKPOINT_MISMATCH)
        if os.path.exists(self.backup_dir):
            for file in os.listdir(self.backup_dir):
                if file.endswith(".json") and file.startswith("snapshot_seq_"):
                    manifest_path = os.path.join(self.backup_dir, file)
                    try:
                        with open(manifest_path, "r", encoding="utf-8") as f:
                            manifest = json.load(f)
                        
                        last_seq = manifest.get("last_seq")
                        head_hash = manifest.get("head_hash")
                        state_hash = manifest.get("state_hash")

                        # If the sequence is within our DB
                        if last_seq and last_seq <= len(rows):
                            db_event = rows[last_seq - 1]
                            if db_event["event_hash"] != head_hash:
                                errors.append(f"CHECKPOINT_MISMATCH: Manifest {file} hash {head_hash} doesn't match DB {db_event['event_hash']}")
                            
                            # Verify snapshot state divergence
                            reconstructed = {k: {} for k in ENTITY_SCHEMAS.keys()}
                            from canonical_db.db import PRIMARY_KEYS
                            for r in rows[:last_seq]:
                                ev_type = r["event_type"]
                                if ev_type in PRIMARY_KEYS:
                                    pk_field = PRIMARY_KEYS[ev_type]
                                    p_dict = json.loads(r["payload"])
                                    pk_val = p_dict.get(pk_field)
                                    if pk_val:
                                        reconstructed[ev_type][pk_val] = p_dict
                            
                            reconstructed_str = canonical_json(reconstructed)
                            computed_state_hash = hashlib.sha256(reconstructed_str.encode('utf-8')).hexdigest()
                            if state_hash and computed_state_hash != state_hash:
                                errors.append(f"SNAPSHOT_DIVERGENCE: Replayed state hash for seq {last_seq} doesn't match checkpoint state_hash {state_hash}")
                    except Exception as e:
                        errors.append(f"CHECKPOINT_MISMATCH: Failed to verify manifest {file}: {e}")

        if errors:
            return {
                "valid": False,
                "reason": f"Found {len(errors)} integrity issues",
                "errors": errors
            }
        
        return {
            "valid": True,
            "events_scanned": len(rows),
            "head_hash": last_hash
        }
