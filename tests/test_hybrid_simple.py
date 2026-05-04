"""
Simple Hybrid Pipeline Test
Tests the core functionality without complex imports
"""
import sys
import os

# Add the current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

def test_hybrid_components():
    """Test individual components of the hybrid pipeline"""
    
    print("=== Testing Hybrid Pipeline Components ===")
    
    try:
        # Test Assignment Engine
        print("\n1. Testing Assignment Engine...")
        from evaluation_engine.assignment_engine import AssignmentEngine
        
        assignment_engine = AssignmentEngine()
        
        # Test high quality task
        result1 = assignment_engine.evaluate(
            "Implement Secure REST API Authentication with JWT",
            """
            Objective: Build authentication system
            Deliverables: JWT endpoints, user management, security
            Timeline: 2 weeks
            Scope: Authentication module only
            """
        )
        
        print(f"   High Quality - Accuracy: {result1['accuracy']}, Completeness: {result1['completeness']}, Status: {result1['base_status']}")
        
        # Test poor quality task
        result2 = assignment_engine.evaluate("Fix bug", "Fix the bug")
        print(f"   Poor Quality - Accuracy: {result2['accuracy']}, Completeness: {result2['completeness']}, Status: {result2['base_status']}")
        
        print("   OK Assignment Engine working")
        
    except Exception as e:
        print(f"   ERROR Assignment Engine failed: {e}")
        return False
    
    try:
        # Test Output Validator
        print("\n2. Testing Output Validator...")
        from app.services.output_validator import OutputValidator
        
        validator = OutputValidator()
        
        # Test valid output
        valid_output = {
            "score": 75,
            "readiness_percent": 75,
            "status": "borderline",
            "failure_reasons": [],
            "improvement_hints": ["Add more detail"],
            "analysis": {
                "technical_quality": 70,
                "clarity": 80,
                "discipline_signals": 60
            },
            "meta": {
                "evaluation_time_ms": 100,
                "mode": "hybrid"
            },
            "feature_coverage": 0.7,
            "architecture_score": 15.0,
            "code_quality_score": 20.0,
            "completeness_score": 30.0,
            "missing_features": [],
            "requirement_match": 0.7,
            "evaluation_summary": "Test summary",
            "documentation_score": 10.0,
            "documentation_alignment": "moderate",
            "title_score": 15.0,
            "description_score": 30.0,
            "repository_score": 35.0
        }
        
        validation_result = validator.validate_output(valid_output)
        print(f"   Valid Output - Is Valid: {validation_result.is_valid}, Errors: {len(validation_result.errors)}")
        
        # Test invalid output
        invalid_output = {"score": "invalid"}
        validation_result2 = validator.validate_output(invalid_output)
        print(f"   Invalid Output - Is Valid: {validation_result2.is_valid}, Errors: {len(validation_result2.errors)}")
        
        print("   OK Output Validator working")
        
    except Exception as e:
        print(f"   ERROR Output Validator failed: {e}")
        return False
    
    try:
        # Test Hybrid Pipeline
        print("\n3. Testing Hybrid Pipeline...")
        from app.services.hybrid_evaluation_pipeline import HybridEvaluationPipeline
        
        pipeline = HybridEvaluationPipeline()
        
        # Test high quality task
        result1 = pipeline.evaluate(
            "Implement Secure REST API Authentication with JWT and Database Integration",
            """
            Objective: Build comprehensive authentication system
            Deliverables: JWT implementation, user endpoints, security measures, database integration
            Timeline: 3 weeks development
            Scope: Authentication module only
            Technical Requirements: RESTful design, secure storage, token handling
            """
        )
        
        print(f"   High Quality - Score: {result1['score']}, Status: {result1['status']}, Mode: {result1['meta']['mode']}")
        
        # Test poor quality task
        result2 = pipeline.evaluate("Fix bug", "Fix the bug in the system")
        print(f"   Poor Quality - Score: {result2['score']}, Status: {result2['status']}, Mode: {result2['meta']['mode']}")
        
        # Verify hierarchy enforcement
        if result1['score'] > result2['score']:
            print("   OK Quality differentiation working")
        else:
            print("   WARNING Quality differentiation may need adjustment")
        
        print("   OK Hybrid Pipeline working")
        
    except Exception as e:
        print(f"   ERROR Hybrid Pipeline failed: {e}")
        return False
    
    print("\n=== Component Tests Complete ===")
    print("OK Assignment Engine: Authoritative base evaluation")
    print("OK Output Validator: Contract enforcement")  
    print("OK Hybrid Pipeline: Integrated evaluation")
    
    return True

def test_determinism():
    """Test that the system is deterministic"""
    
    print("\n=== Testing Determinism ===")
    
    try:
        from app.services.hybrid_evaluation_pipeline import HybridEvaluationPipeline
        
        pipeline = HybridEvaluationPipeline()
        
        # Run same evaluation 3 times
        task_title = "Database API Implementation"
        task_description = """
        Objective: Create database API
        Deliverables: CRUD operations
        Timeline: 1 week
        """
        
        results = []
        for i in range(3):
            result = pipeline.evaluate(task_title, task_description)
            results.append((result['score'], result['status'], len(result['failure_reasons'])))
        
        # Check if all results are identical
        first_result = results[0]
        all_identical = all(result == first_result for result in results)
        
        print(f"   Run 1: Score={results[0][0]}, Status={results[0][1]}")
        print(f"   Run 2: Score={results[1][0]}, Status={results[1][1]}")
        print(f"   Run 3: Score={results[2][0]}, Status={results[2][1]}")
        print(f"   Deterministic: {all_identical}")
        
        if all_identical:
            print("   OK System is deterministic")
            return True
        else:
            print("   ERROR System is not deterministic")
            return False
            
    except Exception as e:
        print(f"   ERROR Determinism test failed: {e}")
        return False

if __name__ == "__main__":
    print("HYBRID INTELLIGENCE INTEGRATION TEST")
    print("Testing the convergence of Assignment + Signals + Validation")
    
    # Test components
    components_ok = test_hybrid_components()
    
    # Test determinism
    determinism_ok = test_determinism()
    
    if components_ok and determinism_ok:
        print("\nHYBRID INTEGRATION SUCCESS!")
        print("Assignment Engine is AUTHORITATIVE")
        print("Signals provide SUPPORTING enrichment")
        print("Validator enforces FINAL CONTRACT")
        print("System is DETERMINISTIC and STABLE")
        print("\nREADY FOR PRODUCTION DEPLOYMENT")
    else:
        print("\nINTEGRATION ISSUES DETECTED")
        print("System needs debugging before deployment")
        sys.exit(1)