# Deterministic Gap Report — Parikshak Gov-OS v6.0.0

**Date:** 2026-05-23

---

## Evaluated Risk Areas

### 1. Timestamps as Sequencing Logic
- **Risk:** `datetime.utcnow()` is non-monotonic under clock drift or NTP corrections.
- **Resolution:** State reconstruction in `CanonicalDB.reconstruct_state()` orders exclusively by `sequence` (SQLite `AUTOINCREMENT` integer PK). Timestamps are stored as metadata only and never used for ordering or hash chaining.
- **Gap:** CLOSED

### 2. Multi-threaded Write Ordering
- **Risk:** Concurrent API workers could interleave writes, producing non-deterministic sequence ordering.
- **Resolution:** `SingleWriterQueue` (one per `db_path`, keyed by absolute path) serializes all `_append_event_sync()` calls under `threading.Lock`. Sequence numbers are assigned by SQLite `AUTOINCREMENT` inside the lock — no gaps, no reordering.
- **Gap:** CLOSED

### 3. JSON Serialization Nondeterminism
- **Risk:** Python `json.dumps()` without `sort_keys` produces nondeterministic key ordering across Python versions and dict insertion order.
- **Resolution:** `canonical_json()` enforces `sort_keys=True`, `separators=(',', ':')`, `ensure_ascii=False`, and `unicodedata.normalize('NFC', ...)`. SHA-256 checksums computed on this canonical form are bitwise identical across runs and platforms.
- **Gap:** CLOSED

### 4. Float Representation Drift
- **Risk:** Float serialization may differ across CPU architectures or Python versions.
- **Resolution:** All float fields in Pydantic schemas (`performance_score`, `improvement_ratio`, `score`) are bounded `float` types. Python's `json.dumps` uses IEEE 754 double precision consistently. No custom float serializers that could drift.
- **Gap:** CLOSED

### 5. Snapshot State Hash Divergence
- **Risk:** A snapshot manifest could reference a state hash that diverges from the actual replayed state.
- **Resolution:** `BackupManager.create_snapshot()` computes `state_hash` by calling `db.reconstruct_state(up_to_seq=last_seq)` and hashing the canonical JSON. `IntegrityValidator.run_full_scan()` re-replays and re-computes this hash on every boot, raising `SNAPSHOT_DIVERGENCE` on mismatch.
- **Gap:** CLOSED

### 6. Orphan Event Risk
- **Risk:** An event could be inserted with a `parent_event_hash` that does not match the actual last event, creating a detached chain.
- **Resolution:** `_append_event_sync()` fetches the last `event_hash` from the DB inside the write lock and overwrites `envelope.parent_event_hash` before computing the new `event_hash`. If the caller provides a non-zero `parent_event_hash` that doesn't match, a `CHECKPOINT_MISMATCH` error is raised.
- **Gap:** CLOSED

### 7. Replay Reconstruction Divergence
- **Risk:** Replaying a JSONL export into a new DB could produce a different state than the original.
- **Resolution:** `RecoveryTool.reconstruct_db_from_jsonl()` inserts events with their original `event_id`, `timestamp`, `event_hash`, and `checksum` preserved. `IntegrityValidator.run_full_scan()` is run on the reconstructed DB — any divergence causes the reconstructed file to be deleted and an error raised.
- **Gap:** CLOSED

### 8. Adapter Isolation
- **Risk:** Ecosystem adapters could accumulate hidden state or write directly to the canonical DB.
- **Resolution:** All adapters under `/integrations/` are read-only consumers. `EcosystemIntegrator.process_niyantran_submission()` returns a receipt without writing to the DB. `propagate_governed_approval()` requires a fully validated `GovernanceEnvelope` with human sign-off before calling `GovernedPipeline.submit_mutation()`.
- **Gap:** CLOSED

---

## Gap Verdict

**No active deterministic gaps found.**

All state reconstruction paths produce bitwise-identical outputs given the same event journal. Replay equivalence is verified by TEST-12 (state hash match across two sequential reconstructions) and TEST-05 (JSONL export → reconstruct → verify).
