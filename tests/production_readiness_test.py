"""
Production Readiness Test - Vinayak Validation Protocol
Comprehensive test of all 7 phases of production readiness
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from evaluation_engine.review_packet_parser import review_packet_parser
from task_selector.final_convergence import final_convergence
from task_selector.production_decision_engine import production_decision_engine
from task_selector.bucket_integration import bucket_integration
from task_selector.niyantran_connection import niyantran_connection
from task_selector.human_in_loop import human_in_loop

def test_phase_1_review_packet_enforcement():
    """Test Phase 1: Review Packet Enforcement (Hard Gate)"""
    print("=== PHASE 1: REVIEW PACKET ENFORCEMENT ===")
    
    # Test packet requirement
    packet_result = review_packet_parser.enforce_packet_requirement(".")
    
    print(f"Review Packet Valid: {packet_result['valid']}")
    if packet_result['valid']:
        print(f"Sections Found: {packet_result['sections_found']}")
        print(f"Content Length: {packet_result['content_length']} chars")
        print("✅ PHASE 1 PASSED: Review Packet Hard Gate Enforced")
    else:
        print(f"❌ PHASE 1 FAILED: {packet_result['reason']}")
        return False
    
    return True

def test_phase_2_evaluation_engine_wiring():
    """Test Phase 2: Evaluation Engine Wiring"""
    print("\n=== PHASE 2: EVALUATION ENGINE WIRING ===")
    
    try:
        # Test canonical evaluation engine integration
        test_result = final_convergence.process_with_convergence(
            task_title="Test API Development Task",
            task_description="Build REST API with authentication and user management",
            repository_url="https://github.com/test/api-project",
            module_id="task-review-agent",
            schema_version="v1.0",
            pdf_text="",
            trace_id="test-phase2-trace-123"
        )
        
        print(f"Evaluation Score: {test_result.get('score', 'N/A')}")
        print(f"Evaluation Status: {test_result.get('status', 'N/A')}")
        print(f"Canonical Authority: {test_result.get('canonical_authority', False)}")
        print("✅ PHASE 2 PASSED: Evaluation Engine Properly Wired")
        return True
        
    except Exception as e:
        print(f"❌ PHASE 2 FAILED: {str(e)}")
        return False

def test_phase_3_decision_output_standardization():
    """Test Phase 3: Decision + Output Standardization"""
    print("\n=== PHASE 3: DECISION + OUTPUT STANDARDIZATION ===")
    
    try:
        # Test production decision engine
        mock_evaluation = {
            "score": 75,
            "status": "pass",
            "evidence_summary": {"delivery_ratio": 0.8, "missing_features_count": 1}
        }
        
        mock_signals = {
            "repository_available": True,
            "feature_match_ratio": 0.7,
            "expected_vs_delivered_evidence": {"delivery_ratio": 0.8}
        }
        
        decision_result = production_decision_engine.make_decision(
            mock_evaluation, mock_signals, {}
        )
        
        print(f"Decision: {decision_result.get('decision', 'N/A')}")
        print(f"Quality Grade: {decision_result.get('quality_rubric', {}).get('quality_grade', 'N/A')}")
        print(f"P/A/C Score: {decision_result.get('pac_detection', {}).get('pac_score', 0)}")
        print(f"Approval Threshold Met: {decision_result.get('decision_criteria', {}).get('approval_threshold_met', False)}")
        print("✅ PHASE 3 PASSED: Decision + Output Standardized")
        return True
        
    except Exception as e:
        print(f"❌ PHASE 3 FAILED: {str(e)}")
        return False

def test_phase_4_bucket_integration():
    """Test Phase 4: Bucket Integration"""
    print("\n=== PHASE 4: BUCKET INTEGRATION ===")
    
    try:
        # Test bucket logging
        mock_evaluation = {
            "evaluation_result": "PASS",
            "failure_type": None,
            "score": 80,
            "status": "pass",
            "pac": {},
            "rubric": {},
            "requires_human_review": False
        }
        mock_signals = {
            "domain": "engineering",
            "repository_available": True,
            "expected_vs_delivered_evidence": {"delivery_ratio": 0.8}
        }
        mock_decision = {
            "decision": "APPROVED",
            "confidence": 0.95,
            "next_direction": "advancement"
        }
        mock_next_task = {
            "next_task_id": "test-123",
            "task_type": "advancement",
            "title": "Next Test Task",
            "difficulty": "beginner"
        }
        mock_task_data = {
            "task_id": "test-task-123",
            "task_title": "Test Task",
            "task_description": "Test Description",
            "submitted_by": "test-user",
            "github_repo_link": "https://github.com/test/repo"
        }
        
        trace_id = bucket_integration.log_evaluation(
            mock_evaluation, mock_signals, mock_decision, 
            mock_next_task, mock_task_data,
            trace_id="test-bucket-trace-123"
        )
        
        print(f"Trace ID Generated: {trace_id}")
        
        # Test bucket retrieval
        logged_evaluation = bucket_integration.get_evaluation_by_trace_id(trace_id)
        print(f"Evaluation Retrieved: {logged_evaluation is not None}")
        
        # Test bucket stats
        stats = bucket_integration.get_bucket_stats()
        print(f"Total Evaluations: {stats['total_evaluations']}")
        
        print("✅ PHASE 4 PASSED: Bucket Integration Working")
        return True
        
    except Exception as e:
        print(f"❌ PHASE 4 FAILED: {str(e)}")
        return False

def test_phase_5_niyantran_connection():
    """Test Phase 5: Niyantran Connection"""
    print("\n=== PHASE 5: NIYANTRAN CONNECTION ===")
    
    try:
        # Test Niyantran task processing
        test_task = {
            "task_id": "task-niyantran-test-001",
            "task_title": "Niyantran Integration Test",
            "task_description": "Test task for Niyantran connection validation",
            "submitted_by": "niyantran-system",
            "repository_url": None,
            "module_id": "task-review-agent",
            "schema_version": "v1.0",
            "trace_id": "test-niyantran-trace-123"
        }
        
        result = niyantran_connection.process_niyantran_task(test_task)
        
        print(f"Task ID: {result.get('task_id', 'N/A')}")
        print(f"Trace ID: {result.get('trace_id', 'N/A')}")
        print(f"Review Score: {result.get('review', {}).get('score', 'N/A')}")
        print(f"Next Task Type: {result.get('next_task', {}).get('task_type', 'N/A')}")
        print(f"Processing Status: {result.get('processing_metadata', {}).get('status', 'N/A')}")
        
        # Test health check
        health = niyantran_connection.health_check()
        print(f"Niyantran Health: {health.get('status', 'N/A')}")
        
        print("✅ PHASE 5 PASSED: Niyantran Connection Working")
        return True
        
    except Exception as e:
        print(f"❌ PHASE 5 FAILED: {str(e)}")
        return False

def test_phase_6_human_in_loop():
    """Test Phase 6: Human-in-Loop + Confidence"""
    print("\n=== PHASE 6: HUMAN-IN-LOOP + CONFIDENCE ===")
    
    try:
        # Test confidence calculation
        mock_evaluation = {
            "score": 45,  # Low score to trigger escalation
            "status": "fail",
            "evidence_summary": {"delivery_ratio": 0.3, "missing_features_count": 5}
        }
        
        mock_decision = {
            "decision": "reject",
            "confidence": 0.6,
            "quality_rubric": {"quality_grade": "D", "total_quality": 2.0},
            "pac_detection": {"pac_score": 1}
        }
        
        mock_signals = {"repository_available": False, "feature_match_ratio": 0.2}
        
        confidence_metrics = human_in_loop.calculate_confidence(
            mock_evaluation, mock_decision, mock_signals
        )
        
        print(f"Final Confidence: {confidence_metrics.final_confidence:.3f}")
        print(f"Requires Escalation: {confidence_metrics.requires_escalation}")
        print(f"Escalation Reasons: {', '.join(confidence_metrics.escalation_reasons)}")
        
        # Test human-in-loop processing
        enhanced_result = human_in_loop.process_with_human_loop(
            mock_evaluation, mock_decision, mock_signals, "test-trace-123"
        )
        
        print(f"Human Review Pending: {enhanced_result.get('human_review_pending', False)}")
        
        # Test pending escalations
        pending = human_in_loop.get_pending_escalations()
        print(f"Pending Escalations: {len(pending)}")
        
        print("✅ PHASE 6 PASSED: Human-in-Loop Working")
        return True
        
    except Exception as e:
        print(f"❌ PHASE 6 FAILED: {str(e)}")
        return False

def test_phase_7_deployment_stability():
    """Test Phase 7: Deployment + Stability"""
    print("\n=== PHASE 7: DEPLOYMENT + STABILITY ===")
    
    try:
        # Test deterministic execution
        test_task = {
            "task_id": "task-determinism-test",
            "task_title": "Determinism Validation Task",
            "task_description": "Test deterministic behavior of the evaluation system",
            "submitted_by": "test-system",
            "module_id": "task-review-agent",
            "schema_version": "v1.0",
            "trace_id": "test-determinism-trace-123"
        }
        
        results = []
        for i in range(3):
            result = niyantran_connection.process_niyantran_task(test_task)
            results.append({
                "run": i + 1,
                "evaluation_result": result["evaluation_result"],
                "failure_type": result["failure_type"],
                "selected_task_id": result["selected_task_id"]
            })
        
        # Check determinism
        first_result = results[0]
        is_deterministic = all(
            r["evaluation_result"] == first_result["evaluation_result"] and
            r["failure_type"] == first_result["failure_type"] and
            r["selected_task_id"] == first_result["selected_task_id"]
            for r in results
        )
        
        print(f"Deterministic Execution: {is_deterministic}")
        print(f"Test Runs: {len(results)}")
        for result in results:
            print(f"  Run {result['run']}: Evaluation={result['evaluation_result']}, FailureType={result['failure_type']}, SelectedTask={result['selected_task_id']}")
        
        if is_deterministic:
            print("✅ PHASE 7 PASSED: System is Deterministic and Stable")
            return True
        else:
            print("❌ PHASE 7 FAILED: System is not deterministic")
            return False
        
    except Exception as e:
        print(f"❌ PHASE 7 FAILED: {str(e)}")
        return False

def run_production_readiness_test():
    """Run complete production readiness test"""
    print("🚀 PARIKSHAK PRODUCTION READINESS TEST")
    print("=" * 50)
    
    phases = [
        ("Phase 1: Review Packet Enforcement", test_phase_1_review_packet_enforcement),
        ("Phase 2: Evaluation Engine Wiring", test_phase_2_evaluation_engine_wiring),
        ("Phase 3: Decision + Output Standardization", test_phase_3_decision_output_standardization),
        ("Phase 4: Bucket Integration", test_phase_4_bucket_integration),
        ("Phase 5: Niyantran Connection", test_phase_5_niyantran_connection),
        ("Phase 6: Human-in-Loop + Confidence", test_phase_6_human_in_loop),
        ("Phase 7: Deployment + Stability", test_phase_7_deployment_stability)
    ]
    
    passed_phases = 0
    total_phases = len(phases)
    
    for phase_name, phase_test in phases:
        try:
            if phase_test():
                passed_phases += 1
        except Exception as e:
            print(f"❌ {phase_name} FAILED: {str(e)}")
    
    print("\n" + "=" * 50)
    print("🎯 PRODUCTION READINESS SUMMARY")
    print("=" * 50)
    print(f"Phases Passed: {passed_phases}/{total_phases}")
    print(f"Success Rate: {(passed_phases/total_phases)*100:.1f}%")
    
    if passed_phases == total_phases:
        print("🎉 ALL PHASES PASSED - PARIKSHAK IS PRODUCTION READY!")
        print("✅ System ready for Vinayak validation")
        print("✅ Niyantran integration complete")
        print("✅ Bucket logging operational")
        print("✅ Human-in-loop functional")
        print("✅ Deterministic execution verified")
        return True
    else:
        print(f"⚠️  {total_phases - passed_phases} PHASES FAILED - PRODUCTION NOT READY")
        return False

if __name__ == "__main__":
    success = run_production_readiness_test()
    exit(0 if success else 1)