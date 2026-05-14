"""
Atomic Persistence Layer — Parikshak v3.0.0
Atomic writes, checksum validation, file locking, replay checkpointing.
Fails loudly on corruption. Never silently continues.
"""
import json
import os
import hashlib
import tempfile
import time
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

logger = logging.getLogger("atomic_persistence")

AUDIT_LOG_DIR      = "storage/audit_logs"
CHECKPOINT_DIR     = "storage/checkpoints"
BUCKET_LOG_DIR     = "storage/bucket_logs"

os.makedirs(AUDIT_LOG_DIR,  exist_ok=True)
os.makedirs(CHECKPOINT_DIR, exist_ok=True)
os.makedirs(BUCKET_LOG_DIR, exist_ok=True)


def _checksum(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()[:16]


def _acquire_lock(lock_path: str, timeout: float = 5.0) -> None:
    """Cross-platform file lock via lock file with timeout."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.close(fd)
            return
        except FileExistsError:
            time.sleep(0.05)
    raise RuntimeError(f"LOCK_TIMEOUT: Could not acquire lock {lock_path} within {timeout}s")


def _release_lock(lock_path: str) -> None:
    try:
        os.unlink(lock_path)
    except Exception:
        pass


def atomic_append(filepath: str, entry: Dict[str, Any]) -> None:
    """
    Atomically append a JSON entry to a JSONL file.
    Uses temp-file write + checksum + fsync + atomic rename for durability.
    File-locked to prevent concurrent corruption.
    """
    line = json.dumps(entry, ensure_ascii=False, default=str)
    checksum = _checksum(line)
    entry_with_checksum = json.dumps(
        {**entry, "_checksum": checksum},
        ensure_ascii=False, default=str
    )

    lock_path = filepath + ".lock"
    _acquire_lock(lock_path)
    try:

        # Read existing content
        existing = ""
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                existing = f.read()

        new_content = existing
        if new_content and not new_content.endswith("\n"):
            new_content += "\n"
        new_content += entry_with_checksum + "\n"

        # Write to temp file
        dir_name = os.path.dirname(filepath) or "."
        tmp_fd, tmp_path = tempfile.mkstemp(dir=dir_name, suffix=".tmp")
        try:
            with os.fdopen(tmp_fd, "w", encoding="utf-8") as tmp_f:
                tmp_f.write(new_content)
                tmp_f.flush()
                os.fsync(tmp_f.fileno())
            # Atomic rename
            os.replace(tmp_path, filepath)
        except Exception as e:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise RuntimeError(f"ATOMIC_WRITE_FAILURE: {filepath} — {e}")

    finally:
        _release_lock(lock_path)


def validate_log_segment(filepath: str) -> Dict[str, Any]:
    """
    Validate a JSONL log file for:
    - parse integrity
    - checksum validation
    - ordering (monotonic timestamps if present)
    Returns { valid, entry_count, corrupt_lines, warnings }
    """
    if not os.path.exists(filepath):
        return {"valid": True, "entry_count": 0, "corrupt_lines": [], "warnings": ["file not found"]}

    corrupt_lines = []
    warnings = []
    entry_count = 0
    last_ts = None

    with open(filepath, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                entry_count += 1

                # Checksum validation
                stored_checksum = entry.pop("_checksum", None)
                if stored_checksum:
                    recomputed = _checksum(
                        json.dumps(entry, ensure_ascii=False, default=str)
                    )
                    if recomputed != stored_checksum:
                        corrupt_lines.append(i)
                        warnings.append(f"Line {i}: checksum mismatch")

                # Ordering validation
                ts = entry.get("timestamp")
                if ts and last_ts and ts < last_ts:
                    warnings.append(f"Line {i}: ordering violation (ts={ts} < prev={last_ts})")
                if ts:
                    last_ts = ts

            except json.JSONDecodeError:
                corrupt_lines.append(i)
                warnings.append(f"Line {i}: JSON parse error")

    valid = len(corrupt_lines) == 0
    return {
        "valid": valid,
        "entry_count": entry_count,
        "corrupt_lines": corrupt_lines,
        "warnings": warnings
    }


def write_replay_checkpoint(trace_id: str, state: Dict[str, Any]) -> str:
    """
    Write a deterministic replay checkpoint.
    Returns checkpoint_id.
    """
    checkpoint_id = f"ckpt-{datetime.now().strftime('%Y%m%d%H%M%S')}-{trace_id[:8]}"
    payload = {
        "checkpoint_id":  checkpoint_id,
        "trace_id":       trace_id,
        "timestamp":      datetime.now().isoformat(),
        "state_hash":     _checksum(json.dumps(state, sort_keys=True, default=str)),
        "state":          state,
        "lineage_marker": True
    }
    filepath = os.path.join(CHECKPOINT_DIR, f"{checkpoint_id}.json")

    tmp_fd, tmp_path = tempfile.mkstemp(dir=CHECKPOINT_DIR, suffix=".tmp")
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, default=str, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, filepath)
    except Exception as e:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise RuntimeError(f"CHECKPOINT_WRITE_FAILURE: {e}")

    logger.info(f"[PERSISTENCE] Checkpoint written: {checkpoint_id}")
    return checkpoint_id


def load_checkpoint(checkpoint_id: str) -> Dict[str, Any]:
    """Load and validate a replay checkpoint."""
    filepath = os.path.join(CHECKPOINT_DIR, f"{checkpoint_id}.json")
    if not os.path.exists(filepath):
        raise ValueError(f"REPLAY_HARD_REJECT: Checkpoint '{checkpoint_id}' not found.")

    with open(filepath, "r", encoding="utf-8") as f:
        payload = json.load(f)

    # Validate hash
    stored_hash = payload.get("state_hash")
    recomputed  = _checksum(json.dumps(payload["state"], sort_keys=True, default=str))
    if stored_hash != recomputed:
        raise ValueError(
            f"REPLAY_HARD_REJECT: Checkpoint '{checkpoint_id}' hash mismatch. "
            f"Stored={stored_hash} Computed={recomputed}. Corruption detected."
        )

    return payload


def recover_interrupted_write(filepath: str) -> bool:
    """
    Detect and recover from interrupted writes.
    Removes orphaned .tmp files. Returns True if recovery performed.
    """
    dir_name = os.path.dirname(filepath) or "."
    recovered = False
    for fname in os.listdir(dir_name):
        if fname.endswith(".tmp"):
            tmp_path = os.path.join(dir_name, fname)
            logger.warning(f"[PERSISTENCE] Removing orphaned tmp file: {tmp_path}")
            os.unlink(tmp_path)
            recovered = True
    return recovered
