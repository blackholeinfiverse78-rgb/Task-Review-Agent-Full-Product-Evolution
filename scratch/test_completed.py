
import sys
import os
import json
from unittest.mock import patch

# Add workspace root to sys.path
sys.path.append("g:/Live Task Review Agent - 2")

from task_selector.niyantran_connection import niyantran_connection

# Mock RepositoryAnalyzer
def mock_repo_analyze(url):
    return {
        "structure": {"total_files": 10, "total_dirs": 3, "languages": {"python": 10}},
        "components": {"routes": ["api.py"], "services": ["service.py"], "models": ["model.py"], "tests": ["test.py"], "docs": ["README.md"]},
        "architecture": {"has_layers": True, "modular": True, "layer_count": 5},
        "quality": {"readme_score": 3, "readme_val": 3, "documentation_density": 0.5},
        "metadata": {"name": "test-repo"}
    }

patcher = patch("evaluation_engine.repository_analyzer.RepositoryAnalyzer.analyze", side_effect=mock_repo_analyze)
patcher.start()

# T-VAA-001 routes to COMPLETED on PASS
input_data = {
    "trace_id": "trace-constant-003",
    "task_id": "T-VAA-001",
    "current_task_id": "T-VAA-001",
    "task_title": "Vaani TTS Validation",
    "task_description": "Validating Vaani TTS system. " * 10,
    "submitted_by": "user-003",
    "repository_url": "https://github.com/test/repo"
}

print("--- TEST 5 — COMPLETED NODE TRAP ---")
res = niyantran_connection.process_niyantran_task(input_data)
print(json.dumps(res, indent=2))
if res["selected_task_id"] == "COMPLETED":
    print("PASS: Routed to COMPLETED node correctly")
else:
    print(f"FAIL: Routed to {res['selected_task_id']} instead of COMPLETED")
