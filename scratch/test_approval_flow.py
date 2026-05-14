import sys
import os
import json
from fastapi.testclient import TestClient

# Add current directory to path
sys.path.append(os.getcwd())

from main import app
from db.persistent_storage import product_storage

client = TestClient(app)

def test_full_governance_flow():
    # Clear storage
    product_storage.clear_all()
    
    sample_submission = {
        "task_id": "T-GOV-001",
        "task_title": "Governance Implementation Test",
        "task_description": "Building a human approval layer for deterministic systems.",
        "submitted_by": "Akash",
        "trace_id": "test-trace-001",
        "module_id": "task-review-agent",
        "schema_version": "v1.0"
    }

    print("\n--- PHASE 1: SUBMISSION ---")
    # 1. Submit task
    response = client.post("/api/v1/production/niyantran/submit", json=sample_submission)
    print(f"Submission Response: {response.json()}")
    assert response.status_code == 200
    assert response.json()["review_state"] == "PENDING_REVIEW"
    
    submission_id = response.json()["submission_id"]
    trace_id = response.json()["trace_id"]

    print("\n--- PHASE 2: DASHBOARD VISIBILITY ---")
    # 2. Check dashboard
    response = client.get("/api/v1/review/all")
    print(f"Dashboard Count: {len(response.json())}")
    assert len(response.json()) == 1
    assert response.json()[0]["submission_id"] == submission_id
    assert response.json()[0]["review_state"] == "PENDING_REVIEW"

    print("\n--- PHASE 3: APPROVAL ---")
    # 3. Approve
    approve_payload = {
        "trace_id": trace_id,
        "submission_id": submission_id,
        "action": "approve"
    }
    response = client.post("/api/v1/review/approve", json=approve_payload)
    print(f"Approve Response: {response.json()}")
    assert response.status_code == 200
    assert response.json()["status"] == "APPROVED"

    print("\n--- PHASE 4: STATE PERSISTENCE ---")
    # 4. Check state again
    response = client.get("/api/v1/review/all")
    assert response.json()[0]["review_state"] == "APPROVED"
    print("State persisted as APPROVED.")

    print("\n--- PHASE 5: MODIFY FLOW ---")
    # Submit another
    sample_submission["trace_id"] = "test-trace-002"
    response = client.post("/api/v1/production/niyantran/submit", json=sample_submission)
    sub2_id = response.json()["submission_id"]
    
    # Modify it
    modify_payload = {
        "trace_id": "test-trace-002",
        "submission_id": sub2_id,
        "action": "modify",
        "override_task_id": "T-GOV-OVERRIDE"
    }
    response = client.post("/api/v1/review/modify", json=modify_payload)
    print(f"Modify Response: {response.json()}")
    assert response.json()["status"] == "MODIFIED"
    assert response.json()["assigned_task"] == "T-GOV-OVERRIDE"

    print("\n--- PHASE 6: AUDIT LOG CHECK ---")
    audit_files = os.listdir("storage/audit_logs")
    print(f"Audit files created: {audit_files}")
    assert len(audit_files) > 0
    
    with open(f"storage/audit_logs/{audit_files[0]}", "r") as f:
        logs = f.readlines()
        print(f"Audit log entries: {len(logs)}")
        for log in logs:
            print(f"  Log: {log.strip()}")

    print("\nALL GOVERNANCE TESTS PASSED!")

if __name__ == "__main__":
    test_full_governance_flow()
