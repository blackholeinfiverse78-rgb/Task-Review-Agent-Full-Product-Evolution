"""
Registry Validator Service
Validates task submissions against Blueprint Registry before evaluation
"""
from typing import Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass
import logging

logger = logging.getLogger("validator")

class ValidationStatus(str, Enum):
    VALID = "VALID"
    INVALID = "INVALID"

class LifecycleStage(str, Enum):
    PLANNING = "planning"
    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"
    DEPRECATED = "deprecated"

    @classmethod
    def allows_work(cls, stage: "LifecycleStage") -> bool:
        return stage in (cls.DEVELOPMENT, cls.TESTING, cls.PRODUCTION)

@dataclass
class ValidationResult:
    status: ValidationStatus
    reason: Optional[str] = None
    module_info: Optional[Dict[str, Any]] = None

class Validator:
    """
    Registry-aware validation service for structural discipline enforcement
    Validates module_id, lifecycle_stage, and schema_version against Blueprint Registry
    """
    
    def __init__(self):
        # Mock Blueprint Registry - In production, this would connect to Sri Satya's Registry Service
        self._blueprint_registry = {
            "task-review-agent": {
                "module_id": "task-review-agent",
                "lifecycle_stage": LifecycleStage.PRODUCTION,
                "schema_version": "v1.0",
                "status": "active",
                "allowed_operations": ["submit", "review", "assign"],
                "created_at": "2026-02-01",
                "updated_at": "2026-02-05"
            },
            "core-development": {
                "module_id": "core-development",
                "lifecycle_stage": LifecycleStage.PRODUCTION,
                "schema_version": "v1.0",
                "status": "active",
                "allowed_operations": ["submit", "review", "assign"],
                "created_at": "2026-02-01",
                "updated_at": "2026-02-05"
            },
            "advanced-features": {
                "module_id": "advanced-features",
                "lifecycle_stage": LifecycleStage.PRODUCTION,
                "schema_version": "v1.0",
                "status": "active",
                "allowed_operations": ["submit", "review", "assign"],
                "created_at": "2026-02-01",
                "updated_at": "2026-02-05"
            },
            "system-integration": {
                "module_id": "system-integration",
                "lifecycle_stage": LifecycleStage.PRODUCTION,
                "schema_version": "v1.0",
                "status": "active",
                "allowed_operations": ["submit", "review", "assign"],
                "created_at": "2026-02-01",
                "updated_at": "2026-02-05"
            },
            "performance-optimization": {
                "module_id": "performance-optimization",
                "lifecycle_stage": LifecycleStage.PRODUCTION,
                "schema_version": "v1.0",
                "status": "active",
                "allowed_operations": ["submit", "review", "assign"],
                "created_at": "2026-02-01",
                "updated_at": "2026-02-05"
            },
            "security-implementation": {
                "module_id": "security-implementation",
                "lifecycle_stage": LifecycleStage.PRODUCTION,
                "schema_version": "v1.0",
                "status": "active",
                "allowed_operations": ["submit", "review", "assign"],
                "created_at": "2026-02-01",
                "updated_at": "2026-02-05"
            },
            "evaluation-engine": {
                "module_id": "evaluation-engine", 
                "lifecycle_stage": LifecycleStage.PRODUCTION,
                "schema_version": "v3.0",
                "status": "active",
                "allowed_operations": ["evaluate", "score", "analyze"],
                "created_at": "2026-02-03",
                "updated_at": "2026-02-05"
            },
            "lifecycle-orchestrator": {
                "module_id": "lifecycle-orchestrator",
                "lifecycle_stage": LifecycleStage.PRODUCTION, 
                "schema_version": "v1.1",
                "status": "active",
                "allowed_operations": ["orchestrate", "manage", "track"],
                "created_at": "2026-02-04",
                "updated_at": "2026-02-05"
            },
            "legacy-module": {
                "module_id": "legacy-module",
                "lifecycle_stage": LifecycleStage.DEPRECATED,
                "schema_version": "v0.9",
                "status": "deprecated",
                "allowed_operations": [],
                "created_at": "2026-01-01",
                "updated_at": "2026-01-15"
            },
            "dev-module": {
                "module_id": "dev-module",
                "lifecycle_stage": LifecycleStage.DEVELOPMENT,
                "schema_version": "v2.0-beta",
                "status": "development",
                "allowed_operations": ["test", "validate"],
                "created_at": "2026-02-05",
                "updated_at": "2026-02-05"
            }
        }
    
    def validate_module_id(self, module_id: str) -> ValidationResult:
        """
        Validate that module_id exists in Blueprint Registry
        
        Args:
            module_id: Module identifier to validate
            
        Returns:
            ValidationResult with status and reason
        """
        logger.info(f"Validating module_id: {module_id}")
        
        if not module_id:
            return ValidationResult(
                status=ValidationStatus.INVALID,
                reason="Module ID cannot be empty"
            )
        
        if module_id not in self._blueprint_registry:
            return ValidationResult(
                status=ValidationStatus.INVALID,
                reason=f"Module ID '{module_id}' not found in Blueprint Registry"
            )
        
        module_info = self._blueprint_registry[module_id]
        logger.info(f"Module found: {module_id} (status: {module_info['status']})")
        
        return ValidationResult(
            status=ValidationStatus.VALID,
            module_info=module_info
        )
    
    def validate_lifecycle_stage(self, module_id: str) -> ValidationResult:
        """
        Validate that module lifecycle_stage allows work
        
        Args:
            module_id: Module identifier to check lifecycle stage
            
        Returns:
            ValidationResult with status and reason
        """
        logger.info(f"Validating lifecycle stage for module: {module_id}")
        
        # First validate module exists
        module_validation = self.validate_module_id(module_id)
        if module_validation.status == ValidationStatus.INVALID:
            return module_validation
        
        module_info = module_validation.module_info
        lifecycle_stage = module_info["lifecycle_stage"]
        
        # Check if lifecycle stage allows work
        if lifecycle_stage == LifecycleStage.DEPRECATED:
            return ValidationResult(
                status=ValidationStatus.INVALID,
                reason=f"Module '{module_id}' is deprecated and cannot accept new work"
            )
        
        if not LifecycleStage.allows_work(lifecycle_stage):
            return ValidationResult(
                status=ValidationStatus.INVALID,
                reason=f"Module '{module_id}' is in {lifecycle_stage} stage and not ready for work"
            )
        
        # Development, Testing, and Production stages allow work
        logger.info(f"Lifecycle stage validation passed: {lifecycle_stage}")
        return ValidationResult(
            status=ValidationStatus.VALID,
            module_info=module_info
        )
    
    def validate_schema_version(self, module_id: str, required_version: str = "v1.0") -> ValidationResult:
        """
        Validate that module schema_version matches requirements
        
        Args:
            module_id: Module identifier to check schema version
            required_version: Required schema version (default: v1.0)
            
        Returns:
            ValidationResult with status and reason
        """
        logger.info(f"Validating schema version for module: {module_id} (required: {required_version})")
        
        # First validate module exists
        module_validation = self.validate_module_id(module_id)
        if module_validation.status == ValidationStatus.INVALID:
            return module_validation
        
        module_info = module_validation.module_info
        current_version = module_info["schema_version"]
        
        # Normalise version: accept both "1.0" and "v1.0"
        def _normalise(v: str) -> str:
            return v if v.startswith('v') else f'v{v}'
        
        if _normalise(current_version) != _normalise(required_version):
            return ValidationResult(
                status=ValidationStatus.INVALID,
                reason=f"Schema version mismatch: module '{module_id}' has {current_version}, required {required_version}"
            )
        
        logger.info(f"Schema version validation passed: {current_version}")
        return ValidationResult(
            status=ValidationStatus.VALID,
            module_info=module_info
        )
    
    def validate_complete(self, module_id: str, schema_version: str = "v1.0") -> ValidationResult:
        """
        Perform complete validation: module_id + lifecycle_stage + schema_version
        
        Args:
            module_id: Module identifier to validate
            schema_version: Required schema version
            
        Returns:
            ValidationResult with comprehensive validation status
        """
        logger.info(f"Performing complete validation for module: {module_id}")
        
        # Step 1: Validate module exists
        module_result = self.validate_module_id(module_id)
        if module_result.status == ValidationStatus.INVALID:
            return module_result
        
        # Step 2: Validate lifecycle stage allows work
        lifecycle_result = self.validate_lifecycle_stage(module_id)
        if lifecycle_result.status == ValidationStatus.INVALID:
            return lifecycle_result
        
        # Step 3: Validate schema version matches
        schema_result = self.validate_schema_version(module_id, schema_version)
        if schema_result.status == ValidationStatus.INVALID:
            return schema_result
        
        logger.info(f"Complete validation passed for module: {module_id}")
        return ValidationResult(
            status=ValidationStatus.VALID,
            module_info=module_result.module_info
        )
    
    def get_module_info(self, module_id: str) -> Optional[Dict[str, Any]]:
        """Get module info, returns None if not found."""
        return self._blueprint_registry.get(module_id)
    
    def list_active_modules(self) -> Dict[str, Dict[str, Any]]:
        """
        List all active modules in the registry
        
        Returns:
            Dictionary of active modules
        """
        return {
            module_id: info 
            for module_id, info in self._blueprint_registry.items()
            if info["status"] == "active"
        }
    
    def is_operation_allowed(self, module_id: str, operation: str) -> bool:
        """Check if operation is allowed for module. Returns False if module not found or operation not allowed."""
        module_info = self._blueprint_registry.get(module_id)
        if module_info is None:
            return False
        return operation in module_info.get("allowed_operations", [])

# Global registry validator instance
validator = Validator()