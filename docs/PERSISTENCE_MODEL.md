# PERSISTENCE DURABILITY MODEL

## 1. ATOMIC WRITE FLOW
All file-based persistence operations (`atomic_append`, `write_replay_checkpoint`) follow an unbreakable durability flow:
1. `tempfile.mkstemp`: Data is written to a unique staging file.
2. `os.fsync`: The OS buffer is forcibly flushed to physical disk hardware.
3. `os.replace`: An atomic rename shifts the temporary file over the target file, ensuring zero chance of torn writes.

## 2. DURABILITY GUARANTEES
- **No In-Place Modification**: Logs use strict append-only persistence.
- **Concurrent Protection**: Uses cross-platform lock files (`.lock`) with timeout checks to serialize appends and avoid race conditions.
- **OCC Governance Locking**: Optimistic Concurrency Control explicitly rejects concurrent or stale state modifications (`expected_version`).
- **Checksum Continuity**: Each payload incorporates a SHA-256 checksum to provide strict continuity checks.

## 3. RECOVERY MODEL
- Any failure mid-write leaves a `.tmp` file but does not corrupt the target file.
- The system automatically triggers orphaned `.tmp` cleanup, discarding incomplete writes gracefully and returning to an operational state.
