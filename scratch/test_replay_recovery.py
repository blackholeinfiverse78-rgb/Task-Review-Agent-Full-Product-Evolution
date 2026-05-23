import sys
import os
import json
import uuid
from datetime import datetime

# Add workspace root to system path
sys.path.append(os.getcwd())

from replay_audit.atomic_persistence import (
    recover_interrupted_write, write_replay_checkpoint, load_checkpoint,
    atomic_append, AUDIT_LOG_DIR, CHECKPOINT_DIR
)
from replay_audit.replay_engine import replay_engine

def test_restart_recovery():
    print("\n--- Testing Restart Recovery ---")
    
    # Ensure checkpoint directory exists
    os.makedirs(CHECKPOINT_DIR, exist_ok=True)
    
    # Create an orphaned .tmp file in the checkpoint directory
    tmp_filename = os.path.join(CHECKPOINT_DIR, f"orphaned_test_{uuid.uuid4().hex[:6]}.tmp")
    with open(tmp_filename, "w") as f:
        f.write("temporary data from interrupted write")
        
    assert os.path.exists(tmp_filename), "Temp file should exist"
    
    # Call recovery
    recovered = recover_interrupted_write(os.path.join(CHECKPOINT_DIR, "dummy.json"))
    
    print(f"Recovery function returned: {recovered}")
    assert recovered is True, "Expected recover_interrupted_write to return True when temp files exist"
    assert not os.path.exists(tmp_filename), "Expected temp file to be deleted"
    
    # Calling it again should return False
    recovered_again = recover_interrupted_write(os.path.join(CHECKPOINT_DIR, "dummy.json"))
    assert recovered_again is False, "Expected no recovery when no temp files exist"
    
    print("✅ Restart recovery test passed.")


def test_replay_reconstruction():
    print("\n--- Testing Replay Reconstruction & Forensic Reporting ---")
    
    trace_id = f"trace-recon-{uuid.uuid4().hex[:8]}"
    state = {
        "event_id": f"evt-{uuid.uuid4().hex[:8]}",
        "action": "modify",
        "submission_id": "sub-recon-001",
        "original_task": "T-GOV-001",
        "override_task": "T-GOV-002",
        "operator_id": "senior-op-recon"
    }
    
    # Write checkpoint
    ckpt_id = write_replay_checkpoint(trace_id, state)
    print(f"Written checkpoint: {ckpt_id}")
    
    # Load and verify reconstruction
    loaded = load_checkpoint(ckpt_id)
    assert loaded["trace_id"] == trace_id
    assert loaded["state"]["action"] == "modify"
    assert loaded["state"]["operator_id"] == "senior-op-recon"
    
    # Append to daily audit log
    date_str = datetime.now().strftime("%Y-%m-%d")
    audit_entry = {
        "event_type": "governance_action",
        "trace_id": trace_id,
        "submission_id": "sub-recon-001",
        "action": "modify",
        "timestamp": datetime.now().isoformat(),
        "operator_id": "senior-op-recon"
    }
    atomic_append(os.path.join(AUDIT_LOG_DIR, f"audit_{date_str}.jsonl"), audit_entry)
    
    # Generate forensic report
    report = replay_engine.generate_forensic_report(trace_id, date_str)
    print(f"Forensic report event count: {report['events_found']}")
    assert report["events_found"] == 1
    assert report["events"][0]["action"] == "modify"
    assert report["integrity"] == "verified"
    
    # Check chain validation
    chain_summary = replay_engine.verify_checkpoint_chain(trace_id)
    assert chain_summary["chain_valid"] is True
    assert chain_summary["checkpoints"] == 1
    
    print("✅ Replay reconstruction & forensic reporting test passed.")


def test_corruption_handling():
    print("\n--- Testing Corruption Handling ---")
    
    # Scenario A: Checkpoint with invalid state hash signature
    trace_id = f"trace-corrupt-{uuid.uuid4().hex[:8]}"
    ckpt_id = f"ckpt-corrupt-{uuid.uuid4().hex[:8]}"
    ckpt_path = os.path.join(CHECKPOINT_DIR, f"{ckpt_id}.json")
    
    payload = {
        "checkpoint_id": ckpt_id,
        "trace_id": trace_id,
        "timestamp": datetime.now().isoformat(),
        "state_hash": "incorrect_hash_signature",
        "state": {"action": "approve", "operator_id": "some-op"},
        "lineage_marker": True
    }
    
    with open(ckpt_path, "w", encoding="utf-8") as f:
        json.dump(payload, f)
        
    try:
        load_checkpoint(ckpt_id)
        assert False, "Expected load_checkpoint to raise ValueError for mismatched hash signature"
    except ValueError as e:
        print(f"Caught expected checkpoint mismatch exception: {e}")
        assert "REPLAY_HARD_REJECT" in str(e)
    finally:
        if os.path.exists(ckpt_path):
            os.remove(ckpt_path)
            
    # Scenario B: Audit log with corrupted JSON syntax
    date_str = "corrupt-date-test"
    audit_path = os.path.join(AUDIT_LOG_DIR, f"audit_{date_str}.jsonl")
    
    with open(audit_path, "w", encoding="utf-8") as f:
        f.write('{"trace_id": "t-1", "action": "approve"}\n')
        f.write('{this is invalid json}\n')
        
    try:
        replay_engine.verify_audit_log(date_str)
        assert False, "Expected verify_audit_log to raise ValueError for malformed JSON line"
    except ValueError as e:
        print(f"Caught expected audit log JSON corruption exception: {e}")
        assert "REPLAY_HARD_REJECT" in str(e)
        
    # Scenario C: Audit log with invalid checksum
    with open(audit_path, "w", encoding="utf-8") as f:
        entry = {
            "trace_id": "t-1",
            "action": "approve",
            "_checksum": "incorrect_checksum"
        }
        f.write(json.dumps(entry) + "\n")
        
    try:
        replay_engine.verify_audit_log(date_str)
        assert False, "Expected verify_audit_log to raise ValueError for checksum mismatch"
    except ValueError as e:
        print(f"Caught expected audit log checksum exception: {e}")
        assert "REPLAY_HARD_REJECT" in str(e)
    finally:
        if os.path.exists(audit_path):
            os.remove(audit_path)
            
    print("✅ Corruption handling test passed (failed loudly as expected).")


def test_divergence_rejection():
    print("\n--- Testing Divergence Rejection ---")
    
    original = {
        "evaluation_result": "PASS",
        "failure_type": None,
        "selected_task_id": "T-GOV-002",
        "source": "assignment_engine"
    }
    
    replayed_matching = {
        "evaluation_result": "PASS",
        "failure_type": None,
        "selected_task_id": "T-GOV-002",
        "source": "assignment_engine"
    }
    
    replayed_divergent = {
        "evaluation_result": "FAIL",
        "failure_type": "incomplete",
        "selected_task_id": "T-GOV-F01",
        "source": "assignment_engine"
    }
    
    # 1. Matching should pass
    report = replay_engine.detect_divergence(original, replayed_matching)
    assert report["divergence"] is False
    
    # 2. Divergent should raise REPLAY_DIVERGENCE
    try:
        replay_engine.detect_divergence(original, replayed_divergent)
        assert False, "Expected detect_divergence to raise ValueError for output divergence"
    except ValueError as e:
        print(f"Caught expected divergence exception: {e}")
        assert "REPLAY_DIVERGENCE" in str(e)
        
    print("✅ Divergence rejection test passed.")


def run_all_replay_tests():
    print("==================================================")
    print("🏁 RUNNING REPLAY & RECOVERY TEST SUITE")
    print("==================================================")
    # Clear checkpoints directory first
    if os.path.exists(CHECKPOINT_DIR):
        import shutil
        for fname in os.listdir(CHECKPOINT_DIR):
            fpath = os.path.join(CHECKPOINT_DIR, fname)
            try:
                if os.path.isfile(fpath):
                    os.unlink(fpath)
            except Exception:
                pass

    try:
        test_restart_recovery()
        test_replay_reconstruction()
        test_corruption_handling()
        test_divergence_rejection()
        print("\n==================================================")
        print("🎉 ALL REPLAY & RECOVERY TESTS PASSED!")
        print("==================================================")
        return True
    except Exception as e:
        import traceback
        print("\n❌ REPLAY & RECOVERY TEST FAILURE:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_all_replay_tests()
    sys.exit(0 if success else 1)
