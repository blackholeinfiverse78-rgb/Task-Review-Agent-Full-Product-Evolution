"""
Candidate Review Pipeline Integration Tests — Parikshak v6.0.0
Verifies:
1. Dataset intake validation (success and fail-fast)
2. Production review execution and report contracts (8 mandatory fields)
3. Next-task recommendation and justification
4. Downstream ecosystem propagation (Gov-OS, Saarthi, Niyantran, Pravah)
5. Replay trace continuity
"""
import os
import json
import uuid
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from main import app
from db.persistent_storage import product_storage
from canonical_db.db import CanonicalDB
from security.middleware import SecurityConfig, UserRole

gov_token = SecurityConfig.create_access_token({"sub": "Akash", "role": UserRole.GOVERNOR.value})
auth_headers = {"Authorization": f"Bearer {gov_token}"}


client = TestClient(app)

@pytest.fixture(autouse=True)
def cleanup():
    """Clear product storage and database tables before each test."""
    product_storage.clear_all()
    # Clean up stale backups
    import shutil
    for bdir in ["storage/backups", "storage/checkpoints"]:
        if os.path.exists(bdir):
            try:
                shutil.rmtree(bdir)
            except Exception:
                pass
        os.makedirs(bdir, exist_ok=True)

    # Reset Canonical DB by removing the database files completely
    db_path = "storage/canonical_db.sqlite"
    for ext in ("", "-wal", "-shm"):
        fpath = db_path + ext
        if os.path.exists(fpath):
            try:
                os.remove(fpath)
            except Exception:
                pass
    
    # Reset files
    for fpath in ["storage/saarthi_visibility.jsonl", "storage/niyantran_assignments.jsonl", "storage/pravah_replay.jsonl"]:
        if os.path.exists(fpath):
            try:
                os.remove(fpath)
            except Exception:
                pass
    yield

def test_intake_validation_fail_fast():
    """Verify that intake validation blocks execution when fields are missing."""
    payload = {
        "assigned_task": "", # Invalid / empty
        "original_task_document": "Build API",
        "review_packet": "Header check",
        "repository_or_commit": "http://github.com/test",
        "submission_date": "2026-06-26T14:30:17Z",
        "due_date": "2026-06-27T14:30:17Z",
        "trace_id": "short" # Too short
    }
    # FastAPI schema validation check (validation error or ValueError)
    resp = client.post("/api/v1/production/intake", json=payload, headers=auth_headers)
    assert resp.status_code in (400, 422)

def test_intake_and_review_pipeline_success():
    """Verify that a valid intake executes evaluation successfully."""
    trace_id = f"trace-test-{uuid.uuid4().hex[:8]}"
    payload = {
        "assigned_task": "Implement Secure REST API Authentication",
        "original_task_document": "Objective: Build JWT auth. Deliverables: login, register endpoints.",
        "review_packet": "Check endpoints and JWT RS256 validation.",
        "repository_or_commit": os.path.abspath("."), # Evaluate current repository
        "submission_date": datetime.now(timezone.utc).isoformat(),
        "due_date": datetime.now(timezone.utc).isoformat(),
        "supporting_evidence": {"evidence_files": ["api/production.py"]},
        "additional_instructions": "Check for docstrings.",
        "trace_id": trace_id,
        "assigned_task_id": "T-GOV-001"
    }

    resp = client.post("/api/v1/production/intake", json=payload, headers=auth_headers)
    assert resp.status_code == 200, resp.text
    res_data = resp.json()

    assert res_data["trace_id"] == trace_id
    assert res_data["status"] == "QUEUED"
    assert res_data["review_state"] == "PENDING_REVIEW"
    
    review = res_data["review"]
    # Check 8 mandatory fields
    assert "evaluation_result" in review
    assert "failure_type" in review
    assert "score" in review
    assert "readiness_percent" in review
    assert "evaluation_summary" in review
    assert "selected_task_id" in review
    assert "selection_reason" in review
    assert "evidence_used" in review
    
    # Check Markdown report formatting contains sections
    summary = review["evaluation_summary"]
    assert "WHAT'S DONE WELL" in summary
    assert "MISSING / INCOMPLETE" in summary
    assert "REQUIRED FIXES" in summary
    assert "OPERATIONAL METRICS" in summary
    assert "EVIDENCE USED" in summary
    assert "RECOMMENDATION & DISPATCH" in summary

    # Verify persisted in database
    submission = product_storage.get_submission(res_data["submission_id"])
    assert submission is not None
    assert submission.review_state == "PENDING_REVIEW"

    review_record = product_storage.get_review_by_submission(res_data["submission_id"])
    assert review_record is not None
    assert review_record.trace_id == trace_id

def test_downstream_ecosystem_propagation():
    """Verify trace propagation across Gov-OS, Saarthi, Niyantran, and Pravah targets."""
    trace_id = f"trace-test-{uuid.uuid4().hex[:8]}"
    payload = {
        "assigned_task": "Gov-OS Integration Validation",
        "original_task_document": "Implement Gov-OS journal and Pravah replay adapters.",
        "review_packet": "Verify all adapters.",
        "repository_or_commit": os.path.abspath("."),
        "submission_date": datetime.now(timezone.utc).isoformat(),
        "due_date": datetime.now(timezone.utc).isoformat(),
        "supporting_evidence": {"evidence_files": ["canonical_db/integration.py"]},
        "trace_id": trace_id,
        "assigned_task_id": "T-GOV-001"
    }

    # 1. Run intake & evaluation
    resp = client.post("/api/v1/production/intake", json=payload, headers=auth_headers)
    assert resp.status_code == 200
    res_data = resp.json()
    submission_id = res_data["submission_id"]

    # Get review to check expected version
    pending_list = client.get("/api/v1/review/pending", headers=auth_headers).json()
    expected_version = 1
    for r in pending_list:
        if r["submission_id"] == submission_id:
            expected_version = r["expected_version"]

    # 2. Approve submission via Human-in-Loop Governance endpoint
    # Requires Operator Akash signature
    approve_payload = {
        "trace_id": trace_id,
        "submission_id": submission_id,
        "operator_id": "Akash",
        "operator_role": "REVIEW_OPERATOR",
        "action": "approve",
        "expected_version": expected_version,
        "reason_taxonomy": "HUMAN_VALIDATION_FAILURE"
    }
    
    # We call approve endpoint
    approve_resp = client.post("/api/v1/review/approve", json=approve_payload, headers=auth_headers)
    assert approve_resp.status_code == 200, approve_resp.text

    # 3. Verify Gov-OS DB commit (sequence appended)
    db = CanonicalDB("storage/canonical_db.sqlite")
    events = db.get_all_events()
    assert len(events) > 0
    review_event = next((e for e in events if e["trace_id"] == trace_id and e["event_type"] == "review_history"), None)
    assert review_event is not None
    
    # Verify cryptographic sequence lineage exists
    assert review_event["event_hash"] is not None
    assert review_event["parent_event_hash"] is not None
    db.close()

    # 4. Verify Saarthi Ledger entry
    saarthi_path = "storage/saarthi_visibility.jsonl"
    assert os.path.exists(saarthi_path)
    with open(saarthi_path, "r", encoding="utf-8") as f:
        saarthi_lines = [json.loads(line) for line in f]
    saarthi_entry = next((e for e in saarthi_lines if e["trace_id"] == trace_id), None)
    assert saarthi_entry is not None
    assert saarthi_entry["destination"] == "Saarthi"

    # 5. Verify Niyantran Assignments Ledger entry
    niyantran_path = "storage/niyantran_assignments.jsonl"
    assert os.path.exists(niyantran_path)
    with open(niyantran_path, "r", encoding="utf-8") as f:
        niyantran_lines = [json.loads(line) for line in f]
    niyantran_entry = next((e for e in niyantran_lines if e["trace_id"] == trace_id), None)
    assert niyantran_entry is not None
    
    # 6. Verify Pravah Replay Ledger entry (including trace continuity)
    pravah_path = "storage/pravah_replay.jsonl"
    assert os.path.exists(pravah_path)
    with open(pravah_path, "r", encoding="utf-8") as f:
        pravah_lines = [json.loads(line) for line in f]
    pravah_entry = next((e for e in pravah_lines if e["trace_id"] == trace_id), None)
    
    assert pravah_entry is not None
    assert pravah_entry["destination"] == "Pravah"
    assert pravah_entry["event_id"] == review_event["event_id"]
    assert pravah_entry["event_hash"] == review_event["event_hash"]
    assert pravah_entry["sequence"] == review_event["sequence"]
    assert pravah_entry["intake_payload"] is not None
    assert pravah_entry["intake_payload"]["assigned_task"] == "Gov-OS Integration Validation"
    assert pravah_entry["review_payload"]["review_id"] is not None
