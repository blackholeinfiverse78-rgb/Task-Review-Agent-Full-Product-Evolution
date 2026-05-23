#!/usr/bin/env python3
"""
Data Consistency Fix Test - Validates score aggregation pipeline
Tests both valid submissions and registry rejections
"""
from fastapi.testclient import TestClient
from main import app
import json

client = TestClient(app)

def test_data_consistency_fix():
    """Test the data consistency fix"""
    
    print("DATA CONSISTENCY FIX TEST")
    print("=" * 50)
    
    # Test 1: Valid Submission (should have consistent scores)
    print("\n1. Testing Valid Submission Data Consistency...")
    
    valid_data = {
        "task_title": "Implement JWT Authentication API",
        "task_description": "Create a comprehensive JWT-based authentication system with user registration, login, token refresh, and role-based access control. Include password hashing, input validation, and secure token storage. Implement middleware for protected routes and proper error handling.",
        "submitted_by": "TestDeveloper",
        "github_repo_link": "https://github.com/test/jwt-auth-api",
        "module_id": "security-implementation",
        "schema_version": "v1.0"
    }
    
    response = client.post("/api/v1/lifecycle/submit", data=valid_data)
    
    if response.status_code == 200:
        result = response.json()
        submission_id = result["submission_id"]
        
        # Check API response consistency
        api_score = result["review_summary"]["score"]
        api_status = result["review_summary"]["status"]
        
        print(f"API Response - Score: {api_score}, Status: {api_status}")
        
        # Get detailed review
        review_response = client.get(f"/api/v1/lifecycle/review/{submission_id}")
        
        if review_response.status_code == 200:
            review_data = review_response.json()
            
            # Extract all score-related data
            overall_score = review_data["score"]
            overall_status = review_data["status"]
            title_score = review_data.get("title_score", 0)
            description_score = review_data.get("description_score", 0)
            repository_score = review_data.get("repository_score", 0)
            
            print(f"Review Details:")
            print(f"  Overall Score: {overall_score}")
            print(f"  Overall Status: {overall_status}")
            print(f"  Title Score: {title_score}")
            print(f"  Description Score: {description_score}")
            print(f"  Repository Score: {repository_score}")
            print(f"  Component Sum: {title_score + description_score + repository_score}")
            
            # Check for evaluation summary
            eval_summary = review_data.get("evaluation_summary", "")
            print(f"  Evaluation Summary: {eval_summary}")
            
            # Data consistency checks
            consistency_issues = []
            
            # Check 1: API vs Review consistency
            if api_score != overall_score:
                consistency_issues.append(f"API score ({api_score}) != Review score ({overall_score})")
            
            if api_status != overall_status:
                consistency_issues.append(f"API status ({api_status}) != Review status ({overall_status})")
            
            # Check 2: Score-Status alignment
            expected_status = "pass" if overall_score >= 80 else "borderline" if overall_score >= 50 else "fail"
            if overall_status != expected_status:
                consistency_issues.append(f"Score {overall_score} should have status '{expected_status}', got '{overall_status}'")
            
            # Check 3: Component scores should be reasonable
            component_sum = title_score + description_score + repository_score
            if abs(component_sum - overall_score) > 50:  # Allow large variance for severe evidence penalties
                consistency_issues.append(f"Component sum ({component_sum}) significantly different from overall ({overall_score})")
            
            if consistency_issues:
                print("[FAIL] Data Consistency Issues Found:")
                for issue in consistency_issues:
                    print(f"  - {issue}")
                return False
            else:
                print("[PASS] Data Consistency: All checks passed")
        else:
            print(f"[FAIL] Could not retrieve review details: {review_response.status_code}")
            return False
    else:
        print(f"[FAIL] Valid submission failed: {response.status_code}")
        return False
    
    # Test 2: Invalid Module (should have consistent rejection)
    print("\n2. Testing Invalid Module Rejection Consistency...")
    
    invalid_data = valid_data.copy()
    invalid_data["module_id"] = "invalid-module-test"
    
    response = client.post("/api/v1/lifecycle/submit", data=invalid_data)
    
    if response.status_code == 200:
        result = response.json()
        api_score = result["review_summary"]["score"]
        api_status = result["review_summary"]["status"]
        
        print(f"Invalid Module - Score: {api_score}, Status: {api_status}")
        
        if api_score == 0 and api_status == "fail":
            print("[PASS] Invalid Module Rejection: Consistent")
        else:
            print(f"[FAIL] Invalid Module Rejection: Expected score=0, status=fail, got score={api_score}, status={api_status}")
            return False
    else:
        print(f"[FAIL] Invalid module test failed: {response.status_code}")
        return False
    
    print("\n" + "=" * 50)
    print("DATA CONSISTENCY FIX TEST PASSED!")
    print("[PASS] Valid Submission: Consistent data flow")
    print("[PASS] Invalid Module: Proper rejection")
    print("[PASS] Score-Status Alignment: Working")
    print("[PASS] Component Score Integration: Working")
    print("\nDATA CONSISTENCY ISSUE RESOLVED!")
    
    return True

if __name__ == "__main__":
    try:
        success = test_data_consistency_fix()
        if not success:
            print("\n[FAIL] DATA CONSISTENCY FIX TEST FAILED")
            exit(1)
    except Exception as e:
        print(f"\n[ERROR] Test failed with error: {e}")
        exit(1)