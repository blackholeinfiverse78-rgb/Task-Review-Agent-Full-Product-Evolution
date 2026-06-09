#!/usr/bin/env python3
"""
Production Readiness Test - Validates all critical requirements
Tests submission ID traceability, input validation, and deterministic behavior
"""
import requests
import json
import time
from datetime import datetime

def test_production_readiness():
    """Test all production readiness requirements"""
    base_url = "http://localhost:8000"
    
    try:
        requests.get(base_url)
    except requests.exceptions.ConnectionError:
        import pytest
        pytest.skip("FastAPI server is not running on http://localhost:8000")
        
    print("PRODUCTION READINESS TEST")
    print("=" * 50)
    
    # Test 1: Submission ID Traceability
    print("\n1. Testing Submission ID Traceability...")
    
    test_data = {
        "task_title": "Test API Authentication System",
        "task_description": "Implement JWT-based authentication with role-based access control for REST API endpoints",
        "submitted_by": "TestUser",
        "github_repo_link": "https://github.com/test/auth-system",
        "module_id": "security-implementation",
        "schema_version": "v1.0"
    }
    
    response = requests.post(f"{base_url}/api/v1/lifecycle/submit", data=test_data)
    
    if response.status_code == 200:
        result = response.json()
        submission_id = result.get("submission_id")
        submission_timestamp = result.get("submission_timestamp")
        attempt_number = result.get("attempt_number", 1)
        
        print(f"[PASS] Submission ID: {submission_id}")
        print(f"[PASS] Timestamp: {submission_timestamp}")
        print(f"[PASS] Attempt Number: {attempt_number}")
        
        # Validate ID format
        if submission_id and submission_id.startswith("sub-"):
            print("[PASS] ID Format: Valid")
        else:
            print("[FAIL] ID Format: Invalid")
            return False
    else:
        print(f"[FAIL] Submission failed: {response.status_code}")
        return False
    
    # Test 2: Deterministic Behavior
    print("\n2. Testing Deterministic Behavior...")
    
    # Submit same data twice
    response1 = requests.post(f"{base_url}/api/v1/lifecycle/submit", data=test_data)
    time.sleep(0.1)  # Small delay
    response2 = requests.post(f"{base_url}/api/v1/lifecycle/submit", data=test_data)
    
    if response1.status_code == 200 and response2.status_code == 200:
        result1 = response1.json()
        result2 = response2.json()
        
        # Check if base content hash is same (deterministic part)
        id1_base = result1["submission_id"].split("-")[1]  # Content hash part
        id2_base = result2["submission_id"].split("-")[1]  # Content hash part
        
        if id1_base == id2_base:
            print("[PASS] Content Hash: Deterministic")
        else:
            print("[FAIL] Content Hash: Non-deterministic")
            return False
            
        # Check if scores are identical (deterministic evaluation)
        score1 = result1["review_summary"]["score"]
        score2 = result2["review_summary"]["score"]
        
        if score1 == score2:
            print(f"[PASS] Score Consistency: {score1} = {score2}")
        else:
            print(f"[FAIL] Score Inconsistency: {score1} != {score2}")
            return False
    else:
        print("[FAIL] Deterministic test failed")
        return False
    
    # Test 3: Registry Validation
    print("\n3. Testing Registry Validation...")
    
    invalid_data = test_data.copy()
    invalid_data["module_id"] = "invalid-module"
    
    response = requests.post(f"{base_url}/api/v1/lifecycle/submit", data=invalid_data)
    
    if response.status_code == 200:
        result = response.json()
        score = result["review_summary"]["score"]
        
        if score == 0:
            print("[PASS] Registry Rejection: Working")
        else:
            print(f"[FAIL] Registry Rejection: Failed (Score: {score})")
            return False
    else:
        print("[FAIL] Registry validation test failed")
        return False
    
    # Test 4: Traceability Retrieval
    print("\n4. Testing Traceability Retrieval...")
    
    # Get review details
    review_response = requests.get(f"{base_url}/api/v1/lifecycle/review/{submission_id}")
    
    if review_response.status_code == 200:
        review_data = review_response.json()
        print(f"[PASS] Review Retrieved: {review_data['submission_id']}")
        print(f"[PASS] Score: {review_data['score']}")
        print(f"[PASS] Status: {review_data['status']}")
    else:
        print("[FAIL] Review retrieval failed")
        return False
    
    # Test 5: History Tracking
    print("\n5. Testing History Tracking...")
    
    history_response = requests.get(f"{base_url}/api/v1/lifecycle/history")
    
    if history_response.status_code == 200:
        history = history_response.json()
        print(f"[PASS] History Retrieved: {len(history)} submissions")
        
        # Check if our submission is in history
        found = any(item["submission_id"] == submission_id for item in history)
        if found:
            print("[PASS] Submission in History: Found")
        else:
            print("[FAIL] Submission in History: Not found")
            return False
    else:
        print("[FAIL] History retrieval failed")
        return False
    
    print("\n" + "=" * 50)
    print("ALL PRODUCTION READINESS TESTS PASSED!")
    print("[PASS] Submission ID Traceability: WORKING")
    print("[PASS] Deterministic Behavior: WORKING") 
    print("[PASS] Registry Validation: WORKING")
    print("[PASS] Traceability Retrieval: WORKING")
    print("[PASS] History Tracking: WORKING")
    print("\nSYSTEM IS PRODUCTION READY!")
    
    return True

if __name__ == "__main__":
    try:
        success = test_production_readiness()
        if not success:
            print("\n[FAIL] PRODUCTION READINESS TEST FAILED")
            exit(1)
    except Exception as e:
        print(f"\n[ERROR] Test failed with error: {e}")
        exit(1)