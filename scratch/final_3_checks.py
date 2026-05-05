
import sys
import os
import json
import logging
from unittest.mock import patch

# Add workspace root to sys.path
sys.path.append("g:/Live Task Review Agent - 2")

# Setup logging to suppress noise
logging.getLogger().setLevel(logging.CRITICAL)

from task_selector.niyantran_connection import niyantran_connection
from task_selector.final_convergence import final_convergence

# Mock RepositoryAnalyzer
def mock_repo_analyze(url):
    if url == "https://github.com/test/repo":
        return {
            "structure": {"total_files": 10, "total_dirs": 3, "languages": {"python": 10}},
            "components": {"routes": ["api.py"], "services": ["service.py"], "models": ["model.py"], "tests": ["test.py"], "docs": ["README.md"]},
            "architecture": {"has_layers": True, "modular": True, "layer_count": 5},
            "quality": {"readme_score": 3, "readme_val": 3, "documentation_density": 0.5},
            "metadata": {"name": "test-repo"}
        }
    return None

patcher = patch("evaluation_engine.repository_analyzer.RepositoryAnalyzer.analyze", side_effect=mock_repo_analyze)
patcher.start()

def check_1_long_chain():
    print("\n--- CHECK 1: Long Chain Traversal ---")
    chain = ["T-GEN-100", "T-GEN-101", "T-GEN-102", "T-GEN-103", "T-GEN-104"]
    current = chain[0]
    for i in range(len(chain)-1):
        input_data = {
            "trace_id": f"trace-chain-{i}",
            "task_id": current,
            "current_task_id": current,
            "task_title": "Chain Task",
            "task_description": "Task description for chain. " * 10,
            "submitted_by": "user-chain",
            "repository_url": "https://github.com/test/repo"
        }
        res = niyantran_connection.process_niyantran_task(input_data)
        next_task = res["selected_task_id"]
        if next_task != chain[i+1]:
            print(f"ERROR: Expected {chain[i+1]}, got {next_task}")
            return False
        current = next_task
    print("PASS: Long chain traversal successful")
    return True

def check_2_failure_cycling():
    print("\n--- CHECK 2: Failure Cycling ---")
    task_id = "T-GOV-001"
    # Force FAIL by using NO repo and short description
    input_data = {
        "trace_id": "trace-cycle",
        "task_id": task_id,
        "current_task_id": task_id,
        "task_title": "Cycle Test",
        "task_description": "Short",
        "submitted_by": "user-cycle",
        "repository_url": None # No repo
    }
    
    # 1st fail
    res1 = niyantran_connection.process_niyantran_task(input_data)
    f01 = res1["selected_task_id"]
    print(f"1st Fail: {task_id} -> {f01}")
    
    # Check consistency
    res3 = niyantran_connection.process_niyantran_task(input_data)
    if res3["selected_task_id"] == f01:
        print("PASS: Failure routing is deterministic")
    else:
        print(f"FAIL: Failure routing changed: {f01} != {res3['selected_task_id']}")
        return False
    return True

def check_3_corrupt_upstream():
    print("\n--- CHECK 3: Corrupt Upstream Input ---")
    try:
        final_convergence._enforce_output_contract({
            "trace_id": "trace-x",
            "submission_id": "sub-x",
            "evaluation_result": "FAIL",
            "failure_type": None,
            "selected_task_id": "T-X",
            "selection_reason": "test",
            "source": "task_graph"
        })
        print("FAIL: Contract violation NOT caught")
        return False
    except ValueError as e:
        print(f"SUCCESS: Caught contract violation: {e}")
        return True

if __name__ == "__main__":
    c1 = check_1_long_chain()
    c2 = check_2_failure_cycling()
    c3 = check_3_corrupt_upstream()
    
    if c1 and c2 and c3:
        print("\nALL 3 CHECKS PASS")
        print("FINAL STATUS: TRUE PASS")
    else:
        print("\nSOME CHECKS FAILED")
        print("FINAL STATUS: FAIL")
