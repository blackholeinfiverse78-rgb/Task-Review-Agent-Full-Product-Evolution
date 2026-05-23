"""
Manual Test Suite for Human Review + Approval Workflow
Run these tests to verify the operational layer works correctly.
"""
import requests
import json
import time
import pytest

BASE_URL = "http://localhost:8000"

# Check if local server is running, otherwise skip tests in this module during automated pytest runs
try:
    requests.get(f"{BASE_URL}/api/v1/review/all", timeout=0.5)
    server_running = True
except requests.exceptions.RequestException:
    server_running = False

pytestmark = pytest.mark.skipif(not server_running, reason="Local FastAPI server is not running")

# Test Payloads
SAMPLE_SUBMISSION_PASS = {
    "task_id": "test-001",
    "task_title": "Build REST API with Authentication",
    "task_description": "Implemented a complete REST API with JWT authentication, user management, role-based access control, comprehensive error handling, unit tests with 85% coverage, and full API documentation using Swagger. Repository includes all source code, tests, and deployment instructions.",
    "submitted_by": "Akash Kumar",
    "repository_url": "https://github.com/test/rest-api-auth",
    "module_id": "task-review-agent",
    "schema_version": "v1.0",
    "pdf_text": "",
    "trace_id": "trace-test-001-pass",
    "current_task_id": "T-GOV-001"
}

SAMPLE_SUBMISSION_FAIL = {
    "task_id": "test-002",
    "task_title": "Simple Calculator",
    "task_description": "Made a calculator app.",
    "submitted_by": "Test User",
    "repository_url": None,
    "module_id": "task-review-agent",
    "schema_version": "v1.0",
    "pdf_text": "",
    "trace_id": "trace-test-002-fail",
    "current_task_id": "T-GOV-001"
}

def test_1_submit_task():
    """TEST 1: Submit task and verify it appears in dashboard"""
    print("\n=== TEST 1: Submit Task ===")
    
    response = requests.post(
        f"{BASE_URL}/api/v1/production/niyantran/submit",
        json=SAMPLE_SUBMISSION_PASS
    )
    
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}")
    
    assert result["review_state"] == "PENDING_REVIEW"
    assert result["status"] == "QUEUED"
    print("✓ Task queued for review")
    
    return result

def test_2_view_pending():
    """TEST 2: View pending reviews in dashboard"""
    print("\n=== TEST 2: View Pending Reviews ===")
    
    response = requests.get(f"{BASE_URL}/api/v1/review/all")
    
    print(f"Status: {response.status_code}")
    reviews = response.json()
    print(f"Total reviews: {len(reviews)}")
    
    for review in reviews:
        print(f"  - {review['candidate_name']}: {review['review_state']}")
    
    print("✓ Dashboard accessible")
    return reviews

def test_3_approve():
    """TEST 3: Approve a submission"""
    print("\n=== TEST 3: Approve Submission ===")
    
    # Get first pending review
    reviews = requests.get(f"{BASE_URL}/api/v1/review/all").json()
    pending = [r for r in reviews if r["review_state"] == "PENDING_REVIEW"]
    
    if not pending:
        print("⚠ No pending reviews to approve")
        return
    
    review = pending[0]
    print(f"Approving: {review['submission_id']}")
    
    response = requests.post(
        f"{BASE_URL}/api/v1/review/approve",
        json={
            "trace_id": review["trace_id"],
            "submission_id": review["submission_id"],
            "operator_id": "op-approve-123",
            "operator_role": "REVIEW_OPERATOR",
            "reason_taxonomy": "REQUIREMENT_CORRECTION",
            "action": "approve",
            "expected_version": 1
        }
    )
    
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}")
    
    assert result["status"] == "APPROVED"
    print("✓ Submission approved")

def test_4_reject():
    """TEST 4: Reject a submission"""
    print("\n=== TEST 4: Reject Submission ===")
    
    # Submit a new task first
    response = requests.post(
        f"{BASE_URL}/api/v1/production/niyantran/submit",
        json=SAMPLE_SUBMISSION_FAIL
    )
    
    time.sleep(1)
    
    # Get the submission
    reviews = requests.get(f"{BASE_URL}/api/v1/review/all").json()
    pending = [r for r in reviews if r["review_state"] == "PENDING_REVIEW"]
    
    if not pending:
        print("⚠ No pending reviews to reject")
        return
    
    review = pending[0]
    print(f"Rejecting: {review['submission_id']}")
    
    response = requests.post(
        f"{BASE_URL}/api/v1/review/reject",
        json={
            "trace_id": review["trace_id"],
            "submission_id": review["submission_id"],
            "operator_id": "op-reject-123",
            "operator_role": "REVIEW_OPERATOR",
            "reason_taxonomy": "REQUIREMENT_CORRECTION",
            "action": "reject",
            "expected_version": 1
        }
    )
    
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}")
    
    assert result["status"] == "REJECTED"
    print("✓ Submission rejected")

def test_5_modify():
    """TEST 5: Modify task assignment"""
    print("\n=== TEST 5: Modify Assignment ===")
    
    # Submit a new task
    response = requests.post(
        f"{BASE_URL}/api/v1/production/niyantran/submit",
        json={**SAMPLE_SUBMISSION_PASS, "trace_id": "trace-test-003-modify"}
    )
    
    time.sleep(1)
    
    # Get the submission
    reviews = requests.get(f"{BASE_URL}/api/v1/review/all").json()
    pending = [r for r in reviews if r["review_state"] == "PENDING_REVIEW"]
    
    if not pending:
        print("⚠ No pending reviews to modify")
        return
    
    review = pending[0]
    print(f"Modifying: {review['submission_id']}")
    print(f"Original task: {review['selected_task_id']}")
    
    override_task = "T-GOV-999"
    
    response = requests.post(
        f"{BASE_URL}/api/v1/review/modify",
        json={
            "trace_id": review["trace_id"],
            "submission_id": review["submission_id"],
            "operator_id": "op-modify-123",
            "operator_role": "SENIOR_REVIEW_OPERATOR",
            "reason_taxonomy": "REQUIREMENT_CORRECTION",
            "action": "modify",
            "override_task_id": override_task,
            "authorized_by": "exec-auth-456",
            "expected_version": 1
        }
    )
    
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}")
    
    assert result["status"] == "MODIFIED"
    assert result["assigned_task"] == override_task
    print("✓ Assignment modified")

def test_6_audit_log():
    """TEST 6: Verify audit log is written"""
    print("\n=== TEST 6: Audit Log Verification ===")
    
    import os
    from datetime import datetime
    
    date_str = datetime.now().strftime("%Y-%m-%d")
    log_file = f"storage/audit_logs/audit_{date_str}.jsonl"
    
    if not os.path.exists(log_file):
        print(f"⚠ Audit log not found: {log_file}")
        return
    
    with open(log_file, "r") as f:
        lines = f.readlines()
    
    print(f"Audit entries today: {len(lines)}")
    
    for line in lines[-3:]:
        entry = json.loads(line)
        print(f"  - {entry['action']}: {entry['submission_id']} -> {entry['final_task']}")
    
    print("✓ Audit log verified")

def run_all_tests():
    """Run complete test suite"""
    print("=" * 60)
    print("HUMAN REVIEW + APPROVAL WORKFLOW TEST SUITE")
    print("=" * 60)
    
    try:
        test_1_submit_task()
        test_2_view_pending()
        test_3_approve()
        test_4_reject()
        test_5_modify()
        test_6_audit_log()
        
        print("\n" + "=" * 60)
        print("ALL TESTS PASSED ✓")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_all_tests()
