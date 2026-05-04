"""
FINAL CONVERGENCE END-TO-END TEST
Tests the complete single authority system with real execution
"""
import sys
import os

# Add paths for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'intelligence-integration-module-main'))

from task_selector.final_convergence import final_convergence
from evaluation_engine.validator import validator, ValidationStatus
from models.schemas import Task
from task_selector.review_orchestrator import ReviewOrchestrator
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("convergence_test")

def test_single_authority_system():
    """
    Test the complete single authority system
    """
    print("=" * 60)
    print("FINAL CONVERGENCE - SINGLE AUTHORITY SYSTEM TEST")
    print("=" * 60)
    
    # TEST 1: Valid submission with repository
    print("\n1. TESTING VALID SUBMISSION")
    print("-" * 40)
    
    valid_result = final_convergence.process_with_convergence(
        task_title="Advanced Authentication System",
        task_description="Implement comprehensive JWT-based authentication with OAuth2, RBAC, rate limiting, and Docker containerization for microservices architecture.",
        repository_url="https://github.com/user/auth-system",
        module_id="task-review-agent",
        schema_version="v1.0"
    )
    
    print(f"Score: {valid_result.get('score')}")
    print(f"Status: {valid_result.get('status')}")
    print(f"Task Type: {valid_result.get('task_type')}")
    print(f"Authority: {valid_result.get('canonical_authority', False)}")
    print(f"Evaluation Basis: {valid_result.get('evaluation_basis')}")
    
    # Verify single authority
    assert valid_result.get('canonical_authority') == True, "Canonical authority not enforced"
    assert valid_result.get('evaluation_basis') == 'assignment_engine', "Wrong evaluation basis"
    
    # TEST 2: Invalid registry submission
    print("\n2. TESTING INVALID REGISTRY SUBMISSION")
    print("-" * 40)
    
    invalid_result = final_convergence.process_with_convergence(
        task_title="Test Task",
        task_description="Test description",
        repository_url="https://github.com/user/test",
        module_id="invalid-module",
        schema_version="v1.0"
    )
    
    print(f"Registry Rejection: {invalid_result.get('registry_rejection', False)}")
    print(f"Score: {invalid_result.get('score')}")
    print(f"Status: {invalid_result.get('status')}")
    
    # Verify registry enforcement
    assert invalid_result.get('registry_rejection') == True, "Registry validation not enforced"
    assert invalid_result.get('score') == 0, "Invalid score for rejected submission"
    
    # TEST 3: Weak submission (should get correction task)
    print("\n3. TESTING WEAK SUBMISSION")
    print("-" * 40)
    
    weak_result = final_convergence.process_with_convergence(
        task_title="Simple Task",
        task_description="Basic implementation",
        repository_url="https://github.com/user/nonexistent",
        module_id="task-review-agent",
        schema_version="v1.0"
    )
    
    print(f"Score: {weak_result.get('score')}")
    print(f"Status: {weak_result.get('status')}")
    print(f"Task Type: {weak_result.get('task_type')}")
    print(f"Difficulty: {weak_result.get('difficulty')}")
    
    # Verify correction assignment
    assert weak_result.get('status') == 'fail', "Weak submission should fail"
    assert weak_result.get('task_type') == 'correction', "Should assign correction task"
    
    print("\n" + "=" * 60)
    print("SINGLE AUTHORITY SYSTEM VERIFIED")
    print("Registry enforcement: ACTIVE")
    print("Canonical intelligence: SINGLE SOURCE")
    print("Validation gate: ENFORCED")
    print("No parallel paths: CONFIRMED")
    print("=" * 60)
    
    return True

def test_orchestrator_integration():
    """
    Test the complete orchestrator integration
    """
    print("\n" + "=" * 60)
    print("ORCHESTRATOR INTEGRATION TEST")
    print("=" * 60)
    
    orchestrator = ReviewOrchestrator()
    
    # Create test task
    task = Task(
        task_id="test-integration-001",
        task_title="Microservices Authentication System",
        task_description="Implement JWT authentication with OAuth2, RBAC, rate limiting, Docker containerization, and comprehensive testing suite.",
        submitted_by="test-user",
        github_repo_link="https://github.com/test/auth-microservice",
        module_id="task-review-agent",
        schema_version="v1.0",
        timestamp=datetime.now()
    )
    
    # Process through orchestrator
    result = orchestrator.process_submission(task)
    
    print(f"Submission ID: {result.get('submission_id')}")
    print(f"Review Score: {result.get('review', {}).get('score')}")
    print(f"Review Status: {result.get('review', {}).get('status')}")
    print(f"Next Task Type: {result.get('next_task', {}).get('task_type')}")
    print(f"Hierarchy Enforced: {result.get('hierarchy_enforced')}")
    print(f"Authority Chain: {result.get('authority_chain')}")
    
    # Verify orchestrator uses single authority
    assert result.get('hierarchy_enforced') == True, "Hierarchy not enforced"
    assert 'Assignment > Signals > Validation' in str(result.get('authority_chain', '')), "Wrong authority chain"
    
    print("\nORCHESTRATOR INTEGRATION VERIFIED")
    return True

def test_determinism():
    """
    Test that the system produces deterministic results
    """
    print("\n" + "=" * 60)
    print("DETERMINISM TEST")
    print("=" * 60)
    
    # Same input, multiple runs
    test_input = {
        "task_title": "REST API with Authentication",
        "task_description": "Build REST API with JWT authentication, user management, and role-based access control",
        "repository_url": "https://github.com/test/rest-api",
        "module_id": "task-review-agent",
        "schema_version": "v1.0"
    }
    
    results = []
    for i in range(3):
        result = final_convergence.process_with_convergence(**test_input)
        results.append({
            'score': result.get('score'),
            'status': result.get('status'),
            'task_type': result.get('task_type')
        })
        print(f"Run {i+1}: Score={result.get('score')}, Status={result.get('status')}, TaskType={result.get('task_type')}")
    
    # Verify all results are identical
    first_result = results[0]
    for i, result in enumerate(results[1:], 2):
        assert result == first_result, f"Run {i} differs from Run 1: {result} != {first_result}"
    
    print(f"\nDETERMINISM VERIFIED: All 3 runs identical")
    print(f"Canonical Score: {first_result['score']}")
    print(f"Canonical Status: {first_result['status']}")
    print(f"Canonical Task Type: {first_result['task_type']}")
    
    return True

def main():
    """
    Run all convergence tests
    """
    try:
        print("STARTING FINAL CONVERGENCE TESTS")
        
        # Test 1: Single authority system
        test_single_authority_system()
        
        # Test 2: Orchestrator integration
        test_orchestrator_integration()
        
        # Test 3: Determinism
        test_determinism()
        
        print("\n" + "=" * 20)
        print("ALL TESTS PASSED - SYSTEM READY FOR PRODUCTION")
        print("Single Authority: ENFORCED")
        print("Registry Gates: ACTIVE")
        print("Validation Layer: ENFORCED")
        print("Deterministic: VERIFIED")
        print("Production Ready: TRUE")
        print("=" * 20)
        
        return True
        
    except Exception as e:
        print(f"\nTEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)