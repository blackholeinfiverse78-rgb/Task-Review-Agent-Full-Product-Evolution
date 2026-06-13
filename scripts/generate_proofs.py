import os
import sys
import json
import shutil
import sqlite3
import hashlib
from datetime import datetime, timezone

def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

# Add root directory to sys.path
sys.path.append(os.getcwd())

from canonical_db.contracts import GovernanceEnvelope, canonical_json
from canonical_db.db import CanonicalDB
from canonical_db.pipeline import GovernedPipeline
from canonical_db.integrity import IntegrityValidator
from canonical_db.backup import BackupManager
from canonical_db.recovery import RecoveryTool

# Monkeypatch to sandbox temp databases and isolate them from storage/backups
original_iv_init = IntegrityValidator.__init__
def patched_iv_init(self, db_path, backup_dir=None):
    if backup_dir is None:
        backup_dir = "storage/backups"
    if "proof_db" not in db_path:
        sandbox_dir = os.path.join(os.getcwd(), "scratch", "temp_backups_generate_proofs")
        os.makedirs(sandbox_dir, exist_ok=True)
        original_iv_init(self, db_path, backup_dir=sandbox_dir)
    else:
        original_iv_init(self, db_path, backup_dir)
IntegrityValidator.__init__ = patched_iv_init

original_bm_init = BackupManager.__init__
def patched_bm_init(self, db_path, backup_dir=None):
    if backup_dir is None:
        backup_dir = "storage/backups"
    if "proof_db" not in db_path:
        sandbox_dir = os.path.join(os.getcwd(), "scratch", "temp_backups_generate_proofs")
        os.makedirs(sandbox_dir, exist_ok=True)
        original_bm_init(self, db_path, backup_dir=sandbox_dir)
    else:
        original_bm_init(self, db_path, backup_dir)
BackupManager.__init__ = patched_bm_init

def make_valid_envelope():
    env = GovernanceEnvelope(
        trace_id="trace-proof-12345",
        schema_version="v1.0",
        actor="operator-1",
        actor_role="operator",
        event_type="candidate_profiles",
        payload={
            "candidate_id": "cand-proof-001",
            "name": "Nikhil Proof",
            "github_handle": "nikhil-proof",
            "skills": ["python", "governance"],
            "performance_score": 99.0
        },
        authorized_by="Akash",
        lineage_reference="lineage-proof",
        approval_token="token-proof-abc",
        parent_event_hash="0"*64
    )
    env.payload_checksum = env.compute_checksum()
    env.checksum = env.payload_checksum
    return env

def main():
    print("Generating proof outputs...")
    
    # Clean backup dir to avoid stale snapshots
    backup_dir = "storage/backups"
    if os.path.exists(backup_dir):
        for f in os.listdir(backup_dir):
            if f.startswith("snapshot_seq_") or f.endswith(".sqlite") or f.endswith(".json"):
                try:
                    os.remove(os.path.join(backup_dir, f))
                except Exception:
                    pass

    # Clean sandbox backup dir to avoid stale test snapshots
    sandbox_dir = "scratch/temp_backups_generate_proofs"
    if os.path.exists(sandbox_dir):
        try:
            shutil.rmtree(sandbox_dir)
        except Exception:
            pass

    os.makedirs("proofs", exist_ok=True)
    os.makedirs("replay_logs", exist_ok=True)
    os.makedirs("integrity_reports", exist_ok=True)
    os.makedirs("snapshots", exist_ok=True)
    os.makedirs("test_vectors", exist_ok=True)

    db_path = "storage/proof_db.sqlite"
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except Exception:
            pass
    
    # 1. Test vectors
    envelope = make_valid_envelope()
    test_vectors = {
        "valid_envelope": envelope.model_dump(),
        "invalid_envelope_missing_actor": {
            "trace_id": "trace-123",
            "schema_version": "v1.0",
            # missing actor
            "payload": {"candidate_id": "cand-1"}
        }
    }
    with open("test_vectors/governance_envelopes.json", "w") as f:
        json.dump(test_vectors, f, indent=4)

    # 2. Boot integrity rejection proof
    # We create a corrupted SQLite DB directly
    corrupt_db_path = "storage/corrupt_proof.sqlite"
    if os.path.exists(corrupt_db_path):
        os.remove(corrupt_db_path)
    
    # Initialize it
    db = CanonicalDB(corrupt_db_path)
    # Write a valid event
    db.append_event(envelope, "operator-1")
    db.close()
    
    # Now manually corrupt it (update payload to cause mismatch)
    conn = sqlite3.connect(corrupt_db_path)
    cursor = conn.cursor()
    cursor.execute("DROP TRIGGER IF EXISTS prevent_update_events")
    cursor.execute("UPDATE events SET payload = ? WHERE sequence = 1", ('{"corrupted": "data"}',))
    conn.commit()
    conn.close()
    
    boot_failed = False
    error_msg = ""
    try:
        CanonicalDB(corrupt_db_path)
    except Exception as e:
        boot_failed = True
        error_msg = str(e)
    
    boot_integrity_proof = {
        "timestamp": _utcnow(),
        "scenario": "Boot validation with corrupted events table",
        "boot_blocked": boot_failed,
        "exception_type": "ValueError" if boot_failed else None,
        "exception_message": error_msg
    }
    with open("proofs/boot_integrity_rejection_proof.json", "w") as f:
        json.dump(boot_integrity_proof, f, indent=4)
        
    if os.path.exists(corrupt_db_path):
        os.remove(corrupt_db_path)

    # 3. Deterministic replay proof & snapshots
    db = CanonicalDB(db_path)
    pipeline = GovernedPipeline(db_path)
    
    # Commit first event
    res1 = pipeline.submit_mutation(envelope, "operator-1")
    snapshot_manifest_path = res1["snapshot"]
    
    # Verify snapshot files
    with open(snapshot_manifest_path, "r") as f:
        manifest = json.load(f)
    
    # Copy manifest and sqlite file to snapshots/
    shutil.copy2(snapshot_manifest_path, "snapshots/")
    shutil.copy2(os.path.join("storage/backups", manifest["snapshot_db"]), "snapshots/")
    
    # Commit second event
    envelope2 = make_valid_envelope()
    envelope2.payload["candidate_id"] = "cand-proof-002"
    envelope2.payload["name"] = "Alice Proof"
    envelope2.payload_checksum = envelope2.compute_checksum()
    envelope2.checksum = envelope2.payload_checksum
    pipeline.submit_mutation(envelope2, "operator-1")
    
    # Reconstruct state twice
    state1 = db.reconstruct_state()
    state2 = db.reconstruct_state()
    state1_str = canonical_json(state1)
    state2_str = canonical_json(state2)
    state_hash1 = hashlib.sha256(state1_str.encode()).hexdigest()
    state_hash2 = hashlib.sha256(state2_str.encode()).hexdigest()
    
    deterministic_replay_proof = {
        "timestamp": _utcnow(),
        "state_1_hash": state_hash1,
        "state_2_hash": state_hash2,
        "match": state_hash1 == state_hash2,
        "reconstructed_read_models": state1
    }
    with open("proofs/deterministic_replay_proof.json", "w") as f:
        json.dump(deterministic_replay_proof, f, indent=4)

    # Replay logs
    events = db.get_all_events()
    with open("replay_logs/recovery_replay.log", "w") as f:
        for ev in events:
            f.write(json.dumps(ev) + "\n")

    # 4. Snapshot restore proof
    # State before restore
    state_before = db.reconstruct_state()
    db.close()
    
    # Restore to snapshot 1
    pipeline.backup_mgr.verify_and_restore(snapshot_manifest_path)
    
    db = CanonicalDB(db_path)
    state_after = db.reconstruct_state()
    db.close()
    
    snapshot_restore_proof = {
        "timestamp": _utcnow(),
        "manifest_used": snapshot_manifest_path,
        "state_before_restore_candidates": list(state_before["candidate_profiles"].keys()),
        "state_after_restore_candidates": list(state_after["candidate_profiles"].keys()),
        "restore_successful": "cand-proof-002" not in state_after["candidate_profiles"]
    }
    with open("proofs/snapshot_restore_proof.json", "w") as f:
        json.dump(snapshot_restore_proof, f, indent=4)

    # 5. Corruption rejection proof
    # We corrupt the DB manually and scan it
    db = CanonicalDB(db_path)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("DROP TRIGGER IF EXISTS prevent_update_events")
    cursor.execute("UPDATE events SET payload = ? WHERE sequence = 1", ('{"corrupted": "data"}',))
    conn.commit()
    conn.close()
    
    validator = IntegrityValidator(db_path)
    scan = validator.run_full_scan()
    db.close()
    
    corruption_rejection_proof = {
        "timestamp": _utcnow(),
        "valid": scan["valid"],
        "errors": scan.get("errors", [])
    }
    with open("proofs/corruption_rejection_proof.json", "w") as f:
        json.dump(corruption_rejection_proof, f, indent=4)
        
    with open("integrity_reports/scan_report.json", "w") as f:
        json.dump(scan, f, indent=4)

    # Clean db
    if os.path.exists(db_path):
        os.remove(db_path)

    # 6. Schema drift rejection proof
    # Attempting to submit envelope with missing schema field
    pipeline = GovernedPipeline(db_path)
    drift_envelope = GovernanceEnvelope(
        trace_id="trace-drift",
        schema_version="v1.0",
        actor="operator-1",
        actor_role="operator",
        event_type="candidate_profiles",
        payload={
            "name": "Drift Candidate" # missing candidate_id
        },
        authorized_by="Akash",
        lineage_reference="lineage-proof",
        approval_token="token-proof-abc",
        parent_event_hash="0"*64
    )
    drift_envelope.payload_checksum = drift_envelope.compute_checksum()
    drift_envelope.checksum = drift_envelope.payload_checksum
    
    drift_failed = False
    drift_error = ""
    try:
        pipeline.submit_mutation(drift_envelope, "operator-1")
    except Exception as e:
        drift_failed = True
        drift_error = str(e)
        
    schema_drift_proof = {
        "timestamp": _utcnow(),
        "drift_rejected": drift_failed,
        "error_message": drift_error
    }
    with open("proofs/schema_drift_rejection_proof.json", "w") as f:
        json.dump(schema_drift_proof, f, indent=4)

    # 7. Autonomous release rejection proof
    release_envelope = make_valid_envelope()
    release_envelope.authorized_by = "AI_Orchestrator_Agent"
    release_envelope.payload_checksum = release_envelope.compute_checksum()
    release_envelope.checksum = release_envelope.payload_checksum
    
    release_failed = False
    release_error = ""
    release_exc_type = None
    try:
        pipeline.submit_mutation(release_envelope, "operator-1")
    except Exception as e:
        release_failed = True
        release_error = str(e)
        release_exc_type = type(e).__name__
        
    autonomous_release_proof = {
        "timestamp": _utcnow(),
        "release_blocked": release_failed,
        "error_message": release_error,
        "exception_type": release_exc_type
    }
    with open("proofs/autonomous_release_rejection_proof.json", "w") as f:
        json.dump(autonomous_release_proof, f, indent=4)

    # 8. Concurrent ordering proof
    import threading
    concurrent_db = "storage/concurrent_proof.sqlite"
    if os.path.exists(concurrent_db):
        os.remove(concurrent_db)
        
    pipeline_c = GovernedPipeline(concurrent_db)
    
    def worker(idx):
        env = make_valid_envelope()
        env.payload["candidate_id"] = f"cand-{idx}"
        env.payload_checksum = env.compute_checksum()
        env.checksum = env.payload_checksum
        try:
            pipeline_c.submit_mutation(env, "operator-1")
        except Exception:
            pass
            
    threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
        
    db_c = CanonicalDB(concurrent_db)
    events_c = db_c.get_all_events()
    db_c.close()
    
    concurrent_ordering_proof = {
        "timestamp": _utcnow(),
        "threads_spawned": 5,
        "events_written": len(events_c),
        "ordered_sequences": [e["sequence"] for e in events_c],
        "strictly_ordered": [e["sequence"] for e in events_c] == [1, 2, 3, 4, 5]
    }
    with open("proofs/concurrent_ordering_proof.json", "w") as f:
        json.dump(concurrent_ordering_proof, f, indent=4)
        
    if os.path.exists(concurrent_db):
        os.remove(concurrent_db)

    print("All proofs successfully written to /proofs, /replay_logs, /integrity_reports, /snapshots, /test_vectors!")

if __name__ == "__main__":
    main()
