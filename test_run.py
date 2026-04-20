import sys
import os
import json
from unittest.mock import patch

from app.services.final_convergence import final_convergence

task_1_pass = {
    "task_title": "Voice Synthesis Inference Engine",
    "task_description": "We need to synthesize voice via the Vaani engine.",
    "current_task_id": "T-TST-001",
    "trace_id": "TRACE-999"
}

task_2_fail = {
    "task_title": "Parikshak Static Linting Validation",
    "task_description": "Static code analysis to enforce styles in Evaluation.",
    "current_task_id": "T-COR-001",
    "trace_id": "TRACE-888"
}

task_3_edge = {
    "task_title": "Random generic task without specific words",
    "task_description": "Do some coding setup and create a basic file",
    "current_task_id": "T-GOV-002",
    "trace_id": "TRACE-777"
}

def test_cases():
    print("Running tests...")
    
    with patch('app.services.final_convergence.assignment_engine.evaluate_and_assign') as mock_satya:
        
        # CASE 1: PASS
        print("\n--- CASE 1: PASS (Score >= 6) ---")
        mock_satya.return_value = {"score": 85, "score_10": 8.5, "status": "pass"}
        res1 = final_convergence.process_with_convergence(**task_1_pass)
        assert res1["task_type"] == "advancement", "Expected advancement task type"
        assert res1["submission_id"], "Missing submission ID"
        assert res1.get("trace_id") == "TRACE-999", "Trace ID was not preserved"
        print("CASE 1 SUCCESS. Output is deterministic advancement.")

        # CASE 2: FAIL
        print("\n--- CASE 2: FAIL (Score < 6) ---")
        mock_satya.return_value = {"score": 40, "score_10": 4.0, "status": "fail"}
        res2 = final_convergence.process_with_convergence(**task_2_fail)
        assert res2["task_type"] == "correction", "Expected correction task type"
        assert res2["submission_id"], "Missing submission ID"
        assert res2.get("trace_id") == "TRACE-888", "Trace ID was not preserved"
        print("CASE 2 SUCCESS. Output is deterministic fallback/correction.")

        # CASE 3: EDGE
        print("\n--- CASE 3: EDGE (Mapping fail) ---")
        mock_satya.return_value = {"score": 75, "score_10": 7.5, "status": "borderline"}
        res3 = final_convergence.process_with_convergence(**task_3_edge)
        # It's a HARD REJECT from mapping, meaning validate_final_output wraps it
        assert res3.get("mapping_rejection") == True or res3.get("rejection_type") == "mapping_rejection" or "mapping_rejected" in str(res3)
        assert res3.get("trace_id") == "TRACE-777", "Trace ID was not preserved in Hard Reject"
        print("CASE 3 SUCCESS. Output maps to Hard Reject correctly.")

        print("\nALL SYSTEM FINAL VERIFICATION TESTS PASSED SUCCESSFULLY.")
        
if __name__ == "__main__":
    test_cases()
