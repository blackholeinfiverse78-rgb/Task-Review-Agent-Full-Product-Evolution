"""
Registry Validation Tests
Tests for structural discipline enforcement via Blueprint Registry
"""
import pytest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from evaluation_engine.validator import (
    Validator, 
    ValidationStatus, 
    ValidationResult,
    LifecycleStage
)

class TestValidator:
    def setup_method(self):
        self.validator = Validator()
    
    def test_validate_module_id_valid(self):
        """Test validation of existing module ID"""
        result = self.validator.validate_module_id("task-review-agent")
        
        assert result.status == ValidationStatus.VALID
        assert result.reason is None
        assert result.module_info is not None
        assert result.module_info["module_id"] == "task-review-agent"
    
    def test_validate_module_id_invalid(self):
        """Test validation of non-existent module ID"""
        result = self.validator.validate_module_id("non-existent-module")
        
        assert result.status == ValidationStatus.INVALID
        assert "not found in Blueprint Registry" in result.reason
        assert result.module_info is None
    
    def test_validate_module_id_empty(self):
        """Test validation of empty module ID"""
        result = self.validator.validate_module_id("")
        
        assert result.status == ValidationStatus.INVALID
        assert "cannot be empty" in result.reason
    
    def test_validate_lifecycle_stage_active(self):
        """Test lifecycle validation for active production module"""
        result = self.validator.validate_lifecycle_stage("task-review-agent")
        
        assert result.status == ValidationStatus.VALID
        assert result.module_info["lifecycle_stage"] == LifecycleStage.PRODUCTION
    
    def test_validate_lifecycle_stage_deprecated(self):
        """Test lifecycle validation for deprecated module"""
        result = self.validator.validate_lifecycle_stage("legacy-module")
        
        assert result.status == ValidationStatus.INVALID
        assert "deprecated" in result.reason
        assert "cannot accept new work" in result.reason
    
    def test_validate_lifecycle_stage_development(self):
        """Test lifecycle validation for development module"""
        result = self.validator.validate_lifecycle_stage("dev-module")
        
        assert result.status == ValidationStatus.VALID
        assert result.module_info["lifecycle_stage"] == LifecycleStage.DEVELOPMENT
    
    def test_validate_schema_version_match(self):
        """Test schema version validation with matching version"""
        result = self.validator.validate_schema_version("task-review-agent", "v1.0")
        
        assert result.status == ValidationStatus.VALID
        assert result.module_info["schema_version"] == "v1.0"
    
    def test_validate_schema_version_mismatch(self):
        """Test schema version validation with mismatched version"""
        result = self.validator.validate_schema_version("evaluation-engine", "v1.0")
        
        assert result.status == ValidationStatus.INVALID
        assert "Schema version mismatch" in result.reason
        assert "has v3.0, required v1.0" in result.reason
    
    def test_validate_complete_success(self):
        """Test complete validation for valid module"""
        result = self.validator.validate_complete("task-review-agent", "v1.0")
        
        assert result.status == ValidationStatus.VALID
        assert result.module_info is not None
    
    def test_validate_complete_invalid_module(self):
        """Test complete validation for invalid module"""
        result = self.validator.validate_complete("invalid-module", "v1.0")
        
        assert result.status == ValidationStatus.INVALID
        assert "not found in Blueprint Registry" in result.reason
    
    def test_validate_complete_deprecated_module(self):
        """Test complete validation for deprecated module"""
        result = self.validator.validate_complete("legacy-module", "v0.9")
        
        assert result.status == ValidationStatus.INVALID
        assert "deprecated" in result.reason
    
    def test_validate_complete_schema_mismatch(self):
        """Test complete validation with schema version mismatch"""
        result = self.validator.validate_complete("evaluation-engine", "v1.0")
        
        assert result.status == ValidationStatus.INVALID
        assert "Schema version mismatch" in result.reason
    
    def test_get_module_info_exists(self):
        """Test getting module info for existing module"""
        info = self.validator.get_module_info("task-review-agent")
        
        assert info is not None
        assert info["module_id"] == "task-review-agent"
        assert info["status"] == "active"
    
    def test_get_module_info_not_exists(self):
        """Test getting module info for non-existent module"""
        info = self.validator.get_module_info("non-existent")
        
        assert info is None
    
    def test_list_active_modules(self):
        """Test listing all active modules"""
        active_modules = self.validator.list_active_modules()
        
        assert len(active_modules) >= 3  # At least 3 active modules in mock data
        assert "task-review-agent" in active_modules
        assert "evaluation-engine" in active_modules
        assert "legacy-module" not in active_modules  # Deprecated, not active
    
    def test_is_operation_allowed_valid(self):
        """Test operation permission for valid operation"""
        allowed = self.validator.is_operation_allowed("task-review-agent", "submit")
        
        assert allowed is True
    
    def test_is_operation_allowed_invalid(self):
        """Test operation permission for invalid operation"""
        allowed = self.validator.is_operation_allowed("task-review-agent", "delete")
        
        assert allowed is False
    
    def test_is_operation_allowed_nonexistent_module(self):
        """Test operation permission for non-existent module"""
        allowed = self.validator.is_operation_allowed("non-existent", "submit")
        
        assert allowed is False
    
    def test_deterministic_validation(self):
        """Test that validation results are deterministic"""
        results = []
        for _ in range(5):
            result = self.validator.validate_complete("task-review-agent", "v1.0")
            results.append((result.status, result.reason))
        
        # All results should be identical
        first_result = results[0]
        for result in results[1:]:
            assert result == first_result
    
    def test_validation_logging(self, caplog):
        """Test that validation operations are properly logged"""
        self.validator.validate_complete("task-review-agent", "v1.0")
        
        assert "Validating module_id: task-review-agent" in caplog.text
        assert "Performing complete validation" in caplog.text
        assert "Complete validation passed" in caplog.text

class TestValidationResult:
    def test_validation_result_creation(self):
        """Test ValidationResult dataclass creation"""
        result = ValidationResult(
            status=ValidationStatus.VALID,
            reason=None,
            module_info={"test": "data"}
        )
        
        assert result.status == ValidationStatus.VALID
        assert result.reason is None
        assert result.module_info == {"test": "data"}
    
    def test_validation_result_invalid(self):
        """Test ValidationResult for invalid case"""
        result = ValidationResult(
            status=ValidationStatus.INVALID,
            reason="Test failure reason"
        )
        
        assert result.status == ValidationStatus.INVALID
        assert result.reason == "Test failure reason"
        assert result.module_info is None

if __name__ == "__main__":
    pytest.main([__file__, "-v"])