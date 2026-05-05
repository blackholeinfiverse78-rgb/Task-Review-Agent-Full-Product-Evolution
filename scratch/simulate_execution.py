
import sys
import os
import json

# Add workspace root to sys.path
sys.path.append("g:/Live Task Review Agent - 2")

from task_selector.niyantran_connection import niyantran_connection

sample_task = {
    "task_id": "T-GOV-001",
    "task_title": "Production System Audit and Validation",
    "task_description": "Perform a comprehensive audit of the production system to ensure compliance with all boundary rules and safety constraints. Verify trace_id propagation and deterministic graph traversal.",
    "submitted_by": "auditor-01",
    "repository_url": "https://github.com/test/repo",
    "trace_id": "TRC-8899-7766-5544"
}

try:
    print("Simulating task submission...")
    result = niyantran_connection.process_niyantran_task(sample_task)
    print("SUCCESS: Result produced")
    print(json.dumps(result, indent=2))
except Exception as e:
    print(f"FAIL: Execution failed with error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
