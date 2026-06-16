# Gov-OS Governance & Security Risk Matrix — v6.0.0

**Date:** 2026-05-23

| Risk ID | Description | Severity | Mitigation | Verification | Status |
|---|---|---|---|---|---|
| RSK-01 | Direct SQL mutation bypassing API layers | Critical | SQLite `BEFORE UPDATE`/`BEFORE DELETE` triggers unconditionally raise `FAIL`. No raw SQL write path exists outside `_append_event_sync`. | TEST-01, TEST-03 | VERIFIED |
| RSK-02 | Stale lock starvation from crashed processes | High | `FileLock` uses PID-based stale lock detection (`OpenProcess` on Windows, `os.kill(0)` on POSIX). Stale locks deleted automatically. | TEST-10 (concurrency) | VERIFIED |
| RSK-03 | Autonomous AI release / unauthorized assignment | Critical | `GovernedPipeline.submit_mutation()` raises `AutonomousReleaseBlocked` for any non-human actor. `AUTHORIZED_GOVERNORS` set is static and hardcoded. | TEST-07, TEST-08 | VERIFIED |
| RSK-04 | Nondeterministic JSON serialization causing hash drift | High | `canonical_json()` enforces `sort_keys=True`, compact separators, NFC Unicode normalization. Bitwise identical across runs. | TEST-12 | VERIFIED |
| RSK-05 | Schema drift on runtime payload insertion | Medium | `FrozenRegistry` blocks runtime schema mutation. Pydantic validates every payload before DB write. `IntegrityValidator` re-validates on scan. | TEST-11 | VERIFIED |
| RSK-06 | Orphan events / detached hash chain | High | `parent_event_hash` verified against previous `event_hash` before every insert. `IntegrityValidator` detects `ORPHAN_EVENT` and `HASH_MISMATCH`. | TEST-03, boot scan | VERIFIED |
| RSK-07 | Clock drift causing replay ordering issues | Medium | State reconstruction uses `sequence` (monotonic integer PK) as sole ordering key. Timestamps are metadata only. | TEST-12, replay suite | VERIFIED |
| RSK-08 | Snapshot divergence after restore | High | `BackupManager.create_snapshot()` stores `state_hash` (canonical replay hash) and `file_hash` (SHA-256 of SQLite file). Both verified on restore. | TEST-04 | VERIFIED |
| RSK-09 | GPT bridge gaining mutation authority | Critical | `GPTBridge` has no `append_event()` call path. `prepare_import_envelope()` returns `AWAITING_HUMAN_APPROVAL` — no DB write. | TEST-06 | VERIFIED |
| RSK-10 | Concurrent write race conditions | High | `SingleWriterQueue` per DB path serializes all writes under `threading.Lock`. Deterministic commit ordering guaranteed. | TEST-10 | VERIFIED |
| RSK-11 | Boot with corrupted journal | Critical | `CanonicalDB.__init__` calls `scan_and_verify()` — raises `STARTUP_SAFETY_GATE_BLOCKED` on any integrity failure. Application cannot start in corrupt state. | TEST-03, boot proof | VERIFIED |
| RSK-12 | Replay reconstruction producing divergent state | High | `reconstruct_db_from_jsonl()` runs `IntegrityValidator.run_full_scan()` on reconstructed DB — removes file and raises on failure. | TEST-05 | VERIFIED |
| RSK-13 | Hidden authority accumulation by Parikshak | Critical | `AUTHORIZED_GOVERNORS` is a static frozenset. No runtime modification path. `ConstitutionalValidator` enforces role permissions explicitly. | TEST-07, TEST-08 | VERIFIED |
| RSK-14 | Adapter direct DB mutation | High | All adapters under `/integrations/` are read-only consumers of the event journal. No `CanonicalDB.append_event()` calls in adapter code. | TEST-09 | VERIFIED |
| RSK-15 | Atomic write failure leaving corrupt JSONL | Medium | `atomic_append()` uses temp-file + `fsync` + `os.replace()`. Orphaned `.tmp` files detected and removed by `recover_interrupted_write()`. | Atomic persistence suite | VERIFIED |

---

## Risk Summary

- Critical risks: 5 — all VERIFIED mitigated
- High risks: 7 — all VERIFIED mitigated
- Medium risks: 3 — all VERIFIED mitigated
- **Total open risks: 0**
