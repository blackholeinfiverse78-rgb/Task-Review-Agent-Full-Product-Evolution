"""
Registry Integration Tests
Tests for structural discipline enforcement in evaluation pipeline
"""
import pytest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from task_selector.review_orchestrator import ReviewOrchestrator
from evaluation_engine.review_engine import ReviewEngine
from contracts.schemas import Task
from db.persistent_storage import product_storage
from datetime import datetime

class TestRegistryIntegration:
    def setup_method(self):
        self.orchestrator = ReviewOrchestrator(review_engine=ReviewEngine())
        product_storage.clear_all()
    
    def test_valid_module_submission(self):
        """Test submission with valid module_id passes through pipeline"""
        task = Task(
            task_id="test-valid-001",
            task_title="Valid Module Test Task",
            task_description="Testing submission with valid module_id that should pass registry validation",
            submitted_by="Registry Tester",
            timestamp=datetime.now(),
            module_id="task-review-agent",  # Valid module
            schema_version="v1.0"  # Matching version
        )
        
        result = self.orchestrator.process_submission(task)
        
        # Should pass validation and proceed to scoring
        assert "submission_id" in result
        assert "review" in result
        assert result["registry_validation"]["status"] == "VALID"
        assert result["review"]["score"] >= 0  # Score was calculated
        assert result["review"]["meta"]["mode"] != "registry_rejection"
        
        # Verify submission was stored
        submission = product_storage.get_submission(result["submission_id"])
        assert submission is not None
        assert submission.task_title == task.task_title
    
    def test_invalid_module_submission(self):
        """Test submission with invalid module_id is rejected"""
        task = Task(
            task_id="test-invalid-001",
            task_title="Invalid Module Test Task", 
            task_description="Testing submission with invalid module_id that should be rejected",
            submitted_by="Registry Tester",
            timestamp=datetime.now(),
            module_id="non-existent-module",  # Invalid module
            schema_version="v1.0"
        )
        
        result = self.orchestrator.process_submission(task)
        
        # Should be rejected before scoring
        assert result["registry_validation"]["status"] == "INVALID"
        assert "not found in Blueprint Registry" in result["registry_validation"]["reason"]
        assert result["review"]["score"] == 0  # No scoring performed
        assert result["review"]["meta"]["mode"] == "registry_rejection"
        assert "Registry Validation Failed" in result["review"]["failure_reasons"][0]
        
        # Should assign corrective next task
        assert result["next_task"]["task_type"] == "correction"
        assert result["next_task"]["title"] == "Registry Compliance Task"
    
    def test_deprecated_module_submission(self):
        """Test submission with deprecated module is rejected"""
        task = Task(
            task_id="test-deprecated-001",
            task_title="Deprecated Module Test Task",
            task_description="Testing submission with deprecated module_id that should be rejected",
            submitted_by="Registry Tester", 
            timestamp=datetime.now(),
            module_id="legacy-module",  # Deprecated module
            schema_version="v0.9"
        )
        
        result = self.orchestrator.process_submission(task)
        
        # Should be rejected due to deprecated status
        assert result["registry_validation"]["status"] == "INVALID"
        assert "deprecated" in result["registry_validation"]["reason"]
        assert "cannot accept new work" in result["registry_validation"]["reason"]
        assert result["review"]["score"] == 0
        assert result["next_task"]["task_type"] == "correction"
    
    def test_schema_mismatch_submission(self):
        """Test submission with schema version mismatch is rejected"""
        task = Task(
            task_id="test-schema-001",
            task_title="Schema Mismatch Test Task",
            task_description="Testing submission with mismatched schema version",
            submitted_by="Registry Tester",
            timestamp=datetime.now(),
            module_id="evaluation-engine",  # Valid module
            schema_version="v1.0"  # Wrong version (module has v3.0)
        )
        
        result = self.orchestrator.process_submission(task)
        
        # Should be rejected due to schema mismatch
        assert result["registry_validation"]["status"] == "INVALID"
        assert "Schema version mismatch" in result["registry_validation"]["reason"]
        assert "has v3.0, required v1.0" in result["registry_validation"]["reason"]
        assert result["review"]["score"] == 0
        assert result["next_task"]["task_type"] == "correction"
    
    def test_development_module_allowed(self):
        """Test submission with development module is allowed"""
        task = Task(
            task_id="test-dev-001",
            task_title="Development Module Test Task",
            task_description="Testing submission with development module_id that should be allowed",
            submitted_by="Registry Tester",
            timestamp=datetime.now(),
            module_id="dev-module",  # Development module
            schema_version="v2.0-beta"
        )
        
        result = self.orchestrator.process_submission(task)
        
        # Should pass validation (development stage allows work)
        assert result["registry_validation"]["status"] == "VALID"
        assert result["review"]["score"] >= 0  # Scoring was performed
        assert result["review"]["meta"]["mode"] != "registry_rejection"
    
    def test_deterministic_validation_behavior(self):
        """Test that registry validation produces deterministic results"""
        task = Task(
            task_id="test-deterministic-001",
            task_title="Deterministic Validation Test",
            task_description="Testing deterministic behavior of registry validation",
            submitted_by="Registry Tester",
            timestamp=datetime.now(),
            module_id="task-review-agent",
            schema_version="v1.0"
        )
        
        results = []
        for i in range(5):
            product_storage.clear_all()
            result = self.orchestrator.process_submission(task)
            results.append({
                "validation_status": result["registry_validation"]["status"],
                "review_score": result["review"]["score"],
                "next_task_type": result["next_task"]["task_type"]
            })
        
        # All results should be identical
        first_result = results[0]
        for result in results[1:]:
            assert result == first_result
    
    def test_evaluation_pipeline_flow(self):
        """Test complete evaluation pipeline with registry validation"""
        # Test valid submission flows through complete pipeline
        valid_task = Task(
            task_id="test-flow-001",
            task_title="Pipeline Flow Test Task",
            task_description="Testing complete evaluation pipeline flow with registry validation",
            submitted_by="Pipeline Tester",
            timestamp=datetime.now(),
            module_id="lifecycle-orchestrator",
            schema_version="v1.1"
        )
        
        result = self.orchestrator.process_submission(valid_task)
        
        # Verify complete pipeline execution
        assert result["registry_validation"]["status"] == "VALID"
        
        # Verify all pipeline components executed
        submission = product_storage.get_submission(result["submission_id"])
        review = product_storage.get_review(result["review_id"])
        next_task = product_storage.get_next_task(result["next_task_id"])
        
        assert submission is not None
        assert review is not None
        assert next_task is not None
        
        # Verify data consistency
        assert review.submission_id == submission.submission_id
        assert next_task.previous_submission_id == submission.submission_id
        assert next_task.review_id == review.review_id
    
    def test_scoring_unchanged_for_valid_submissions(self):
        """Test that scoring logic remains unchanged for valid submissions"""
        task = Task(
            task_id="test-scoring-001",
            task_title="Scoring Consistency Test Task",
            task_description="Testing that scoring remains unchanged for valid registry submissions",
            submitted_by="Scoring Tester",
            timestamp=datetime.now(),
            module_id="task-review-agent",
            schema_version="v1.0"
        )
        
        result = self.orchestrator.process_submission(task)
        
        # Should have normal scoring behavior
        assert result["registry_validation"]["status"] == "VALID"
        assert result["review"]["score"] > 0  # Should get actual score
        assert len(result["review"]["failure_reasons"]) >= 0  # Normal failure reasons
        assert len(result["review"]["improvement_hints"]) >= 0  # Normal hints
        
        # Should not have registry-specific failure reasons
        failure_reasons = " ".join(result["review"]["failure_reasons"])
        assert "Registry Validation Failed" not in failure_reasons
    
    def test_audit_trail_for_rejected_submissions(self):
        """Test that rejected submissions create proper audit trail"""
        task = Task(
            task_id="test-audit-001",
            task_title="Audit Trail Test Task",
            task_description="Testing audit trail creation for rejected submissions",
            submitted_by="Audit Tester",
            timestamp=datetime.now(),
            module_id="invalid-module",
            schema_version="v1.0"
        )
        
        result = self.orchestrator.process_submission(task)
        
        # Verify audit trail exists
        submission = product_storage.get_submission(result["submission_id"])
        review = product_storage.get_review(result["review_id"])
        next_task = product_storage.get_next_task(result["next_task_id"])
        
        assert submission is not None
        assert review is not None
        assert next_task is not None
        
        # Verify rejection is properly recorded
        assert review.score == 0
        assert review.status == "fail"
        assert "Registry Validation Failed" in review.failure_reasons[0]
        assert next_task.task_type == "correction"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])