import os
import shutil
import json
import hashlib
import uuid
import sqlite3
from datetime import datetime, timezone
from typing import Dict, Any, List

def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

def _checkpoint_wal(db_path: str) -> None:
    """Force WAL checkpoint so snapshot captures a clean, self-contained SQLite file."""
    if not os.path.exists(db_path):
        return
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
        conn.commit()
    finally:
        conn.close()

class BackupManager:
    def __init__(self, db_path: str, backup_dir: str = None):
        self.db_path = db_path
        if backup_dir is None:
            db_name = os.path.splitext(os.path.basename(db_path))[0]
            backup_dir = os.path.join("storage", "backups", db_name)
        self.backup_dir = backup_dir
        os.makedirs(self.backup_dir, exist_ok=True)

    def create_snapshot(self, last_seq: int, head_hash: str) -> str:
        """Creates a WAL-checkpointed snapshot and manifest with state_hash + file_hash."""
        # Checkpoint WAL before copy so snapshot is self-contained
        _checkpoint_wal(self.db_path)

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        snapshot_db_name = f"snapshot_seq_{last_seq}_{timestamp}.sqlite"
        snapshot_db_path = os.path.join(self.backup_dir, snapshot_db_name)

        shutil.copy2(self.db_path, snapshot_db_path)
        file_hash = self._calculate_file_hash(snapshot_db_path)

        from canonical_db.db import CanonicalDB
        from canonical_db.contracts import canonical_json
        db = CanonicalDB(self.db_path)
        try:
            state = db.reconstruct_state(up_to_seq=last_seq)
        finally:
            db.close()
        state_str = canonical_json(state)
        state_hash = hashlib.sha256(state_str.encode('utf-8')).hexdigest()

        manifest = {
            "replay_checkpoint_id": f"chk-{uuid.uuid4().hex[:12]}",
            "snapshot_db": snapshot_db_name,
            "last_seq": last_seq,
            "head_hash": head_hash,
            "timestamp": _utcnow(),
            "file_hash": file_hash,
            "state_hash": state_hash
        }

        manifest_path = os.path.join(self.backup_dir, f"snapshot_seq_{last_seq}_{timestamp}.json")
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=4)

        return manifest_path

    def verify_and_restore(self, manifest_path: str) -> bool:
        """Verifies snapshot file_hash, restores DB, checkpoints WAL, verifies state_hash parity."""
        if not os.path.exists(manifest_path):
            raise FileNotFoundError(f"Manifest not found: {manifest_path}")

        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        snapshot_db_name = manifest["snapshot_db"]
        snapshot_db_path = os.path.join(self.backup_dir, snapshot_db_name)

        if not os.path.exists(snapshot_db_path):
            raise FileNotFoundError(f"Snapshot database file not found: {snapshot_db_path}")

        # 1. Verify snapshot file integrity
        computed_hash = self._calculate_file_hash(snapshot_db_path)
        if computed_hash != manifest["file_hash"]:
            raise ValueError(
                f"BACKUP_SIGNATURE_MISMATCH: {snapshot_db_name} "
                f"expected={manifest['file_hash']} got={computed_hash}"
            )

        # 2. Atomic restore with rollback on failure
        temp_backup = self.db_path + ".restore_tmp"
        if os.path.exists(self.db_path):
            shutil.copy2(self.db_path, temp_backup)

        try:
            shutil.copy2(snapshot_db_path, self.db_path)
            # Remove any stale WAL/SHM from the pre-restore DB so restored DB is clean
            for ext in ("-wal", "-shm"):
                stale = self.db_path + ext
                if os.path.exists(stale):
                    os.remove(stale)
            # Checkpoint the restored DB to ensure it is self-contained
            _checkpoint_wal(self.db_path)
            if os.path.exists(temp_backup):
                os.remove(temp_backup)
        except Exception as e:
            if os.path.exists(temp_backup):
                shutil.move(temp_backup, self.db_path)
            raise e

        # 3. Replay parity verification — reconstruct state and compare state_hash
        from canonical_db.db import CanonicalDB
        from canonical_db.contracts import canonical_json
        db = CanonicalDB(self.db_path)
        try:
            restored_state = db.reconstruct_state(up_to_seq=manifest["last_seq"])
        finally:
            db.close()

        restored_str = canonical_json(restored_state)
        restored_hash = hashlib.sha256(restored_str.encode('utf-8')).hexdigest()

        if restored_hash != manifest["state_hash"]:
            raise ValueError(
                f"RESTORE_PARITY_MISMATCH: Replayed state hash {restored_hash} "
                f"does not match manifest state_hash {manifest['state_hash']}. "
                "Restore aborted — data integrity cannot be guaranteed."
            )

        return True

    def _calculate_file_hash(self, file_path: str) -> str:
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def list_snapshots(self) -> List[Dict[str, Any]]:
        snapshots = []
        for file in os.listdir(self.backup_dir):
            if file.endswith(".json"):
                try:
                    with open(os.path.join(self.backup_dir, file), "r") as f:
                        snapshots.append(json.load(f))
                except Exception:
                    pass
        return sorted(snapshots, key=lambda x: x["last_seq"])
