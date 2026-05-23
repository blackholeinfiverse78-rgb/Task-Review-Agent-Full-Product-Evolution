# 🚀 Gov-OS Deployment Checklist (v6.0.0)

This checklist details the steps to deploy Parikshak Gov-OS to staging and production environments safely.

---

## 📋 1. Pre-Deployment Verification

### Safety Gates & Integrity Checks
- [ ] Verify SQLite trigger generation scripts are included in the migration files.
- [ ] Confirm startup safety gate scanner executes on database boot, scanning for all 6 integrity errors:
  - `HASH_MISMATCH`
  - `ORPHAN_EVENT`
  - `SEQUENCE_BREAK`
  - `SCHEMA_DRIFT`
  - `SNAPSHOT_DIVERGENCE`
  - `CHECKPOINT_MISMATCH`
- [ ] Verify that manual updates/deletes raise database engine constraint exceptions.

### Concurrency & Serializability
- [ ] Single-writer lock is enabled.
- [ ] All API handlers route mutations through `pipeline.submit_mutation()` using the thread-safe queue.

### Human Approval Locks
- [ ] Verify that `AutonomousReleaseBlocked` exceptions are raised for AI-initiated task assignments.
- [ ] Validate that the GPT bridge has no mutation rights on the live database.

---

## 🚀 2. Deployment Steps

### Step 1: Initialize Database
- Build the database container or deploy the local sqlite database file to `storage/canonical_db.sqlite`.
- Ensure write-ahead logging (WAL mode) is active.
- Verify trigger creation matches schema specifications.

### Step 2: Boot & Safety Gate Scan
- Run the system startup check.
- Observe logs for:
  ```text
  INFO: [STARTUP_GATE] Scanning database events...
  INFO: [STARTUP_GATE] Scan complete. 0 issues found.
  ```

### Step 3: Run Diagnostic Suite
- Execute the test suite on target staging server:
  ```bash
  python -X utf8 scratch/test_operating_system.py
  ```
- Verify 12/12 test outcomes pass.

---

## 🔄 3. Rollback & Recovery Runbook

### Checkpoint Restore
If a deployment fails or data corruption is introduced:
1. Locate the correct snapshot manifest JSON inside `storage/backups/`.
2. Execute the verification and restore routine:
   ```python
   BackupManager("storage/canonical_db.sqlite").verify_and_restore("storage/backups/snapshot_seq_N_timestamp.json")
   ```
3. Re-boot the system to trigger the startup safety gate.

### Reconstruct from Journal
If the SQLite file is completely lost:
1. Re-initialize a blank database structure.
2. Run the recovery tool to import and replay the JSONL audit log journal:
   ```python
   RecoveryTool("storage/canonical_db.sqlite").reconstruct_db_from_jsonl("storage/audit_logs/audit_file.jsonl", "storage/reconstructed.sqlite")
   ```
