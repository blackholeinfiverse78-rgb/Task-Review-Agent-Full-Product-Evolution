
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

# Mock RepositoryAnalyzer to ensure determinism and avoid network noise
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

def run_test(name, input_data, iterations=1, expect_fail=False):
    print(f"\n--- {name} ---")
    results = []
    for i in range(iterations):
        try:
            res = niyantran_connection.process_niyantran_task(input_data)
            results.append(res)
            if expect_fail:
                print(f"ERROR: Expected failure but got success in iteration {i}")
                return False
        except Exception as e:
            if expect_fail:
                print(f"SUCCESS: Caught expected failure: {type(e).__name__}")
                return True
            else:
                print(f"ERROR: Unexpected failure in iteration {i}: {type(e).__name__}: {e}")
                return False
    
    # Check consistency
    for i in range(1, len(results)):
        if results[i] != results[0]:
            print(f"ERROR: Nondeterminism detected between iteration 0 and {i}")
            print(f"Diff: {results[0]} != {results[i]}")
            return False
    
    if iterations > 1:
        print(f"PASS: {iterations} iterations identical")
    
    # Check field count
    if len(results[0]) != 7:
        print(f"ERROR: Expected exactly 7 fields, got {len(results[0])}: {list(results[0].keys())}")
        return False
    
    # Check fields
    required = {"trace_id", "submission_id", "evaluation_result", "failure_type", "selected_task_id", "selection_reason", "source"}
    if set(results[0].keys()) != required:
        print(f"ERROR: Field mismatch. Found: {set(results[0].keys())}")
        return False
        
    print("PASS: Fields and contract valid")
    return results[0]

# --- TEST 1 & 8 ---
base_input = {
    "trace_id": "trace-constant-001",
    "task_id": "T-GOV-001",
    "task_title": "Test Title",
    "task_description": "Test description long enough to pass. " * 5,
    "submitted_by": "user-001",
    "repository_url": "https://github.com/test/repo"
}

t1_res = run_test("TEST 1 — SUBMISSION_ID DETERMINISM", base_input, iterations=5)

# --- TEST 3 ---
noise_input = base_input.copy()
noise_input["extra_field"] = "SHOULD_BE_IGNORED"
t3_res = run_test("TEST 3 — FIELD ORDER & STRICT CONTRACT", noise_input)

# --- TEST 4 ---
invalid_mapping_input = base_input.copy()
invalid_mapping_input["current_task_id"] = "NON_EXISTENT_TASK"
t4_ok = run_test("TEST 4 — GRAPH HARD FAILURE", invalid_mapping_input, expect_fail=True)

# --- TEST 6 ---
trace_tamper_input = base_input.copy()
trace_tamper_input["trace_id"] = ""
t6_ok = run_test("TEST 6 — TRACE TAMPERING", trace_tamper_input, expect_fail=True)

# --- TEST 7 ---
domain_trap_input = base_input.copy()
domain_trap_input["task_description"] = "This is a React frontend UI dashboard with Tailwind"
t7_res = run_test("TEST 7 — HIDDEN DOMAIN LOGIC", domain_trap_input)

# --- TEST 8 ---
shuffled_input = {
    "repository_url": "https://github.com/test/repo",
    "submitted_by": "user-001",
    "task_description": "Test description long enough to pass. " * 5,
    "task_title": "Test Title",
    "task_id": "T-GOV-001",
    "trace_id": "trace-constant-001"
}
t8_res = run_test("TEST 8 — ORDER INDEPENDENCE", shuffled_input)

# Check cross-test consistency
if t1_res and t8_res:
    if t1_res == t8_res:
        print("\n--- CONSISTENCY CHECK ---")
        print("PASS: Shuffled and base inputs produce identical output")
    else:
        print("\n--- CONSISTENCY CHECK ---")
        print("FAIL: Shuffled and base inputs produce DIFFERENT output")
