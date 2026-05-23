import sys
import os
import json
from fastapi.testclient import TestClient

# Add current directory to path
sys.path.append(os.getcwd())

from main import app
from db.persistent_storage import product_storage

client = TestClient(app)

GOVERNANCE_OPERATOR = {
    "operator_id": "test-operator-001",
    "operator_role": "REVIEW_OPERATOR",
    "reason_taxonomy": "REQUIREMENT_CORRECTION",
    "expected_version": 1,
}

GOVERNANCE_MODIFIER = {
    "operator_id": "senior-operator-001",
    "operator_role": "SENIOR_REVIEW_OPERATOR",
    "reason_taxonomy": "REQUIREMENT_CORRECTION",
    "authorized_by": "exec-auth-001",
    "expected_version": 1,
}

def test_full_governance_flow():
    # Clear storage
    product_storage.clear_all()
    
    print("\n--- PHASE 1: SUBMISSION ---")
    # Submit via lifecycle endpoint (has trace_id auto-generation)
    form_data = {
        "task_title": "Governance Implementation Test Task",
        "task_description": "Building a human approval layer for deterministic governance systems with full audit trail.",
        "submitted_by": "Akash",
        "module_id": "task-review-agent",
        "schema_version": "v1.0",
    }
    response = client.post("/api/v1/lifecycle/submit", data=form_data)
    print(f"Submission Response: {response.json()}")
    assert response.status_code == 200
    
    submission_id = response.json()["submission_id"]
    print(f"submission_id: {submission_id}")

    print("\n--- PHASE 2: DASHBOARD VISIBILITY ---")
    # Check all reviews endpoint
    response = client.get("/api/v1/review/all")
    all_reviews = response.json()
    print(f"Dashboard Count: {len(all_reviews)}")
    assert len(all_reviews) >= 1
    our_review = next((r for r in all_reviews if r["submission_id"] == submission_id), None)
    assert our_review is not None, f"submission_id {submission_id} not in review queue"
    assert our_review["review_state"] == "PENDING_REVIEW"

    # Get the trace_id from the review record
    trace_id = our_review["trace_id"]

    print("\n--- PHASE 3: APPROVAL ---")
    approve_payload = {
        **GOVERNANCE_OPERATOR,
        "trace_id": trace_id,
        "submission_id": submission_id,
        "action": "approve",
    }
    response = client.post("/api/v1/review/approve", json=approve_payload)
    print(f"Approve Response: {response.json()}")
    assert response.status_code == 200
    assert response.json()["status"] == "APPROVED"

    print("\n--- PHASE 4: STATE PERSISTENCE ---")
    response = client.get("/api/v1/review/all")
    our_review = next((r for r in response.json() if r["submission_id"] == submission_id), None)
    assert our_review["review_state"] == "APPROVED"
    print("State persisted as APPROVED.")

    print("\n--- PHASE 5: MODIFY FLOW ---")
    # Submit another task
    form_data2 = {
        "task_title": "Second Governance Task for Override Test",
        "task_description": "Testing the governance modification flow for assignment override capability.",
        "submitted_by": "Akash",
        "module_id": "task-review-agent",
        "schema_version": "v1.0",
    }
    response = client.post("/api/v1/lifecycle/submit", data=form_data2)
    assert response.status_code == 200
    sub2_id = response.json()["submission_id"]
    
    # Get its trace_id
    all_reviews2 = client.get("/api/v1/review/all").json()
    review2 = next((r for r in all_reviews2 if r["submission_id"] == sub2_id), None)
    assert review2 is not None
    trace2 = review2["trace_id"]
    
    # Modify it
    modify_payload = {
        **GOVERNANCE_MODIFIER,
        "trace_id": trace2,
        "submission_id": sub2_id,
        "action": "modify",
        "override_task_id": "T-GOV-OVERRIDE",
    }
    response = client.post("/api/v1/review/modify", json=modify_payload)
    print(f"Modify Response: {response.json()}")
    assert response.json()["status"] == "MODIFIED"
    assert response.json()["assigned_task"] == "T-GOV-OVERRIDE"

    print("\n--- PHASE 6: AUDIT LOG CHECK ---")
    audit_dir = "storage/audit_logs"
    if os.path.exists(audit_dir):
        audit_files = os.listdir(audit_dir)
        print(f"Audit files created: {audit_files}")
        assert len(audit_files) > 0

    print("\nALL GOVERNANCE TESTS PASSED!")

if __name__ == "__main__":
    test_full_governance_flow()
