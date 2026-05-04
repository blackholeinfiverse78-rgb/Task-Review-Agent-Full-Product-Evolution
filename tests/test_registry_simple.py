"""
Simple Registry Validation Test
Quick verification that registry validation is working
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from evaluation_engine.validator import validator, ValidationStatus

def test_registry_validation():
    print("=" * 60)
    print("REGISTRY VALIDATION VERIFICATION")
    print("=" * 60)
    
    # Test 1: Valid module
    print("\n[TEST 1] Valid Module Validation")
    result = validator.validate_complete("task-review-agent", "v1.0")
    print(f"Status: {result.status}")
    print(f"Module: {result.module_info['module_id'] if result.module_info else 'None'}")
    assert result.status == ValidationStatus.VALID
    print("✓ PASS")
    
    # Test 2: Invalid module
    print("\n[TEST 2] Invalid Module Rejection")
    result = validator.validate_complete("invalid-module", "v1.0")
    print(f"Status: {result.status}")
    print(f"Reason: {result.reason}")
    assert result.status == ValidationStatus.INVALID
    assert "not found in Blueprint Registry" in result.reason
    print("✓ PASS")
    
    # Test 3: Deprecated module
    print("\n[TEST 3] Deprecated Module Rejection")
    result = validator.validate_complete("legacy-module", "v0.9")
    print(f"Status: {result.status}")
    print(f"Reason: {result.reason}")
    assert result.status == ValidationStatus.INVALID
    assert "deprecated" in result.reason
    print("✓ PASS")
    
    # Test 4: Schema mismatch
    print("\n[TEST 4] Schema Version Mismatch")
    result = validator.validate_complete("evaluation-engine", "v1.0")
    print(f"Status: {result.status}")
    print(f"Reason: {result.reason}")
    assert result.status == ValidationStatus.INVALID
    assert "Schema version mismatch" in result.reason
    print("✓ PASS")
    
    print("\n" + "=" * 60)
    print("REGISTRY VALIDATION: ALL TESTS PASSED")
    print("✓ Module ID validation working")
    print("✓ Lifecycle stage validation working")
    print("✓ Schema version validation working")
    print("✓ Structural discipline enforcement active")
    print("=" * 60)

if __name__ == "__main__":
    test_registry_validation()