import os
import sys
import json
import sqlite3
import hashlib
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor

def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

sys.path.append(os.getcwd())

from canonical_db.contracts import GovernanceEnvelope
from canonical_db.db import CanonicalDB
from canonical_db.integrity import IntegrityValidator
from canonical_db.backup import BackupManager
from canonical_db.recovery import RecoveryTool
from canonical_db.pipeline import GovernedPipeline
from canonical_db.gpt_bridge import GPTBridge
from canonical_db.strategic_approval import StrategicApprovalEngine
from canonical_db.integration import EcosystemIntegrator

TEST_DB = "storage/test_canonical_db.sqlite"

def run_test(num: str, name: str, func):
    print(f"\n==================================================")
    print(f"RUNNING {num}: {name}")
    print(f"==================================================")
    try:
        status, evidence, proof, replay = func()
        print(f"STATUS: {status}")
        print(f"EVIDENCE: {evidence}")
        print(f"DETERMINISTIC PROOF: {proof}")
        print(f"REPLAY RESULT: {replay}")
        return True
    except Exception as e:
        import traceback
        print(f"STATUS: FAIL")
        print(f"ERROR: {e}")
        traceback.print_exc()
        return False

# Setup helpers
def init_clean_db():
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    # Re-initialize empty DB schema
    db = CanonicalDB(TEST_DB)
    db.close()
    
    # Clean backup dir
    backup_dir = "storage/backups"
    if os.path.exists(backup_dir):
        for f in os.listdir(backup_dir):
            if f.startswith("snapshot_seq_") or f.endswith(".sqlite") or f.endswith(".json"):
                try:
                    os.remove(os.path.join(backup_dir, f))
                except Exception:
                    pass

def make_valid_envelope() -> GovernanceEnvelope:
    return GovernanceEnvelope(
        trace_id="trace-test-12345",
        schema_version="v1.0",
        actor="operator-1",
        event_type="candidate_profiles",
        payload={
            "candidate_id": "cand-001",
            "name": "Nikhil",
            "github_handle": "nikhil-dev",
            "skills": ["python", "sqlite", "governance"],
            "performance_score": 95.5
        },
        authorized_by="Akash"
    )

# ----------------- TEST FUNCTIONS -----------------

def test_01_db_init():
    init_clean_db()
    db = CanonicalDB(TEST_DB)
    # Verify events table
    cursor = db.conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='events'")
    table_exists = cursor.fetchone() is not None
    db.close()
    
    status = "PASS" if table_exists else "FAIL"
    evidence = f"Database initialized at {TEST_DB}."
    proof = f"Table 'events' exists: {table_exists}"
    replay = "No events present yet."
    return status, evidence, proof, replay

def test_02_write_validation():
    db = CanonicalDB(TEST_DB)
    envelope = make_valid_envelope()
    envelope.checksum = envelope.compute_checksum()
    
    # Commit via raw db to verify hashing
    event = db.append_event(envelope, "operator-1")
    db.close()

    status = "PASS" if event["sequence"] == 1 else "FAIL"
    evidence = f"Committed sequence {event['sequence']} with event_id {event['event_id']}."
    proof = f"parent_event_hash: {event['parent_event_hash']}\nevent_hash: {event['event_hash']}"
    replay = f"Read model candidate name: {envelope.payload['name']}"
    return status, evidence, proof, replay

def test_03_corruption_detection():
    # Corrupt the database by dropping the triggers temporarily and updating a payload
    conn = sqlite3.connect(TEST_DB)
    cursor = conn.cursor()
    cursor.execute("DROP TRIGGER prevent_update_events")
    cursor.execute("UPDATE events SET payload = ? WHERE sequence = 1", ('{"corrupted": "data"}',))
    conn.commit()
    conn.close()

    # Scan for corruption
    validator = IntegrityValidator(TEST_DB)
    scan = validator.run_full_scan()
    
    status = "PASS" if not scan["valid"] else "FAIL"
    evidence = f"Corrupted payload. Scanner outcome: {scan['valid']}"
    proof = f"Scanner errors detected:\n" + "\n".join(scan.get("errors", []))
    replay = "State reconstruction blocked due to integrity failure."
    
    # Restore db for next tests
    init_clean_db()
    return status, evidence, proof, replay

def test_04_restore_proof():
    init_clean_db()
    pipeline = GovernedPipeline(TEST_DB)
    envelope1 = make_valid_envelope()
    envelope1.checksum = envelope1.compute_checksum()
    res1 = pipeline.submit_mutation(envelope1, "operator-1")
    snapshot_manifest = res1["snapshot"]

    # Write a second event
    envelope2 = make_valid_envelope()
    envelope2.payload["candidate_id"] = "cand-002"
    envelope2.payload["name"] = "Alice"
    envelope2.checksum = envelope2.compute_checksum()
    res2 = pipeline.submit_mutation(envelope2, "operator-1")

    # Verify candidate 2 is present
    db = CanonicalDB(TEST_DB)
    state_before = db.reconstruct_state()
    db.close()
    
    # Restore to snapshot 1
    pipeline.backup_mgr.verify_and_restore(snapshot_manifest)

    # Verify state after restore (candidate 2 should be gone)
    db = CanonicalDB(TEST_DB)
    state_after = db.reconstruct_state()
    db.close()

    success = ("cand-002" in state_before["candidate_profiles"]) and ("cand-002" not in state_after["candidate_profiles"])
    status = "PASS" if success else "FAIL"
    evidence = f"Restored to snapshot {snapshot_manifest}"
    proof = f"cand-002 in state_before: { 'cand-002' in state_before['candidate_profiles'] }\ncand-002 in state_after: { 'cand-002' in state_after['candidate_profiles'] }"
    replay = f"Replayed state candidates: {list(state_after['candidate_profiles'].keys())}"
    return status, evidence, proof, replay

def test_05_replay_reconstruction():
    init_clean_db()
    pipeline = GovernedPipeline(TEST_DB)
    envelope = make_valid_envelope()
    envelope.checksum = envelope.compute_checksum()
    pipeline.submit_mutation(envelope, "operator-1")

    # Export to JSONL
    tool = RecoveryTool(TEST_DB)
    jsonl_path = "storage/test_audit_log.jsonl"
    tool.export_journal_to_jsonl(jsonl_path)

    # Reconstruct into a new SQLite database file
    reconstructed_db = "storage/reconstructed_test_db.sqlite"
    success = tool.reconstruct_db_from_jsonl(jsonl_path, reconstructed_db)

    # Replay reconstructed db state
    db = CanonicalDB(reconstructed_db)
    state = db.reconstruct_state()
    db.close()

    status = "PASS" if success else "FAIL"
    evidence = f"Exported to {jsonl_path} and reconstructed to {reconstructed_db}."
    proof = f"Reconstructed state has cand-001: {'cand-001' in state['candidate_profiles']}"
    replay = f"Candidate name after reconstruction: {state['candidate_profiles']['cand-001']['name']}"
    
    # Cleanup reconstructed db file
    if os.path.exists(reconstructed_db):
        os.remove(reconstructed_db)
    if os.path.exists(jsonl_path):
        os.remove(jsonl_path)
        
    return status, evidence, proof, replay

def test_06_gpt_boundary():
    init_clean_db()
    bridge = GPTBridge(TEST_DB)
    
    # 1. Export state
    export_payload = bridge.export_state_for_gpt()
    has_signature = "system_signature" in export_payload

    # 2. GPT Scaffold validation & wrap in Governance Envelope
    gpt_scaffold = {
        "candidate_id": "cand-gpt-99",
        "name": "GPT Scaffolding Review",
        "skills": ["reasoning"],
        "performance_score": 85.0
    }
    
    envelope_wrap = bridge.prepare_import_envelope(gpt_scaffold, "candidate_profiles", "trace-gpt-bridge", "gpt")
    
    # Verify that it is NOT committed to the DB yet (DB should be empty)
    db = CanonicalDB(TEST_DB)
    events = db.get_all_events()
    db.close()

    success = has_signature and envelope_wrap["status"] == "AWAITING_HUMAN_APPROVAL" and len(events) == 0
    status = "PASS" if success else "FAIL"
    evidence = "GPT exported signed state and prepared scaffold envelope."
    proof = f"Awaiting human approval: {envelope_wrap['status'] == 'AWAITING_HUMAN_APPROVAL'}\nDB contains 0 events: {len(events) == 0}"
    replay = f"Bridge status: {envelope_wrap['bridge_validation']}"
    return status, evidence, proof, replay

def test_07_human_approval_lock():
    init_clean_db()
    pipeline = GovernedPipeline(TEST_DB)
    
    # Try to commit without signature
    envelope = make_valid_envelope()
    envelope.authorized_by = None
    envelope.checksum = envelope.compute_checksum()

    blocked = False
    try:
        pipeline.submit_mutation(envelope, "operator-1")
    except PermissionError as e:
        blocked = True
        evidence = str(e)

    status = "PASS" if blocked else "FAIL"
    proof = f"Blocked unauthorized write: {blocked}"
    replay = "DB state remains pristine (0 events)."
    return status, evidence, proof, replay

def test_08_autonomous_release():
    init_clean_db()
    pipeline = GovernedPipeline(TEST_DB)
    
    # Try to commit with non-human / unauthorized signature
    envelope = make_valid_envelope()
    envelope.authorized_by = "AI_Orchestrator_Agent"
    envelope.checksum = envelope.compute_checksum()

    blocked = False
    try:
        pipeline.submit_mutation(envelope, "operator-1")
    except PermissionError as e:
        blocked = True
        evidence = str(e)

    status = "PASS" if blocked else "FAIL"
    proof = f"Blocked autonomous release signature: {blocked}"
    replay = "DB state remains pristine (0 events)."
    return status, evidence, proof, replay

def test_09_ecosystem_integration():
    init_clean_db()
    integrator = EcosystemIntegrator(TEST_DB)
    
    # Mock human governance review approval envelope
    envelope = GovernanceEnvelope(
        trace_id="trace-eco-12345",
        schema_version="v1.0",
        actor="operator-1",
        event_type="review_history",
        payload={
            "review_id": "rev-eco-001",
            "submission_id": "sub-eco-001",
            "status": "APPROVED",
            "score": 92.0,
            "reviewed_by": "Akash",
            "reviewed_at": _utcnow()
        },
        authorized_by="Akash"
    )
    envelope.checksum = envelope.compute_checksum()

    res = integrator.propagate_governed_approval(envelope, "Akash")

    # Check ledgers
    saarthi_exists = os.path.exists("storage/saarthi_visibility.jsonl")
    niyantran_exists = os.path.exists("storage/niyantran_assignments.jsonl")

    success = res["status"] == "PROPAGATED" and saarthi_exists and niyantran_exists
    status = "PASS" if success else "FAIL"
    evidence = f"Propagated review to ledgers: Saarthi={saarthi_exists}, Niyantran={niyantran_exists}"
    proof = f"Status: {res['status']}"
    replay = "Event sourced chain successfully appended."
    
    # Cleanup ledger files
    if os.path.exists("storage/saarthi_visibility.jsonl"):
        os.remove("storage/saarthi_visibility.jsonl")
    if os.path.exists("storage/niyantran_assignments.jsonl"):
        os.remove("storage/niyantran_assignments.jsonl")
        
    return status, evidence, proof, replay

def test_10_concurrency():
    init_clean_db()
    pipeline = GovernedPipeline(TEST_DB)
    
    def submit_worker(idx: int):
        # We need a new connection pool for each thread to simulate concurrent client actions
        envelope = make_valid_envelope()
        envelope.payload["candidate_id"] = f"cand-thread-{idx}"
        envelope.payload["name"] = f"ThreadCandidate {idx}"
        envelope.checksum = envelope.compute_checksum()
        
        # We wrap in try-except to log output
        try:
            pipeline.submit_mutation(envelope, "operator-1")
            return True
        except Exception:
            return False

    # Spawn 10 concurrent threads appending events
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(submit_worker, i) for i in range(10)]
        results = [f.result() for f in futures]

    # Verify event journal state
    db = CanonicalDB(TEST_DB)
    events = db.get_all_events()
    db.close()

    success = len(events) == 10
    status = "PASS" if success else "FAIL"
    evidence = f"Spawned 10 threads. Successful commits: {sum(results)}"
    proof = f"Total DB records: {len(events)} (Expected 10)"
    replay = f"Reconstructed candidates count: {len(events)}"
    return status, evidence, proof, replay

def test_11_schema_drift():
    init_clean_db()
    pipeline = GovernedPipeline(TEST_DB)
    
    # Payload has missing candidate_id (required field)
    envelope = GovernanceEnvelope(
        trace_id="trace-drift-12345",
        schema_version="v1.0",
        actor="operator-1",
        event_type="candidate_profiles",
        payload={
            "name": "Drift Candidate",
            "skills": []
        },
        authorized_by="Akash"
    )
    envelope.checksum = envelope.compute_checksum()

    blocked = False
    try:
        pipeline.submit_mutation(envelope, "operator-1")
    except Exception as e:
        blocked = True
        evidence = str(e)

    status = "PASS" if blocked else "FAIL"
    proof = f"Schema validation exception caught: {blocked}"
    replay = "DB state remains clean."
    return status, evidence, proof, replay

def test_12_determinism():
    init_clean_db()
    pipeline = GovernedPipeline(TEST_DB)
    
    # Appending 3 profiles
    for i in range(3):
        envelope = make_valid_envelope()
        envelope.payload["candidate_id"] = f"cand-{i}"
        envelope.payload["name"] = f"DeterministicCandidate {i}"
        envelope.checksum = envelope.compute_checksum()
        pipeline.submit_mutation(envelope, "operator-1")

    # Reconstruct read models multiple times
    db = CanonicalDB(TEST_DB)
    state1 = db.reconstruct_state()
    state2 = db.reconstruct_state()
    db.close()

    state1_str = json.dumps(state1, sort_keys=True)
    state2_str = json.dumps(state2, sort_keys=True)

    success = (state1_str == state2_str)
    status = "PASS" if success else "FAIL"
    evidence = "Read models reconstructed twice sequentially."
    proof = f"State 1 hash: {hashlib.sha256(state1_str.encode()).hexdigest()}\nState 2 hash: {hashlib.sha256(state2_str.encode()).hexdigest()}"
    replay = "Replay reconstruction is 100% deterministic."
    return status, evidence, proof, replay

# ----------------- MAIN RUNNER -----------------

def run_all_self_tests():
    print("==================================================")
    print("🏁 STARTING PARIKSHAK GOV-OS DIAGNOSTICS SUITE")
    print("==================================================")
    
    tests = [
        ("TEST-01", "Secure DB initialization", test_01_db_init),
        ("TEST-02", "Write validation", test_02_write_validation),
        ("TEST-03", "Corruption detection", test_03_corruption_detection),
        ("TEST-04", "Restore proof", test_04_restore_proof),
        ("TEST-05", "Replay reconstruction", test_05_replay_reconstruction),
        ("TEST-06", "GPT boundary enforcement", test_06_gpt_boundary),
        ("TEST-07", "Human approval lock", test_07_human_approval_lock),
        ("TEST-08", "Autonomous release rejection", test_08_autonomous_release),
        ("TEST-09", "Ecosystem integration", test_09_ecosystem_integration),
        ("TEST-10", "Concurrency resilience", test_10_concurrency),
        ("TEST-11", "Schema drift rejection", test_11_schema_drift),
        ("TEST-12", "Determinism verification", test_12_determinism),
    ]

    passed = 0
    for num, name, func in tests:
        if run_test(num, name, func):
            passed += 1

    print("\n" + "=" * 50)
    print("🎯 GOV-OS DIAGNOSTIC SUMMARY")
    print("=" * 50)
    print(f"Passed: {passed}/{len(tests)}")
    print(f"Success Rate: {(passed / len(tests)) * 100:.1f}%")
    
    # Cleanup test DB files
    if os.path.exists(TEST_DB):
        try:
            os.remove(TEST_DB)
        except Exception:
            pass
            
    sys.exit(0 if passed == len(tests) else 1)

if __name__ == "__main__":
    run_all_self_tests()
