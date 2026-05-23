# 🔁 Replay and Integrity Guide (Gov-OS Hardened)

Parikshak Gov-OS enforces absolute state integrity and deterministic audit tracking. Every state mutation is represented as an event in a local SQLite event journal.

---

## 1. Immutable Event Sourcing Model

The core database operates as an **Immutable Event Journal**:
- **Triggers**: DB triggers disallow any `UPDATE` or `DELETE` statements on the `events` table.
- **Monotonicity**: The `event_sequence` is sequential and strictly increasing.
- **Envelope Signatures**: Every event requires a full Governance Envelope containing cryptographic checks (`payload_checksum`, `parent_event_hash`, `approval_token`).

---

## 2. Replay-Safe Reconstruction

Read models (e.g. `candidate_profiles`, `task_lineage`, etc.) are reconstructed purely by replaying the journal from sequence 1:
- **Determinism**: The reconstruction process uses canonical JSON serialization (sorted keys, no spaces, UTF-8 normalization) and sorted dictionary keys.
- **No Side Effects**: Reading/reconstruction performs zero database mutations.
- **No Runtime Mutation**: Model schemas are statically validated against the schema registry and cannot drift at runtime.

---

## 3. Startup Safety Gate

Every database initialization executes `scan_and_verify()` as a startup gate. Boot is blocked if any of the following 6 integrity flags are detected:
- `HASH_MISMATCH`: The stored event checksum/hash does not match the re-computed hash.
- `ORPHAN_EVENT`: An event exists whose parent hash cannot be resolved or doesn't match the preceding event hash.
- `SEQUENCE_BREAK`: Monotonicity is violated or gaps exist in the sequence log.
- `SCHEMA_DRIFT`: Logged event payload does not match its registry-defined Pydantic schema.
- `SNAPSHOT_DIVERGENCE`: Replaying events up to a sequence results in a state hash that diverges from the recorded checkpoint hash.
- `CHECKPOINT_MISMATCH`: Local database state diverges from the manifest records stored in the backups folder.

---

## 4. Corruption Recovery & Rollbacks

- **Rollback Anchors**: The system can rollback to any arbitrary sequence number `N`. It achieves this by cleaning the read model tables and replaying sequence `1` through `N`.
- **Audit Logs Reconstruction**: In the event of SQLite file corruption, database state can be reconstructed by importing and replaying the JSONL audit log journal files.
