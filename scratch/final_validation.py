
import sys
import os
import json
import logging

# Add workspace root to sys.path
sys.path.append("g:/Live Task Review Agent - 2")

from task_selector.niyantran_connection import niyantran_connection
from unittest.mock import patch

# Mock RepositoryAnalyzer to return valid signals for the PASS case
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

patcher = patch("evaluation_engine.signal_engine.RepositoryAnalyzer.analyze", side_effect=mock_repo_analyze)
patcher.start()

# Setup logging to suppress noise
logging.getLogger().setLevel(logging.ERROR)

def run_test_case(name, task_data):
    print(f"\n--- TEST CASE: {name} ---")
    try:
        result = niyantran_connection.process_niyantran_task(task_data)
        print(f"STATUS: SUCCESS")
        print(json.dumps(result, indent=2))
        return result
    except Exception as e:
        print(f"STATUS: HARD REJECT / FAIL")
        print(f"ERROR: {type(e).__name__}: {e}")
        return None

def test_determinism(task_data):
    print("\n--- TEST CASE: Determinism check ---")
    res1 = niyantran_connection.process_niyantran_task(task_data)
    res2 = niyantran_connection.process_niyantran_task(task_data)
    
    # Remove any possible non-deterministic fields if any exist (though we shouldn't have any now)
    if res1 == res2:
        print("DETERMINISM: PASS (Identical outputs)")
    else:
        print("DETERMINISM: FAIL (Outputs differ)")
        print("DIFF:")
        for k in res1:
            if res1[k] != res2[k]:
                print(f"  {k}: {res1[k]} != {res2[k]}")

# 1. PASS case
pass_case = {
    "task_id": "T-GOV-001",
    "task_title": "Production System Audit and Validation",
    "task_description": "Perform a comprehensive audit of the production system. This is a very detailed description that should pass the word count and completeness rules for a pass case. We need to check repository and architecture signals. " * 5,
    "submitted_by": "auditor-01",
    "repository_url": "https://github.com/test/repo",
    "trace_id": "TRC-PASS-001"
}

# 2. schema_violation (missing repository)
schema_case = {
    "task_id": "T-GOV-001",
    "task_title": "Too Short",
    "task_description": "Small",
    "submitted_by": "auditor-01",
    "trace_id": "TRC-SCHEMA-001"
}

# 3. incomplete (no proof/architecture in desc) - simulated by rule engine logic
incomplete_case = {
    "task_id": "T-GOV-001",
    "task_title": "Missing Proof Case",
    "task_description": "This is a description that lacks proof of work and architecture signals. It should fail the completeness check in the rule engine. " * 5,
    "submitted_by": "auditor-01",
    "repository_url": "https://github.com/test/repo-empty",
    "trace_id": "TRC-INCOMPLETE-001"
}

# 6. missing trace_id
missing_trace_case = {
    "task_id": "T-GOV-001",
    "task_title": "Missing Trace",
    "task_description": "No trace id provided.",
    "submitted_by": "auditor-01"
}

# 7. Unknown mapping (invalid current_task_id)
invalid_mapping_case = {
    "task_id": "T-GOV-001",
    "task_title": "Invalid Current Task",
    "task_description": "This task uses an invalid current_task_id.",
    "submitted_by": "auditor-01",
    "trace_id": "TRC-MAPPING-001",
    "current_task_id": "INVALID-TASK-ID"
}

if __name__ == "__main__":
    run_test_case("PASS Case", pass_case)
    run_test_case("Schema Violation", schema_case)
    run_test_case("Missing Trace ID", missing_trace_case)
    run_test_case("Unknown Mapping", invalid_mapping_case)
    test_determinism(pass_case)
