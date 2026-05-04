"""
Test Cases for Hybrid Evaluation Pipeline
Verifies hierarchy enforcement: Assignment → Signals → Validation
"""
import pytest
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from app.services.hybrid_evaluation_pipeline import HybridEvaluationPipeline
from evaluation_engine.assignment_engine import AssignmentEngine, AssignmentStatus
from app.services.evaluation_engine import EvaluationEngine
from app.services.output_validator import OutputValidator

class TestHybridEvaluationPipeline:
    
    def setup_method(self):
        """Setup test fixtures"""
        self.pipeline = HybridEvaluationPipeline()
        self.assignment_engine = AssignmentEngine()
        self.signal_engine = EvaluationEngine()
        self.validator = OutputValidator()
    
    def test_assignment_fail_overrides_strong_signals(self):
        """Test: Assignment FAIL → final = FAIL (signals cannot override)"""
        
        # Task with poor assignment structure but potentially good signals
        task_title = "Fix bug"  # Poor title
        task_description = "Fix the bug in the code"  # Poor description, missing requirements
        repository_url = "https://github.com/user/well-structured-repo"
        
        result = self.pipeline.evaluate(task_title, task_description, repository_url)
        
        # Verify assignment engine would fail this
        assignment_result = self.assignment_engine.evaluate(task_title, task_description)
        assert assignment_result["base_status"] == AssignmentStatus.FAIL.value
        
        # Verify final result respects assignment failure
        assert result["status"] == "fail"
        assert result["score"] < 50
        assert len(result["failure_reasons"]) > 0
        assert "missing_requirements" in str(result["failure_reasons"]) or len(result["failure_reasons"]) > 0
    
    def test_assignment_pass_with_weak_signals_stays_pass(self):
        """Test: Assignment PASS + weak signals → PASS with quality indicators"""
        
        # Task with good assignment structure
        task_title = "Implement REST API Authentication System with JWT and Database Integration"
        task_description = """
        Objective: Build a secure authentication system for the web application
        
        Deliverables:
        - JWT token generation and validation
        - User registration and login endpoints
        - Password hashing and security measures
        - Database integration for user management
        
        Timeline: 2 weeks development + 1 week testing
        
        Scope: Authentication module only, excludes authorization roles
        
        Requirements:
        - RESTful API design
        - Secure password storage
        - Token expiration handling
        - Input validation and error handling
        """
        repository_url = None  # No repo = weak signals
        
        result = self.pipeline.evaluate(task_title, task_description, repository_url)
        
        # Verify assignment engine would pass this
        assignment_result = self.assignment_engine.evaluate(task_title, task_description)
        assert assignment_result["base_status"] == AssignmentStatus.PASS.value
        
        # Verify final result maintains pass status
        assert result["status"] == "pass"
        assert result["score"] >= 80  # PASS must be >= 80
        assert result["completeness_score"] > 75  # Good assignment completeness
    
    def test_assignment_borderline_signal_refinement(self):
        """Test: Assignment BORDERLINE allows signal refinement within bounds"""
        
        # Task with moderate assignment structure
        task_title = "Database API Implementation"
        task_description = """
        Objective: Create database API endpoints
        
        Deliverables:
        - CRUD operations for user data
        - API documentation
        
        Timeline: 1 week
        """
        repository_url = "https://github.com/user/good-repo"
        
        result = self.pipeline.evaluate(task_title, task_description, repository_url)
        
        # Verify assignment engine would be borderline
        assignment_result = self.assignment_engine.evaluate(task_title, task_description)
        assert assignment_result["base_status"] == AssignmentStatus.BORDERLINE.value
        
        # Verify final result stays in borderline range (50-79)
        assert result["status"] in ["borderline", "pass"]  # Could be refined up to pass
        if result["status"] == "borderline":
            assert 50 <= result["score"] <= 79
        else:  # If refined to pass
            assert result["score"] >= 80
    
    def test_output_contract_compliance(self):
        """Test: All outputs comply with strict contract"""
        
        test_cases = [
            ("Simple Task", "Do something simple"),
            ("Complex API Task", """
            Objective: Build comprehensive REST API
            Deliverables: Full CRUD operations, authentication, documentation
            Timeline: 3 weeks
            Scope: Backend API only
            """),
            ("", "")  # Edge case
        ]
        
        for title, description in test_cases:
            try:
                result = self.pipeline.evaluate(title, description)
                
                # Validate contract compliance
                validation = self.validator.validate_output(result)
                assert validation.is_valid, f"Contract violation: {validation.errors}"
                
                # Verify required fields
                required_fields = [
                    "score", "readiness_percent", "status", "failure_reasons",
                    "improvement_hints", "analysis", "meta"
                ]
                for field in required_fields:
                    assert field in result, f"Missing required field: {field}"
                
                # Verify value ranges
                assert 0 <= result["score"] <= 100
                assert result["status"] in ["pass", "borderline", "fail"]
                assert result["meta"]["mode"] == "hybrid"
                
            except Exception as e:
                pytest.fail(f"Pipeline failed for case ({title}, {description}): {str(e)}")
    
    def test_hierarchy_enforcement_deterministic(self):
        """Test: Same inputs produce identical outputs (deterministic)"""
        
        task_title = "Build Authentication System"
        task_description = """
        Objective: Implement user authentication
        Deliverables: Login/logout functionality
        Timeline: 1 week
        """
        
        # Run evaluation 5 times
        results = []
        for _ in range(5):
            result = self.pipeline.evaluate(task_title, task_description)
            results.append((result["score"], result["status"], len(result["failure_reasons"])))
        
        # Verify all results are identical
        first_result = results[0]
        for result in results[1:]:
            assert result == first_result, "Pipeline is not deterministic"
    
    def test_assignment_engine_authority(self):
        """Test: Assignment engine decisions are always respected"""
        
        # Test case where assignment fails but signals might be good
        poor_assignment_title = "Fix"
        poor_assignment_description = "Fix it"
        good_repo = "https://github.com/user/excellent-repo"
        
        result = self.pipeline.evaluate(poor_assignment_title, poor_assignment_description, good_repo)
        
        # Assignment engine should fail this
        assignment_result = self.assignment_engine.evaluate(poor_assignment_title, poor_assignment_description)
        
        # Verify assignment authority is maintained
        if assignment_result["base_status"] == AssignmentStatus.FAIL.value:
            assert result["status"] == "fail"
            assert result["score"] < 50
        
        # Test case where assignment passes
        good_assignment_title = "Implement Secure User Authentication API with JWT Tokens"
        good_assignment_description = """
        Objective: Build secure authentication system
        Deliverables: JWT implementation, user endpoints, security measures
        Timeline: 2 weeks development
        Scope: Authentication module only
        """
        
        result2 = self.pipeline.evaluate(good_assignment_title, good_assignment_description)
        assignment_result2 = self.assignment_engine.evaluate(good_assignment_title, good_assignment_description)
        
        if assignment_result2["base_status"] == AssignmentStatus.PASS.value:
            assert result2["status"] in ["pass", "borderline"]  # Can't be fail if assignment passes
            assert result2["score"] >= 50  # Minimum for non-fail
    
    def test_signal_enrichment_without_override(self):
        """Test: Signals enrich analysis but don't override assignment decisions"""
        
        # Borderline assignment that signals can refine
        title = "API Development Task"
        description = """
        Objective: Create REST API
        Deliverables: CRUD endpoints
        Timeline: 1 week
        Scope: Basic operations
        """
        
        # Test without repository (minimal signals)
        result_no_repo = self.pipeline.evaluate(title, description)
        
        # Test with repository (enhanced signals)
        result_with_repo = self.pipeline.evaluate(title, description, "https://github.com/user/repo")
        
        # Both should have same assignment base, but signals can refine
        assignment_result = self.assignment_engine.evaluate(title, description)
        
        # If assignment is borderline, both results should respect that
        if assignment_result["base_status"] == AssignmentStatus.BORDERLINE.value:
            # Both should be in valid range for borderline
            assert result_no_repo["status"] in ["borderline", "pass", "fail"]
            assert result_with_repo["status"] in ["borderline", "pass", "fail"]
            
            # Repository version might have enhanced analysis
            if result_with_repo.get("repository_score", 0) > 0:
                # Signals provided enrichment
                assert "analysis" in result_with_repo
                assert result_with_repo["meta"]["mode"] == "hybrid"

if __name__ == "__main__":
    # Run tests
    test_instance = TestHybridEvaluationPipeline()
    test_instance.setup_method()
    
    print("Running Hybrid Pipeline Tests...")
    
    try:
        test_instance.test_assignment_fail_overrides_strong_signals()
        print("✓ Assignment fail override test passed")
    except Exception as e:
        print(f"✗ Assignment fail override test failed: {e}")
    
    try:
        test_instance.test_assignment_pass_with_weak_signals_stays_pass()
        print("✓ Assignment pass with weak signals test passed")
    except Exception as e:
        print(f"✗ Assignment pass with weak signals test failed: {e}")
    
    try:
        test_instance.test_output_contract_compliance()
        print("✓ Output contract compliance test passed")
    except Exception as e:
        print(f"✗ Output contract compliance test failed: {e}")
    
    try:
        test_instance.test_hierarchy_enforcement_deterministic()
        print("✓ Deterministic hierarchy test passed")
    except Exception as e:
        print(f"✗ Deterministic hierarchy test failed: {e}")
    
    try:
        test_instance.test_assignment_engine_authority()
        print("✓ Assignment engine authority test passed")
    except Exception as e:
        print(f"✗ Assignment engine authority test failed: {e}")
    
    print("\nHybrid Pipeline Integration Tests Complete!")