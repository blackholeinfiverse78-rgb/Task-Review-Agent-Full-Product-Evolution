import requests
import json
import sys

BASE_URL = "http://localhost:8000/api/v1/lifecycle"

def run_verification():
    print("Checking backend health...")
    try:
        health_resp = requests.get("http://localhost:8000/health")
        print(f"Health check status: {health_resp.status_code}, body: {health_resp.json()}")
    except Exception as e:
        print(f"Health check failed to connect: {e}")
        sys.exit(1)

    print("\n1. Testing task submission form data...")
    submit_data = {
        "task_title": "Build a Secure Async API Gateway for User Authentication",
        "task_description": "Create a comprehensive async REST API gateway with JWT authorization and Pydantic schema validation. Includes Docker compose configuration and full documentation.",
        "submitted_by": "Ishan Shirode",
        "github_repo_link": "https://github.com/blackholeinfiverse78-rgb/Task-Review-Agent-Full-Product-Evolution",
        "module_id": "task-review-agent",
        "schema_version": "v1.0"
    }
    
    try:
        res = requests.post(f"{BASE_URL}/submit", data=submit_data)
        print(f"Submission status: {res.status_code}")
        if res.status_code != 200:
            print(f"Submission Error: {res.text}")
            sys.exit(1)
            
        submit_res = res.json()
        print("Submission Response:")
        print(json.dumps(submit_res, indent=2))
        
        submission_id = submit_res["submission_id"]
    except Exception as e:
        print(f"Submission request failed: {e}")
        sys.exit(1)

    print("\n2. Testing review details retrieval...")
    try:
        res = requests.get(f"{BASE_URL}/review/{submission_id}")
        print(f"Review status: {res.status_code}")
        if res.status_code != 200:
            print(f"Review Error: {res.text}")
            sys.exit(1)
            
        review_res = res.json()
        print("Review Response:")
        print(json.dumps(review_res, indent=2))
    except Exception as e:
        print(f"Review request failed: {e}")
        sys.exit(1)

    print("\n3. Testing next task details retrieval...")
    try:
        res = requests.get(f"{BASE_URL}/next/{submission_id}")
        print(f"Next task status: {res.status_code}")
        if res.status_code != 200:
            print(f"Next task Error: {res.text}")
            sys.exit(1)
            
        next_res = res.json()
        print("Next Task Response:")
        print(json.dumps(next_res, indent=2))
    except Exception as e:
        print(f"Next task request failed: {e}")
        sys.exit(1)

    print("\n4. Testing submission history retrieval...")
    try:
        res = requests.get(f"{BASE_URL}/history")
        print(f"History status: {res.status_code}")
        if res.status_code != 200:
            print(f"History Error: {res.text}")
            sys.exit(1)
            
        history_res = res.json()
        print(f"History items count: {len(history_res)}")
        print("Latest History Item:")
        print(json.dumps(history_res[-1], indent=2))
    except Exception as e:
        print(f"History request failed: {e}")
        sys.exit(1)

    print("\n5. Testing Gov-OS review approval route (for Human in the loop)...")
    try:
        # Check pending reviews
        pending_resp = requests.get("http://localhost:8000/api/v1/review/pending")
        pending_cases = pending_resp.json()
        print(f"Pending reviews count: {len(pending_cases)}")
        
        trace_id = "trace-test-default-123456"
        for item in pending_cases:
            if item.get("submission_id") == submission_id:
                trace_id = item.get("trace_id", trace_id)
                print(f"Found pending review. Trace ID: {trace_id}")
                break
        
        # Approve using /api/v1/review/approve
        # We need a GovernanceRequest body
        approve_data = {
            "submission_id": submission_id,
            "operator_id": "Akash",
            "operator_role": "SENIOR_REVIEW_OPERATOR",
            "action": "approve",
            "trace_id": trace_id,
            "expected_version": 1,
            "reason_taxonomy": "HUMAN_VALIDATION_FAILURE"
        }
        res = requests.post("http://localhost:8000/api/v1/review/approve", json=approve_data)
        print(f"Gov-OS Approve status: {res.status_code}")
        print(res.json())
        if res.status_code != 200:
            print("Failed to approve review.")
            sys.exit(1)
    except Exception as e:
        print(f"Approve request failed: {e}")
        sys.exit(1)

    print("\n=============================================")
    print("ALL API FLOW TESTS PASSED SUCCESSFULLY!")
    print("=============================================")

if __name__ == "__main__":
    run_verification()
