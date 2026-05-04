"""
FINAL CONVERGENCE Verification Script
Tests the complete Assignment Authority > Signal Support > Validation Gate hierarchy
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from task_selector.final_convergence import final_convergence
from app.services.assignment_authority import assignment_authority
from evaluation_engine.shraddha_validation import validation_gate
import json

def test_final_convergence():
    """Test complete FINAL CONVERGENCE flow"""
    print("=" * 60)
    print("FINAL CONVERGENCE VERIFICATION")
    print("=" * 60)
    
    # Test Case 1: High Quality Task (should get advancement)
    print("\n1. TESTING HIGH QUALITY TASK")
    print("-" * 40)
    
    result1 = final_convergence.process_with_convergence(
        task_title="Advanced Microservices Authentication System",
        task_description="Implement comprehensive JWT-based authentication with role-based access control, OAuth2 integration, password hashing with bcrypt, session management, rate limiting, and comprehensive API documentation. Include Docker containerization and CI/CD pipeline setup.",
        repository_url="https://github.com/user/advanced-auth-system",
        module_id="core-development",
        schema_version="v1.0"
    )
    
    print(f"Score: {result1.get('score')}")
    print(f"Status: {result1.get('status')}")
    print(f"Task Type: {result1.get('task_type')}")
    print(f"Authority Override: {result1.get('authority_override')}")
    print(f"Evaluation Basis: {result1.get('evaluation_basis')}")
    
    # Test Case 2: Medium Quality Task (should get reinforcement)
    print("\n2. TESTING MEDIUM QUALITY TASK")
    print("-" * 40)
    
    result2 = final_convergence.process_with_convergence(
        task_title="Basic API Authentication",
        task_description="Create simple JWT authentication for REST API with basic user login and logout functionality.",
        repository_url="https://github.com/user/basic-auth",
        module_id="core-development",
        schema_version="v1.0"
    )
    
    print(f"Score: {result2.get('score')}")
    print(f"Status: {result2.get('status')}")
    print(f"Task Type: {result2.get('task_type')}")
    print(f"Authority Override: {result2.get('authority_override')}")
    
    # Test Case 3: Low Quality Task (should get correction)
    print("\n3. TESTING LOW QUALITY TASK")
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
    
    # Test Case 4: Registry Validation Failure
    print("\n4. TESTING REGISTRY VALIDATION FAILURE")
    print("-" * 40)
    
    result4 = final_convergence.process_with_convergence(
        task_title="Test Task",
        task_description="Test description",
        repository_url="https://github.com/user/test-repo",
        module_id="invalid-module",
        schema_version="v1.0"
    )
    
    print(f"Score: {result4.get('score')}")
    print(f"Status: {result4.get('status')}")
    print(f"Registry Rejection: {result4.get('registry_rejection')}")
    
    return result1, result2, result3, result4

def test_assignment_authority():
    """Test Assignment Authority directly"""
    print("\n" + "=" * 60)
    print("ASSIGNMENT AUTHORITY VERIFICATION")
    print("=" * 60)
    
    # Test evidence-driven evaluation
    expected_vs_delivered = {
        "expected_count": 10,
        "delivered_count": 3,
        "delivery_ratio": 0.3
    }
    
    missing_features = [
        "OAuth2 integration",
        "Rate limiting",
        "API documentation",
        "Docker containerization"
    ]
    
    failure_reasons = [
        "Repository not found",
        "Missing implementation files"
    ]
    
    authority_result = assignment_authority.evaluate_assignment_readiness(
        task_title="Test Assignment",
        task_description="Test description",
        expected_vs_delivered=expected_vs_delivered,
        missing_features=missing_features,
        failure_reasons=failure_reasons
    )
    
    print(f"Assignment Score: {authority_result['assignment_score']}")
    print(f"Assignment Status: {authority_result['assignment_status']}")
    print(f"Next Assignment Type: {authority_result['next_assignment']['assignment_type']}")
    print(f"Focus Area: {authority_result['next_assignment']['focus_area']}")
    print(f"Authority Level: {authority_result['authority_level']}")
    
    return authority_result

def test_validation_gate():
    """Test Shraddha's Validation Gate"""
    print("\n" + "=" * 60)
    print("VALIDATION GATE VERIFICATION")
    print("=" * 60)
    
    # Test with invalid data that needs correction
    invalid_result = {
        "submission_id": "test-123",
        "score": 150,  # Invalid - over 100
        "status": "invalid_status",  # Invalid enum
        "readiness_percent": -10,  # Invalid - negative
        "next_task_id": "next-123",
        "task_type": "invalid_type",  # Invalid enum
        "title": "Test Task",
        "difficulty": "invalid_difficulty"  # Invalid enum
    }
    
    validated_result = validation_gate.validate_final_output(
        invalid_result, 
        source="test_validation"
    )
    
    print(f"Original Score: {invalid_result['score']} -> Corrected: {validated_result.get('score')}")
    print(f"Original Status: {invalid_result['status']} -> Corrected: {validated_result.get('status')}")
    print(f"Original Task Type: {invalid_result['task_type']} -> Corrected: {validated_result.get('task_type')}")
    print(f"Validation Metadata: {validated_result.get('validation_metadata', {}).get('validated_by')}")
    
    return validated_result

def test_hierarchy_enforcement():
    """Test that Assignment Authority overrides Signal Evaluation"""
    print("\n" + "=" * 60)
    print("HIERARCHY ENFORCEMENT VERIFICATION")
    print("=" * 60)
    
    # Simulate signal result with high score
    signal_result = {
        "score": 85,
        "status": "pass",
        "title": "High Signal Score Task",
        "description": "Task with high signal score",
        "missing_features": ["critical_feature_1", "critical_feature_2"],
        "failure_reasons": ["Repository not found", "Missing implementation"]
    }
    
    # Assignment Authority should override based on evidence
    overridden_result = assignment_authority.override_signal_evaluation(signal_result)
    
    print(f"Original Signal Score: {signal_result['score']}")
    print(f"Assignment Authority Score: {overridden_result['score']}")
    print(f"Authority Override Applied: {overridden_result.get('authority_override')}")
    print(f"Evaluation Basis: {overridden_result.get('evaluation_basis')}")
    print(f"Authority Correction: {overridden_result.get('authority_correction')}")
    
    return overridden_result

def verify_convergence_requirements():
    """Verify all FINAL CONVERGENCE requirements are met"""
    print("\n" + "=" * 60)
    print("CONVERGENCE REQUIREMENTS VERIFICATION")
    print("=" * 60)
    
    requirements = {
        "Assignment Authority as Canonical": False,
        "Signal Evaluation as Supporting": False,
        "Validation Layer as Final Gate": False,
        "Evidence-driven Intelligence": False,
        "Registry Enforcement": False,
        "No Parallel Logic Paths": False
    }
    
    # Test each requirement
    try:
        # 1. Assignment Authority as Canonical
        auth_result = assignment_authority.evaluate_assignment_readiness(
            "Test", "Test", {}, [], []
        )
        if auth_result.get("authority_level") == "CANONICAL":
            requirements["Assignment Authority as Canonical"] = True
        
        # 2. Signal Evaluation as Supporting
        conv_result = final_convergence.process_with_convergence(
            "Test", "Test", None, "core-development", "v1.0"
        )
        if conv_result.get("supporting_signals"):
            requirements["Signal Evaluation as Supporting"] = True
        
        # 3. Validation Layer as Final Gate
        val_result = validation_gate.validate_final_output({"score": 50}, "test")
        if val_result.get("validation_metadata", {}).get("validation_level") == "FINAL_AUTHORITATIVE":
            requirements["Validation Layer as Final Gate"] = True
        
        # 4. Evidence-driven Intelligence
        if conv_result.get("expected_vs_delivered") and conv_result.get("missing_features"):
            requirements["Evidence-driven Intelligence"] = True
        
        # 5. Registry Enforcement
        if conv_result.get("convergence_metadata", {}).get("hierarchy_enforced"):
            requirements["Registry Enforcement"] = True
        
        # 6. No Parallel Logic Paths
        if conv_result.get("evaluation_basis") == "assignment_authority":
            requirements["No Parallel Logic Paths"] = True
            
    except Exception as e:
        print(f"Verification error: {e}")
    
    # Print results
    print("\nREQUIREMENT STATUS:")
    for req, status in requirements.items():
        status_symbol = "✅" if status else "❌"
        print(f"{status_symbol} {req}")
    
    all_passed = all(requirements.values())
    print(f"\nOVERALL STATUS: {'✅ ALL REQUIREMENTS MET' if all_passed else '❌ REQUIREMENTS MISSING'}")
    
    return requirements

if __name__ == "__main__":
    print("FINAL CONVERGENCE SYSTEM VERIFICATION")
    print("Testing Assignment Authority > Signal Support > Validation Gate")
    
    try:
        # Run all tests
        conv_results = test_final_convergence()
        auth_result = test_assignment_authority()
        val_result = test_validation_gate()
        hierarchy_result = test_hierarchy_enforcement()
        requirements = verify_convergence_requirements()
        
        print("\n" + "=" * 60)
        print("VERIFICATION COMPLETE")
        print("=" * 60)
        
        # Summary
        all_requirements_met = all(requirements.values())
        if all_requirements_met:
            print("🎉 FINAL CONVERGENCE SUCCESSFULLY IMPLEMENTED")
            print("✅ Assignment Authority is CANONICAL")
            print("✅ Signal Evaluation is SUPPORTING ONLY")
            print("✅ Validation Layer is FINAL GATE")
            print("✅ Evidence-driven Intelligence")
            print("✅ Registry Enforcement")
            print("✅ Single Unified Flow")
        else:
            print("⚠️  CONVERGENCE IMPLEMENTATION INCOMPLETE")
            missing = [req for req, status in requirements.items() if not status]
            for req in missing:
                print(f"❌ Missing: {req}")
        
    except Exception as e:
        print(f"VERIFICATION FAILED: {e}")
        import traceback
        traceback.print_exc()