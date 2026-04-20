import sys
import os
import json
from unittest.mock import patch

# Mock out the engines that use DB connections or other complex things, since we just want to test Final Convergence
from app.services.final_convergence import final_convergence
# Wait, we need to make sure we don't hit real exceptions in unmocked signal_collector etc.
# Actually, the user says "Run system locally", Let's just run it with a simple script and mock if necessary
# Let's see if we can run it purely.

task_1_pass = {
    "task_title": "Governance Task Submission Evaluation",
    "task_description": "We need to evaluate a task for the task review engine within Niyantran governance.",
    "current_task_id": "T-GOV-001"
}

task_2_fail = {
    "task_title": "Core Database Relational Storage",
    "task_description": "Implementing relational storage within the database of core product.",
    "current_task_id": "T-COR-001"
}

task_3_edge = {
    "task_title": "Random generic task without specific words",
    "task_description": "Do some coding setup and create a basic file",
    "current_task_id": "T-GOV-002" # Edge case mapping will fail and trigger HARD REJECT
}

def test_cases():
    print("Running tests...")
    
    # Mocking canonical engine to return specific scores since Sri Satya connects to external
    with patch('app.services.final_convergence.assignment_engine.evaluate_and_assign') as mock_satya:
        
        # CASE 1: PASS
        print("\n--- CASE 1: PASS (Score >= 6) ---")
        mock_satya.return_value = {"score": 85, "score_10": 8.5, "status": "pass"}
        res1 = final_convergence.process_with_convergence(**task_1_pass)
        assert res1["task_type"] == "advancement"
        assert res1["submission_id"]
        print("CASE 1 SUCCESS. Output is deterministic advancement.")

        # CASE 2: FAIL
        print("\n--- CASE 2: FAIL (Score < 6) ---")
        mock_satya.return_value = {"score": 40, "score_10": 4.0, "status": "fail"}
        res2 = final_convergence.process_with_convergence(**task_2_fail)
        assert res2["task_type"] == "correction"
        assert res2["submission_id"]
        print("CASE 2 SUCCESS. Output is deterministic fallback/correction.")

        # CASE 3: EDGE
        print("\n--- CASE 3: EDGE (Mapping fail) ---")
        mock_satya.return_value = {"score": 75, "score_10": 7.5, "status": "borderline"}
        res3 = final_convergence.process_with_convergence(**task_3_edge)
        assert res3["task_type"] == "reinforcement"
        assert res3["capability"] == "Unknown", "Should be rejected heavily to fallback"
        print("CASE 3 SUCCESS. Output maps to Unknown correctly reflecting the HARD REJECT.")

        print("\nALL SYSTEM FINAL VERIFICATION TESTS PASSED SUCCESSFULLY.")
        
if __name__ == "__main__":
    test_cases()
