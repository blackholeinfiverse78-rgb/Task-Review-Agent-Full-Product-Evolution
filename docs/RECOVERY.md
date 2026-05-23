# 🩹 Gov-OS Disaster Recovery & Reconstruction Manual

This manual describes how to recover system state from database corruptions, data loss, or system divergence using Parikshak's event sourcing infrastructure.

---

## 1. Diagnostics and Identification
If the system fails to boot, it will raise `STARTUP_SAFETY_GATE_BLOCKED` and log the specific integrity issue. Match the error string to find the resolution:

- **`HASH_MISMATCH`**: Event payload or checksum in SQLite events table has been mutated.
- **`SEQUENCE_BREAK`**: Sequence indices are corrupted or missing.
- **`SNAPSHOT_DIVERGENCE`**: Local backups folder has snapshot state files that do not match the current database's event-sourcing reconstruction.

---

## 2. Recovery Playbook A: Reconstruct DB from Audit JSONL

If the database file `storage/canonical_db.sqlite` is lost or corrupted:
1. Re-initialize a clean SQLite database structure.
2. Run the `reconstruct` endpoint or recovery script to read and replay the JSONL audit journal log:
   ```bash
   curl -X POST http://localhost:8000/api/v1/gov-os/reconstruct \
     -H "Content-Type: application/json" \
     -d '{
       "jsonl_path": "storage/audit_logs/audit_2026-05-23.jsonl",
       "new_db_path": "storage/canonical_db.sqlite"
     }'
   ```
3. Re-run `python -X utf8 scratch/test_operating_system.py` to verify the DB is healthy.

---

## 3. Recovery Playbook B: Rollback to Safe Checkpoint Anchor

If a bad event is committed (e.g. human error during approval):
1. Identify the last clean event sequence number `N`.
2. Rollback the database using the rollback endpoint:
   ```bash
   curl -X POST http://localhost:8000/api/v1/gov-os/rollback \
     -H "Content-Type: application/json" \
     -d '{"target_seq": N}'
   ```
3. This cleans all read model tables and replays events exactly from sequence 1 up to sequence `N`, updating the active snapshot reference.

---

## 4. Recovery Playbook C: Restore Snapshot Manifest

To restore the system directly to a snapshot backup:
1. Locate the correct snapshot manifest JSON inside `storage/backups/`.
2. Invoke the restore program via Python:
   ```python
   from canonical_db.backup import BackupManager
   BackupManager("storage/canonical_db.sqlite").verify_and_restore("storage/backups/snapshot_seq_N_timestamp.json")
   ```
3. Restart the FastAPI backend.
