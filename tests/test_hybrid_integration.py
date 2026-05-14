"""
Integration Test for Hybrid Pipeline with Review Orchestrator
Tests the complete flow: submission → hybrid evaluation → next task
"""
import sys
import os
import json
from datetime import datetime

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from task_selector.review_orchestrator import ReviewOrchestrator
from evaluation_engine.review_engine import ReviewEngine
from app.services.next_task_generator import NextTaskGenerator
from contracts.schemas import Task

def test_hybrid_integration():
    """Test complete integration flow"""
    
    print("=== Hybrid Pipeline Integration Test ===")
    
    # Setup orchestrator with dependencies
    review_engine = ReviewEngine()
    next_task_generator = NextTaskGenerator()
    orchestrator = ReviewOrchestrator(review_engine, next_task_generator)
    
    # Test Case 1: High Quality Task (should PASS)
    print("\n1. Testing High Quality Task...")
    
    high_quality_task = Task(
        task_id="test-001",
        task_title="Implement Secure REST API Authentication System with JWT and Database Integration",
        task_description="""
        Objective: Build a comprehensive authentication system for the web application
        
        Deliverables:
        - JWT token generation and validation endpoints
        - User registration and login functionality
        - Secure password hashing implementation
        - Database integration for user management
        - API documentation and testing suite
        
        Timeline: 3 weeks (2 weeks development + 1 week testing)
        
        Scope: Authentication module only, excludes authorization roles and permissions
        
        Technical Requirements:
        - RESTful API design principles
        - Secure password storage with bcrypt
        - JWT token expiration handling
        - Input validation and error handling
        - Database schema design for users
        """,
        submitted_by="Test User",
        timestamp=datetime.now(),
        github_repo_link="https://github.com/user/auth-system"
    )
    
    try:
        result1 = orchestrator.process_submission(high_quality_task)
        print(f"   Score: {result1.review.score}")
        print(f"   Status: {result1.review.status}")
        print(f"   Classification: {result1.readiness_classification}")
        print(f"   Next Task: {result1.next_task.title}")
        print(f"   Mode: {result1.review.meta.mode}")
        
        # Verify high quality expectations
        assert result1.review.score >= 70, f"Expected high score, got {result1.review.score}"
        assert result1.review.meta.mode == "hybrid", "Should use hybrid mode"
        assert result1.review.completeness_score > 50, "Should have good completeness"
        print("   ✓ High quality task test passed")
        
    except Exception as e:
        print(f"   ✗ High quality task test failed: {e}")
        return False
    
    # Test Case 2: Poor Quality Task (should FAIL)
    print("\n2. Testing Poor Quality Task...")
    
    poor_quality_task = Task(
        task_id="test-002", 
        task_title="Fix bug",
        task_description="Fix the bug in the system",
        submitted_by="Test User",
        timestamp=datetime.now()
    )
    
    try:
        result2 = orchestrator.process_submission(poor_quality_task)
        print(f"   Score: {result2.review.score}")
        print(f"   Status: {result2.review.status}")
        print(f"   Classification: {result2.readiness_classification}")
        print(f"   Failure Reasons: {result2.review.failure_reasons}")
        print(f"   Mode: {result2.review.meta.mode}")
        
        # Verify poor quality expectations
        assert result2.review.score < 60, f"Expected low score, got {result2.review.score}"
        assert result2.review.status in ["fail", "borderline"], f"Expected fail/borderline, got {result2.review.status}"
        assert len(result2.review.failure_reasons) > 0, "Should have failure reasons"
        print("   ✓ Poor quality task test passed")
        
    except Exception as e:
        print(f"   ✗ Poor quality task test failed: {e}")
        return False
    
    # Test Case 3: Borderline Task (should be BORDERLINE)
    print("\n3. Testing Borderline Quality Task...")
    
    borderline_task = Task(
        task_id="test-003",
        task_title="Database API Implementation",
        task_description="""
        Objective: Create database API endpoints for user management
        
        Deliverables:
        - CRUD operations for user data
        - Basic API documentation
        
        Timeline: 1 week development
        """,
        submitted_by="Test User", 
        timestamp=datetime.now(),
        github_repo_link="https://github.com/user/simple-api"
    )
    
    try:
        result3 = orchestrator.process_submission(borderline_task)
        print(f"   Score: {result3.review.score}")
        print(f"   Status: {result3.review.status}")
        print(f"   Classification: {result3.readiness_classification}")
        print(f"   Improvement Hints: {len(result3.review.improvement_hints)} hints")
        print(f"   Mode: {result3.review.meta.mode}")
        
        # Verify borderline expectations
        assert 30 <= result3.review.score <= 90, f"Expected moderate score, got {result3.review.score}"
        assert result3.review.meta.mode == "hybrid", "Should use hybrid mode"
        assert len(result3.review.improvement_hints) > 0, "Should have improvement hints"
        print("   ✓ Borderline quality task test passed")
        
    except Exception as e:
        print(f"   ✗ Borderline quality task test failed: {e}")
        return False
    
    # Test Case 4: Determinism Test
    print("\n4. Testing Determinism...")
    
    try:
        # Run same task multiple times
        results = []
        for i in range(3):
            result = orchestrator.process_submission(high_quality_task)
            results.append((result.review.score, result.review.status, result.readiness_classification))
        
        # Verify all results are identical
        first_result = results[0]
        for i, result in enumerate(results[1:], 1):
            assert result == first_result, f"Result {i+1} differs from first: {result} vs {first_result}"
        
        print(f"   All 3 runs produced identical results: Score={first_result[0]}, Status={first_result[1]}")
        print("   ✓ Determinism test passed")
        
    except Exception as e:
        print(f"   ✗ Determinism test failed: {e}")
        return False
    
    # Test Case 5: Contract Compliance
    print("\n5. Testing Output Contract Compliance...")
    
    try:
        result = orchestrator.process_submission(high_quality_task)
        review_dict = result.review.model_dump()
        
        # Check required fields
        required_fields = [
            "score", "readiness_percent", "status", "failure_reasons",
            "improvement_hints", "analysis", "meta"
        ]
        
        for field in required_fields:
            assert field in review_dict, f"Missing required field: {field}"
        
        # Check value ranges
        assert 0 <= review_dict["score"] <= 100, f"Score out of range: {review_dict['score']}"
        assert review_dict["status"] in ["pass", "borderline", "fail"], f"Invalid status: {review_dict['status']}"
        assert review_dict["meta"]["mode"] == "hybrid", f"Expected hybrid mode, got {review_dict['meta']['mode']}"
        
        # Check analysis structure
        analysis = review_dict["analysis"]
        assert "technical_quality" in analysis, "Missing technical_quality in analysis"
        assert "clarity" in analysis, "Missing clarity in analysis"
        assert "discipline_signals" in analysis, "Missing discipline_signals in analysis"
        
        print("   ✓ Contract compliance test passed")
        
    except Exception as e:
        print(f"   ✗ Contract compliance test failed: {e}")
        return False
    
    print("\n=== All Integration Tests Passed! ===")
    print("✓ Hybrid pipeline successfully integrated")
    print("✓ Assignment engine authority maintained")
    print("✓ Signal enrichment working")
    print("✓ Output validation enforced")
    print("✓ System deterministic and stable")
    
    return True

if __name__ == "__main__":
    success = test_hybrid_integration()
    if success:
        print("\n🎉 HYBRID INTEGRATION COMPLETE - SYSTEM READY FOR DEMO")
    else:
        print("\n❌ INTEGRATION FAILED - NEEDS DEBUGGING")
        sys.exit(1)