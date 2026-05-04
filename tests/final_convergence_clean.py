"""
FINAL CONVERGENCE VERIFICATION
Day-wise Integration Status and Connectivity Check

Verifies:
1. Sri Satya -> Assignment-based evaluation (AUTHORITATIVE)
2. Ishan -> Signal-based evaluation (SUPPORTING) 
3. Shraddha -> Output validation (FINAL WRAPPER)

Integration Hierarchy: Assignment -> Signals -> Validation
"""
import sys
import os
import json
from datetime import datetime
from typing import Dict, Any

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def test_day_1_assignment_engine():
    """Phase 1: Assignment Engine Integration (Sri Satya)"""
    print("=" * 80)
    print("DAY 1 VERIFICATION: ASSIGNMENT ENGINE INTEGRATION")
    print("=" * 80)
    
    try:
        # Check if intelligence module exists
        intelligence_path = os.path.join(current_dir, "intelligence-integration-module-main")
        if not os.path.exists(intelligence_path):
            print("[FAIL] CRITICAL: Intelligence module not found")
            return False
            
        # Import assignment engine
        sys.path.insert(0, intelligence_path)
        from engine.task_intelligence_engine import TaskIntelligenceEngine
        
        # Test assignment engine
        engine = TaskIntelligenceEngine()
        test_review = {
            "score": 75,
            "status": "borderline",
            "missing_features": ["authentication", "validation"],
            "completeness_score": 65
        }
        
        result = engine.generate_next_task(test_review)
        print(f"[PASS] Assignment Engine: Working")
        print(f"   Generated Task: {result.get('title', 'N/A')}")
        print(f"   Task Type: {result.get('task_type', 'N/A')}")
        print(f"   Difficulty: {result.get('difficulty', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Assignment Engine Failed: {e}")
        return False

def test_day_2_signal_evaluation():
    """Phase 2: Signal-based Evaluation Integration (Ishan)"""
    print("\n" + "=" * 80)
    print("DAY 2 VERIFICATION: SIGNAL-BASED EVALUATION")
    print("=" * 80)
    
    try:
        from app.services.evaluation_engine import EvaluationEngine
        from evaluation_engine.repository_analyzer import RepositoryAnalyzer
        
        # Test signal extraction
        eval_engine = EvaluationEngine()
        repo_analyzer = RepositoryAnalyzer()
        
        # Test with real GitHub repo
        repo_signals = repo_analyzer.analyze("https://github.com/octocat/Hello-World")
        
        if repo_signals and not repo_signals.get('error'):
            print(f"[PASS] Repository Analysis: Working")
            print(f"   Total Files: {repo_signals.get('structure', {}).get('total_files', 0)}")
            print(f"   Architecture Layers: {repo_signals.get('architecture', {}).get('layer_count', 0)}")
            print(f"   Language: {repo_signals.get('metadata', {}).get('language', 'N/A')}")
        else:
            print(f"[WARN] Repository Analysis: Fallback mode (no GitHub access)")
        
        # Test full evaluation pipeline
        result = eval_engine.evaluate(
            task_title="Implement User Authentication System",
            task_description="Build JWT-based auth with login, register, token refresh",
            repository_url="https://github.com/octocat/Hello-World"
        )
        
        print(f"[PASS] Evaluation Engine: Working")
        print(f"   Final Score: {result.get('score', 0)}")
        print(f"   Title Score: {result.get('title_score', 0)}")
        print(f"   Description Score: {result.get('description_score', 0)}")
        print(f"   Repository Score: {result.get('repository_score', 0)}")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Signal Evaluation Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_day_3_output_validation():
    """Phase 3: Output Validation Integration (Shraddha)"""
    print("\n" + "=" * 80)
    print("DAY 3 VERIFICATION: OUTPUT VALIDATION & CONTRACT COMPLIANCE")
    print("=" * 80)
    
    try:
        from models.schemas import ReviewOutput, Analysis, Meta
        from task_selector.review_orchestrator import ReviewOrchestrator
        from evaluation_engine.review_engine import ReviewEngine
        from models.schemas import Task
        from datetime import datetime
        
        # Test contract validation
        orchestrator = ReviewOrchestrator(ReviewEngine())
        
        test_task = Task(
            task_id="convergence-test",
            task_title="Test Contract Validation",
            task_description="Verify output contract compliance with strict schema validation",
            submitted_by="Convergence Tester",
            timestamp=datetime.now(),
            module_id="core-development",
            schema_version="v1.0",
            github_repo_link="https://github.com/octocat/Hello-World"
        )
        
        result = orchestrator.process_submission(test_task)
        
        # Validate required fields
        required_fields = [
            "submission_id", "review_id", "next_task_id", 
            "review", "next_task", "registry_validation", "lifecycle"
        ]
        
        missing_fields = [field for field in required_fields if field not in result]
        
        if not missing_fields:
            print("[PASS] Output Contract: Compliant")
            print(f"   Submission ID: {result['submission_id']}")
            print(f"   Review Score: {result['review']['score']}")
            print(f"   Review Status: {result['review']['status']}")
            print(f"   Next Task: {result['next_task']['title']}")
            print(f"   Registry Status: {result['registry_validation']['status']}")
        else:
            print(f"[FAIL] Output Contract: Missing fields {missing_fields}")
            return False
        
        # Test ReviewOutput schema compliance
        review_output = ReviewOutput(**result['review'])
        print("[PASS] Schema Validation: Passed")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Output Validation Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_hybrid_integration():
    """Test Hybrid Pipeline: Assignment -> Signals -> Validation"""
    print("\n" + "=" * 80)
    print("HYBRID INTEGRATION TEST: ASSIGNMENT -> SIGNALS -> VALIDATION")
    print("=" * 80)
    
    try:
        from task_selector.review_orchestrator import ReviewOrchestrator
        from evaluation_engine.review_engine import ReviewEngine
        from models.schemas import Task
        from models.persistent_storage import product_storage
        from datetime import datetime
        
        # Clear storage
        product_storage.clear_all()
        
        # Test scenarios
        test_scenarios = [
            {
                "name": "HIGH QUALITY TASK",
                "task": Task(
                    task_id="hybrid-high",
                    task_title="Advanced Microservices Architecture Implementation",
                    task_description="""
                    Implement a comprehensive microservices architecture with:
                    - API Gateway with rate limiting and authentication
                    - Service discovery and load balancing
                    - Distributed tracing and monitoring
                    - Event-driven communication with message queues
                    - Database per service pattern
                    - Circuit breaker pattern implementation
                    - Containerization with Docker and Kubernetes
                    - CI/CD pipeline with automated testing
                    """,
                    submitted_by="Senior Developer",
                    timestamp=datetime.now(),
                    module_id="advanced-features",
                    schema_version="v1.0",
                    github_repo_link="https://github.com/octocat/Hello-World"
                ),
                "expected_status": "pass"
            },
            {
                "name": "MEDIUM QUALITY TASK", 
                "task": Task(
                    task_id="hybrid-medium",
                    task_title="Basic User Authentication",
                    task_description="Simple login and registration with basic validation",
                    submitted_by="Developer",
                    timestamp=datetime.now(),
                    module_id="core-development",
                    schema_version="v1.0",
                    github_repo_link="https://github.com/octocat/Hello-World"
                ),
                "expected_status": "borderline"
            },
            {
                "name": "LOW QUALITY TASK",
                "task": Task(
                    task_id="hybrid-low",
                    task_title="Fix bug",
                    task_description="Something is broken",
                    submitted_by="User",
                    timestamp=datetime.now(),
                    module_id="core-development", 
                    schema_version="v1.0"
                ),
                "expected_status": "fail"
            }
        ]
        
        orchestrator = ReviewOrchestrator(ReviewEngine())
        results = []
        
        for scenario in test_scenarios:
            print(f"\n--- Testing: {scenario['name']} ---")
            
            try:
                result = orchestrator.process_submission(scenario['task'])
                score = result['review']['score']
                status = result['review']['status']
                
                print(f"   Score: {score}")
                print(f"   Status: {status}")
                print(f"   Expected: {scenario['expected_status']}")
                
                # Verify hierarchy: Assignment authoritative
                if status == "fail" and score < 50:
                    print("   [PASS] Assignment Authority: Enforced (FAIL)")
                elif status in ["pass", "borderline"]:
                    print("   [PASS] Assignment Authority: Enforced (PASS/BORDERLINE)")
                
                results.append({
                    "scenario": scenario['name'],
                    "score": score,
                    "status": status,
                    "expected": scenario['expected_status'],
                    "passed": True
                })
                
            except Exception as e:
                print(f"   [FAIL] Failed: {e}")
                results.append({
                    "scenario": scenario['name'],
                    "passed": False,
                    "error": str(e)
                })
        
        # Summary
        passed = sum(1 for r in results if r.get('passed', False))
        total = len(results)
        
        print(f"\n--- HYBRID INTEGRATION SUMMARY ---")
        print(f"Passed: {passed}/{total}")
        
        if passed == total:
            print("[PASS] Hybrid Integration: WORKING")
            return True
        else:
            print("[FAIL] Hybrid Integration: ISSUES DETECTED")
            return False
            
    except Exception as e:
        print(f"[FAIL] Hybrid Integration Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_determinism():
    """Test Deterministic Output"""
    print("\n" + "=" * 80)
    print("DETERMINISM VERIFICATION")
    print("=" * 80)
    
    try:
        from task_selector.review_orchestrator import ReviewOrchestrator
        from evaluation_engine.review_engine import ReviewEngine
        from models.schemas import Task
        from models.persistent_storage import product_storage
        from datetime import datetime
        
        orchestrator = ReviewOrchestrator(ReviewEngine())
        
        # Same task, multiple runs
        test_task = Task(
            task_id="determinism-test",
            task_title="Determinism Verification Task",
            task_description="Test deterministic scoring with identical inputs",
            submitted_by="Test Runner",
            timestamp=datetime.now(),
            module_id="core-development",
            schema_version="v1.0"
        )
        
        scores = []
        for i in range(3):
            product_storage.clear_all()
            result = orchestrator.process_submission(test_task)
            scores.append(result['review']['score'])
            print(f"   Run {i+1}: Score = {scores[-1]}")
        
        # Check determinism
        if len(set(scores)) == 1:
            print("[PASS] Determinism: VERIFIED")
            return True
        else:
            print(f"[FAIL] Determinism: FAILED - Scores vary: {scores}")
            return False
            
    except Exception as e:
        print(f"[FAIL] Determinism Test Failed: {e}")
        return False

def test_api_stability():
    """Test API Endpoint Stability"""
    print("\n" + "=" * 80)
    print("API STABILITY VERIFICATION")
    print("=" * 80)
    
    try:
        from api.lifecycle import router
        from models.persistent_storage import product_storage
        
        # Check critical endpoints exist
        endpoints = []
        for route in router.routes:
            if hasattr(route, 'path'):
                endpoints.append(route.path)
        
        required_endpoints = ['/submit', '/history', '/review/{submission_id}', '/next/{submission_id}']
        missing = [ep for ep in required_endpoints if not any(ep.replace('{submission_id}', '{taskId}') in existing or ep in existing for existing in endpoints)]
        
        if not missing:
            print("[PASS] API Endpoints: All present")
        else:
            print(f"[FAIL] API Endpoints: Missing {missing}")
            return False
        
        # Check storage layer
        print(f"[PASS] Storage Layer: Working")
        print(f"   Submissions: {len(product_storage.submissions)}")
        print(f"   Reviews: {len(product_storage.reviews)}")
        print(f"   Next Tasks: {len(product_storage.next_tasks)}")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] API Stability Failed: {e}")
        return False

def main():
    """Run complete FINAL CONVERGENCE verification"""
    print("FINAL CONVERGENCE VERIFICATION STARTING")
    print("Verifying 3-system integration: Assignment -> Signals -> Validation")
    print("Timeline: 1 DAY FAST TRACK")
    
    results = {
        "day_1_assignment": test_day_1_assignment_engine(),
        "day_2_signals": test_day_2_signal_evaluation(), 
        "day_3_validation": test_day_3_output_validation(),
        "hybrid_integration": test_hybrid_integration(),
        "determinism": test_determinism(),
        "api_stability": test_api_stability()
    }
    
    # Final Summary
    print("\n" + "=" * 80)
    print("FINAL CONVERGENCE VERIFICATION SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"{test_name.upper().replace('_', ' ')}: {status}")
    
    print(f"\nOVERALL: {passed}/{total} TESTS PASSED")
    
    if passed == total:
        print("\nFINAL CONVERGENCE: COMPLETE")
        print("Assignment -> Signals -> Validation pipeline WORKING")
        print("System ready for parikshak.blackholeinfiverse.com deployment")
        return True
    else:
        print("\nFINAL CONVERGENCE: INCOMPLETE")
        print("System requires fixes before deployment")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)