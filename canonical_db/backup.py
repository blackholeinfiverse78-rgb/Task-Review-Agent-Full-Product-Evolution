import os
import shutil
import json
import hashlib
import uuid
from datetime import datetime
from typing import Dict, Any, List

class BackupManager:
    def __init__(self, db_path: str, backup_dir: str = "storage/backups"):
        self.db_path = db_path
        self.backup_dir = backup_dir
        os.makedirs(self.backup_dir, exist_ok=True)

    def create_snapshot(self, last_seq: int, head_hash: str) -> str:
        """Creates a snapshot copy of the SQLite database and records a JSON manifest."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        snapshot_db_name = f"snapshot_seq_{last_seq}_{timestamp}.sqlite"
        snapshot_db_path = os.path.join(self.backup_dir, snapshot_db_name)
        
        # 1. Copy SQLite database file
        shutil.copy2(self.db_path, snapshot_db_path)

        # 2. Calculate file hash
        file_hash = self._calculate_file_hash(snapshot_db_path)

        # Reconstruct state at last_seq to calculate state_hash
        from canonical_db.db import CanonicalDB
        from canonical_db.contracts import canonical_json
        db = CanonicalDB(self.db_path)
        try:
            state = db.reconstruct_state(up_to_seq=last_seq)
        finally:
            db.close()
        state_str = canonical_json(state)
        state_hash = hashlib.sha256(state_str.encode('utf-8')).hexdigest()

        # 3. Create manifest
        manifest = {
            "replay_checkpoint_id": f"chk-{uuid.uuid4().hex[:12]}",
            "snapshot_db": snapshot_db_name,
            "last_seq": last_seq,
            "head_hash": head_hash,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "file_hash": file_hash,
            "state_hash": state_hash
        }
        
        manifest_path = os.path.join(self.backup_dir, f"snapshot_seq_{last_seq}_{timestamp}.json")
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=4)

        return manifest_path

    def verify_and_restore(self, manifest_path: str) -> bool:
        """Verifies snapshot signature/hash and restores the DB file to the main path."""
        if not os.path.exists(manifest_path):
            raise FileNotFoundError(f"Manifest not found: {manifest_path}")

        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        snapshot_db_name = manifest["snapshot_db"]
        snapshot_db_path = os.path.join(self.backup_dir, snapshot_db_name)

        if not os.path.exists(snapshot_db_path):
            raise FileNotFoundError(f"Snapshot database file not found: {snapshot_db_path}")

        # 1. Verify file hash signature
        computed_hash = self._calculate_file_hash(snapshot_db_path)
        if computed_hash != manifest["file_hash"]:
            raise ValueError(
                f"BACKUP_SIGNATURE_MISMATCH: Snapshot file {snapshot_db_name} integrity check failed. "
                f"Manifest expects {manifest['file_hash']}, got {computed_hash}"
            )

        # 2. Safely copy to destination
        # Backup active database in case of sudden failure during restore
        temp_backup = self.db_path + ".restore_tmp"
        if os.path.exists(self.db_path):
            shutil.copy2(self.db_path, temp_backup)

        try:
            shutil.copy2(snapshot_db_path, self.db_path)
            if os.path.exists(temp_backup):
                os.remove(temp_backup)
            return True
        except Exception as e:
            # Revert
            if os.path.exists(temp_backup):
                shutil.move(temp_backup, self.db_path)
            raise e

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
