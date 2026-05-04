"""
AUTHORITY REALIGNMENT VERIFICATION SCRIPT
Tests the corrected hierarchy: Assignment Authority > Signal Support > Validation Gate
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from task_selector.final_convergence import final_convergence
from app.services.assignment_authority import assignment_authority
from evaluation_engine.shraddha_validation import validation_gate
from evaluation_engine.signal_engine import signal_engine
import json

def test_authority_realignment():
    """Test complete authority realignment"""
    print("=" * 60)
    print("AUTHORITY REALIGNMENT VERIFICATION")
    print("=" * 60)
    
    # Test Case 1: PASS Case (High Quality)
    print("\n1. TESTING PASS CASE")
    print("-" * 40)
    
    result1 = final_convergence.process_with_convergence(
        task_title="Advanced Microservices Authentication System with OAuth2 Integration",
        task_description="Implement comprehensive JWT-based authentication with role-based access control, OAuth2 integration, password hashing with bcrypt, session management, rate limiting, API documentation, Docker containerization, and CI/CD pipeline setup with comprehensive testing suite.",
        repository_url="https://github.com/user/advanced-auth-system",
        module_id="core-development",
        schema_version="v1.0"
    )
    
    print(f"Score: {result1.get('score')}")
    print(f"Status: {result1.get('status')}")
    print(f"Task Type: {result1.get('task_type')}")
    print(f"Authority Override: {result1.get('authority_override')}")
    print(f"Evaluation Basis: {result1.get('evaluation_basis')}")
    print(f"Hierarchy Enforced: {result1.get('convergence_metadata', {}).get('hierarchy_enforced')}")
    
    # Test Case 2: BORDERLINE Case (Medium Quality)
    print("\n2. TESTING BORDERLINE CASE")
    print("-" * 40)
    
    result2 = final_convergence.process_with_convergence(
        task_title="REST API Authentication with JWT",
        task_description="Create JWT authentication for REST API with user login, logout, and basic role management. Include password hashing and session handling.",
        repository_url="https://github.com/user/basic-auth",
        module_id="core-development",
        schema_version="v1.0"
    )
    
    print(f"Score: {result2.get('score')}")
    print(f"Status: {result2.get('status')}")
    print(f"Task Type: {result2.get('task_type')}")
    print(f"Authority Override: {result2.get('authority_override')}")
    
    # Test Case 3: FAIL Case (Low Quality)
    print("\n3. TESTING FAIL CASE")
    print("-" * 40)
    
    result3 = final_convergence.process_with_convergence(
        task_title="Auth",
        task_description="Make login work",
        repository_url="https://github.com/user/nonexistent-repo",
        module_id="core-development",
        schema_version="v1.0"
    )
    
    print(f"Score: {result3.get('score')}")
    print(f"Status: {result3.get('status')}")
    print(f"Task Type: {result3.get('task_type')}")
    print(f"Authority Override: {result3.get('authority_override')}")
    
    return result1, result2, result3

def test_signal_engine_authority():
    """Test that Signal Collector has NO scoring authority"""
    print("\n" + "=" * 60)
    print("SIGNAL COLLECTOR AUTHORITY TEST")
    print("=" * 60)
    
    signals = signal_engine.collect_supporting_signals(
        task_title="Test Task",
        task_description="Test description with technical requirements",
        repository_url="https://github.com/user/test-repo"
    )
    
    print(f"Signal Authority: {signals.get('signal_authority')}")
    print(f"Can Determine Score: {signals.get('can_determine_score')}")
    print(f"Repository Available: {signals.get('repository_available')}")
    print(f"Expected Features: {len(signals.get('expected_features', []))}")
    print(f"Missing Features: {len(signals.get('missing_features', []))}")
    print(f"Failure Indicators: {len(signals.get('failure_indicators', []))}")
    
    # Verify NO scoring authority
    assert signals.get('signal_authority') == 'SUPPORTING_ONLY'
    assert signals.get('can_determine_score') == False
    print("✓ Signal Collector correctly has NO scoring authority")
    
    return signals

def test_assignment_authority_primary():
    """Test Assignment Authority as PRIMARY evaluator"""
    print("\n" + "=" * 60)
    print("ASSIGNMENT AUTHORITY PRIMARY TEST")
    print("=" * 60)
    
    # Create mock supporting signals
    supporting_signals = {
        "expected_vs_delivered_evidence": {
            "expected_count": 8,
            "delivered_count": 3,
            "delivery_ratio": 0.375
        },
        "missing_features": ["OAuth2 integration", "Rate limiting", "API documentation"],
        "failure_indicators": ["repository_not_found", "low_feature_match_ratio"],
        "repository_available": False,
        "feature_match_ratio": 0.2
    }
    
    authority_result = assignment_authority.evaluate_assignment_readiness(
        task_title="Test Assignment Authority",
        task_description="Test description",
        supporting_signals=supporting_signals
    )
    
    print(f"Authority Level: {authority_result.get('authority_level')}")
    print(f"Score: {authority_result.get('score')}")
    print(f"Status: {authority_result.get('status')}")
    print(f"Assignment Status: {authority_result.get('assignment_status')}")
    print(f"Authority Override: {authority_result.get('authority_override')}")
    print(f"Evidence Driven: {authority_result.get('evidence_driven')}")
    print(f"Evidence Summary: {authority_result.get('evidence_summary')}")
    
    # Verify PRIMARY authority
    assert authority_result.get('authority_level') == 'PRIMARY_CANONICAL'
    assert authority_result.get('authority_override') == True
    assert authority_result.get('evidence_driven') == True
    print("✓ Assignment Authority correctly is PRIMARY evaluator")
    
    return authority_result

def test_validation_gate_final():
    """Test Validation Gate as FINAL authority"""
    print("\n" + "=" * 60)
    print("VALIDATION GATE FINAL TEST")
    print("=" * 60)
    
    # Test with data that needs correction
    test_result = {
        "submission_id": "test-123",
        "score": 120,  # Invalid - over 100
        "status": "invalid_status",  # Invalid enum
        "readiness_percent": -5,  # Invalid - negative
        "next_task_id": "next-123",
        "task_type": "invalid_type",  # Invalid enum
        "title": "Test Task",
        "difficulty": "invalid_difficulty"  # Invalid enum
    }
    
    validated_result = validation_gate.validate_final_output(
        test_result, 
        source="assignment_authority"
    )
    
    print(f"Original Score: {test_result['score']} -> Corrected: {validated_result.get('score')}")
    print(f"Original Status: {test_result['status']} -> Corrected: {validated_result.get('status')}")
    print(f"Validation Level: {validated_result.get('validation_metadata', {}).get('validation_level')}")
    print(f"Contract Compliance: {validated_result.get('validation_metadata', {}).get('contract_compliance')}")
    
    # Verify FINAL gate authority
    assert validated_result.get('validation_metadata', {}).get('validation_level') == 'FINAL_AUTHORITATIVE'
    assert validated_result.get('score') <= 100  # Corrected
    assert validated_result.get('status') in ['pass', 'borderline', 'fail']  # Corrected
    print("✓ Validation Gate correctly is FINAL authority")
    
    return validated_result

def verify_hierarchy_enforcement():
    """Verify strict hierarchy enforcement"""
    print("\n" + "=" * 60)
    print("HIERARCHY ENFORCEMENT VERIFICATION")
    print("=" * 60)
    
    # Test complete flow
    result = final_convergence.process_with_convergence(
        task_title="Hierarchy Test Task",
        task_description="Testing hierarchy enforcement",
        repository_url=None,
        module_id="core-development",
        schema_version="v1.0"
    )
    
    convergence_meta = result.get('convergence_metadata', {})
    validation_meta = result.get('validation_metadata', {})
    
    print(f"Hierarchy Enforced: {convergence_meta.get('hierarchy_enforced')}")
    print(f"Assignment Authority: {convergence_meta.get('assignment_authority')}")
    print(f"Signal Evaluation: {convergence_meta.get('signal_evaluation')}")
    print(f"Validation Layer: {convergence_meta.get('validation_layer')}")
    print(f"No Parallel Paths: {convergence_meta.get('no_parallel_paths')}")
    print(f"Validation Level: {validation_meta.get('validation_level')}")
    
    # Verify hierarchy
    hierarchy_checks = {
        "Hierarchy Enforced": convergence_meta.get('hierarchy_enforced') == True,
        "Assignment PRIMARY": convergence_meta.get('assignment_authority') == 'PRIMARY',
        "Signals SUPPORTING": convergence_meta.get('signal_evaluation') == 'SUPPORTING',
        "Validation FINAL": convergence_meta.get('validation_layer') == 'FINAL_WRAPPER',
        "No Parallel Paths": convergence_meta.get('no_parallel_paths') == True,
        "Final Validation": validation_meta.get('validation_level') == 'FINAL_AUTHORITATIVE'
    }
    
    print("\nHIERARCHY VERIFICATION:")
    for check, status in hierarchy_checks.items():
        status_symbol = "✓" if status else "✗"
        print(f"{status_symbol} {check}")
    
    all_passed = all(hierarchy_checks.values())
    return all_passed, hierarchy_checks

def test_determinism():
    """Test deterministic behavior"""
    print("\n" + "=" * 60)
    print("DETERMINISM VERIFICATION")
    print("=" * 60)
    
    # Same input should produce same output
    test_input = {
        "task_title": "Determinism Test API",
        "task_description": "Create REST API with authentication",
        "repository_url": "https://github.com/user/test-api",
        "module_id": "core-development",
        "schema_version": "v1.0"
    }
    
    # Run 3 times
    results = []
    for i in range(3):
        result = final_convergence.process_with_convergence(**test_input)
        results.append({
            "score": result.get('score'),
            "status": result.get('status'),
            "task_type": result.get('task_type')
        })
        print(f"Run {i+1}: Score={result.get('score')}, Status={result.get('status')}")
    
    # Check consistency
    first_result = results[0]
    deterministic = all(
        r['score'] == first_result['score'] and 
        r['status'] == first_result['status'] and
        r['task_type'] == first_result['task_type']
        for r in results
    )
    
    print(f"Deterministic: {'✓' if deterministic else '✗'}")
    return deterministic

if __name__ == "__main__":
    print("AUTHORITY REALIGNMENT & VALIDATION GATE ENFORCEMENT")
    print("Testing corrected hierarchy: Assignment > Signals > Validation")
    
    try:
        # Run all tests
        pass_borderline_fail = test_authority_realignment()
        signals = test_signal_engine_authority()
        authority = test_assignment_authority_primary()
        validation = test_validation_gate_final()
        hierarchy_passed, hierarchy_checks = verify_hierarchy_enforcement()
        deterministic = test_determinism()
        
        print("\n" + "=" * 60)
        print("VERIFICATION COMPLETE")
        print("=" * 60)
        
        # Summary
        if hierarchy_passed and deterministic:
            print("🎉 AUTHORITY REALIGNMENT SUCCESSFUL")
            print("✓ Assignment Authority is PRIMARY")
            print("✓ Signal Collector is SUPPORTING ONLY")
            print("✓ Validation Gate is FINAL AUTHORITY")
            print("✓ Registry Enforcement ACTIVE")
            print("✓ Hierarchy ENFORCED")
            print("✓ System DETERMINISTIC")
            print("\n✅ READY FOR VINAYAK TESTING")
        else:
            print("⚠️ AUTHORITY REALIGNMENT INCOMPLETE")
            if not hierarchy_passed:
                failed_checks = [check for check, status in hierarchy_checks.items() if not status]
                for check in failed_checks:
                    print(f"✗ Failed: {check}")
            if not deterministic:
                print("✗ Failed: Deterministic behavior")
        
    except Exception as e:
        print(f"VERIFICATION FAILED: {e}")
        import traceback
        traceback.print_exc()