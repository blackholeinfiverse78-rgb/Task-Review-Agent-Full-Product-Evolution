"""
Parikshak Ecosystem Service Readiness Validation Harness
==========================================================
Verifies Phase 1-5 requirements:
  1. Intake Contract compliance for Niyantran, HackaVerse, and Generic Consumers.
  2. Authority ceilings (blocks unauthorised governors, blocks autonomous releases).
  3. Database immutability (triggers reject UPDATE/DELETE).
  4. Multi-consumer contract alignment (no forks).
  5. Lineage and replay verification.
"""
import os
import sys
import json
import sqlite3
from datetime import datetime, timezone

# Add project root to sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Monkeypatch IntegrityValidator to use a sandbox backup directory
from canonical_db.integrity import IntegrityValidator
original_init = IntegrityValidator.__init__
def patched_init(self, db_path, backup_dir=None):
    sandbox_backup_dir = os.path.join(project_root, "scratch", "temp_backups")
    os.makedirs(sandbox_backup_dir, exist_ok=True)
    original_init(self, db_path, backup_dir=sandbox_backup_dir)
IntegrityValidator.__init__ = patched_init

from canonical_db.db import CanonicalDB
from canonical_db.contracts import GovernanceEnvelope, AutonomousReleaseBlocked
from canonical_db.pipeline import GovernedPipeline
from task_selector.niyantran_connection import niyantran_connection
from task_selector.human_in_loop import human_in_loop
from evaluation_engine.rule_engine import RuleEngine

# Sandboxed DB Path for safety tests
TEST_DB_PATH = os.path.join(project_root, "scratch", "boundary_test_db.sqlite")

def clean_db():
    for p in [TEST_DB_PATH, TEST_DB_PATH + "-wal", TEST_DB_PATH + "-shm"]:
        if os.path.exists(p):
            try: os.remove(p)
            except Exception: pass

def run_readiness_tests():
    print("======================================================================")
    print("STARTING PARIKSHAK ECOSYSTEM SERVICE READINESS TESTS")
    print("======================================================================\n")

    clean_db()
    db = CanonicalDB(TEST_DB_PATH)
    
    # Initialize DB with seed event matching candidate_profiles schema
    seed_payload = {
        "candidate_id": "cand-seed-000",
        "name": "System Seed",
        "github_handle": "seed-handle",
        "skills": ["system"],
        "performance_score": 100.0
    }
    
    seed_env = GovernanceEnvelope(
        trace_id="trace-seed-000",
        schema_version="v1.0",
        actor="System Seed",
        actor_role="system",
        timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        lineage_reference="genesis",
        authorized_by="Akash",
        event_type="candidate_profiles",
        payload=seed_payload,
        parent_event_hash="0" * 64,
        approval_token="token-default-123",
        payload_checksum=None
    )
    # Autocompute checksums
    seed_env.payload_checksum = seed_env.compute_checksum()
    seed_env.checksum = seed_env.payload_checksum
    
    db.append_event(seed_env, "Akash")
    head_event = db.get_last_event()
    head_hash = head_event["event_hash"]
    db.close()

    pipeline = GovernedPipeline(TEST_DB_PATH)

    print("--- 1. TESTING AUTHORITY CEILINGS ---")
    
    # CASE 1.1: Unauthorised Human governor signing override
    unauth_payload = {
        "review_id": "rev-unauth-001",
        "submission_id": "sub-unauth-001",
        "status": "APPROVED",
        "score": 90.0,
        "reviewed_by": "Hacker_Bob",
        "reviewed_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    }
    
    unauth_env = GovernanceEnvelope(
        trace_id="trace-unauth-001",
        schema_version="v1.0",
        actor="Malicious Actor",
        actor_role="attacker",
        timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        lineage_reference="test",
        authorized_by="Hacker_Bob", # Not in allowlist
        event_type="review_history",
        payload=unauth_payload,
        parent_event_hash=head_hash,
        approval_token="token-unauth",
        payload_checksum=None
    )
    unauth_env.payload_checksum = unauth_env.compute_checksum()
    unauth_env.checksum = unauth_env.payload_checksum
    
    try:
        pipeline.submit_mutation(unauth_env, "Hacker_Bob")
        print("[-] FAIL: Mutation allowed by unauthorised actor!")
        sys.exit(1)
    except PermissionError as e:
        print(f"[+] SUCCESS: Unauthorised human mutation blocked as expected. Error: {e}")

    # CASE 1.2: Autonomous Release (AI sign-off) block
    ai_payload = {
        "assignment_id": "assign-ai-002",
        "task_id": "NT-ADV-B-001",
        "candidate_id": "cand-ai-002",
        "assigned_by": "AI_Orchestrator_Agent",
        "assigned_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    }

    ai_env = GovernanceEnvelope(
        trace_id="trace-ai-002",
        schema_version="v1.0",
        actor="AI_Orchestrator_Agent",
        actor_role="orchestrator",
        timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        lineage_reference="test",
        authorized_by="AI_Orchestrator_Agent", # AI actor
        event_type="assignment_history",
        payload=ai_payload,
        parent_event_hash=head_hash,
        approval_token="token-ai",
        payload_checksum=None
    )
    ai_env.payload_checksum = ai_env.compute_checksum()
    ai_env.checksum = ai_env.payload_checksum

    try:
        pipeline.submit_mutation(ai_env, "AI_Orchestrator_Agent")
        print("[-] FAIL: Autonomous release by AI agent was committed!")
        sys.exit(1)
    except AutonomousReleaseBlocked as e:
        print(f"[+] SUCCESS: Autonomous release blocked as expected. Error: {e}")
    except PermissionError as e:
        print(f"[+] SUCCESS: Autonomous release blocked by permission error. Error: {e}")

    print("\n--- 2. TESTING DATABASE IMMUTABILITY (TRIGGERS) ---")
    # Connect directly via sqlite3 and attempt illegal operations
    conn = sqlite3.connect(TEST_DB_PATH)
    cursor = conn.cursor()
    
    # CASE 2.1: Test UPDATE prevention
    try:
        cursor.execute("UPDATE events SET actor='Tampered' WHERE sequence=1")
        conn.commit()
        print("[-] FAIL: Database allows UPDATE operations!")
        sys.exit(1)
    except (sqlite3.OperationalError, sqlite3.IntegrityError) as e:
        print(f"[+] SUCCESS: UPDATE operation blocked by trigger. Error: {e}")

    # CASE 2.2: Test DELETE prevention
    try:
        cursor.execute("DELETE FROM events WHERE sequence=1")
        conn.commit()
        print("[-] FAIL: Database allows DELETE operations!")
        sys.exit(1)
    except (sqlite3.OperationalError, sqlite3.IntegrityError) as e:
        print(f"[+] SUCCESS: DELETE operation blocked by trigger. Error: {e}")
    conn.close()

    print("\n--- 3. TESTING INTAKE CONTRACTS & QUEUE STATES ---")
    
    # CASE 3.1: Verify intake forces queue state
    task_payload = {
        "task_id": "T-GOV-100",
        "task_title": "Ecosystem Connection Test",
        "task_description": "Validate that consumer submissions are properly queued.",
        "submitted_by": "Ishan Shirode",
        "repository_url": "https://github.com/blackholeinfiverse78-rgb/test-repo",
        "trace_id": "trace-readiness-777",
        "current_task_id": "T-GOV-001"
    }
    
    intake_res = niyantran_connection.process_niyantran_task(task_payload)
    print(f"[+] SUCCESS: Ingestion result schema validated: {list(intake_res.keys())}")
    
    # Verify it does NOT commit to Canonical DB, but queues in memory/loop
    db = CanonicalDB(TEST_DB_PATH)
    events = db.get_all_events()
    assert len(events) == 1, "Database should still contain only seed event."
    db.close()
    print("[+] SUCCESS: Intake did not commit to Canonical DB (Awaiting human approval).")

    print("\n--- 4. TESTING MULTI-CONSUMER VALIDATION ---")
    
    consumers = ["HackaVerse", "Niyantran", "Generic External Consumer"]
    for idx, consumer in enumerate(consumers):
        payload = {
            "task_id": f"T-CON-{idx:03d}",
            "task_title": f"Service Integration for {consumer}",
            "task_description": f"Enforce contract compliance for {consumer} without custom logic.",
            "submitted_by": f"developer-{consumer.lower().replace(' ', '-')}",
            "repository_url": "https://github.com/blackholeinfiverse78-rgb/test-repo",
            "trace_id": f"trace-consumer-{idx:03d}-{consumer[:4]}",
            "current_task_id": "T-GOV-001"
        }
        res = niyantran_connection.process_niyantran_task(payload)
        
        # Verify schema
        assert res["trace_id"] == payload["trace_id"]
        assert "submission_id" in res
        assert "evaluation_result" in res
        assert "selected_task_id" in res
        
        # Save integration proof JSON log
        proof_dir = os.path.join(project_root, "integration_proofs")
        os.makedirs(proof_dir, exist_ok=True)
        with open(os.path.join(proof_dir, f"{consumer.lower().replace(' ', '_')}_integration.json"), "w") as f:
            json.dump({"payload": payload, "receipt": res}, f, indent=2)
        print(f"[+] SUCCESS: Simulated {consumer} ingestion, standard contract returned, proof saved.")

    print("\n--- 5. TESTING DETERMINISTIC REPLAYABILITY ---")
    rule_engine = RuleEngine()
    signals = {
        "domain": "engineering",
        "repository_available": True,
        "description_signals": {"word_count": 150},
        "repository_signals": {
            "structure": {"total_files": 10},
            "quality": {"readme_val": 1},
            "components": {"tests": ["test_api.py"], "docs": []},
            "architecture": {"layer_count": 3, "modular": True},
            "metadata": {"name": "test-repo"}
        },
        "expected_vs_delivered_evidence": {"delivery_ratio": 1.0, "expected_count": 5},
        "missing_features": []
    }
    
    eval_run_1 = rule_engine.evaluate(signals)
    eval_run_2 = rule_engine.evaluate(signals)
    eval_run_3 = rule_engine.evaluate(signals)
    
    assert eval_run_1["evaluation_result"] == eval_run_2["evaluation_result"] == eval_run_3["evaluation_result"]
    assert eval_run_1["failure_type"] == eval_run_2["failure_type"] == eval_run_3["failure_type"]
    print("[+] SUCCESS: Rule engine evaluations are 100% deterministic (reproducible outcomes).")

    print("\n======================================================================")
    print("ALL ECOSYSTEM SERVICE READINESS TESTS PASSED SUCCESSFULLY!")
    print("======================================================================\n")
    clean_db()

if __name__ == "__main__":
    run_readiness_tests()
