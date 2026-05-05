import sys
import os
import json
import logging

# Add the workspace root to sys.path
sys.path.append(r'g:\Live Task Review Agent - 2')

# Suppress logging for cleaner output
logging.basicConfig(level=logging.ERROR)

from task_selector.final_convergence import final_convergence
from engine.task_graph_engine import task_graph_engine

def run_test(case_name, input_data):
    print(f"--- Running {case_name} ---")
    try:
        output = final_convergence.process_with_convergence(
            evaluation_result=input_data["evaluation_result"],
            failure_type=input_data.get("failure_type"),
            submission_id=input_data["submission_id"],
            trace_id=input_data["trace_id"],
            current_task_id=input_data.get("current_task_id")
        )
        print(json.dumps(output, indent=2))
        return output
    except Exception as e:
        print(f"EXCEPTION: {str(e)}")
        return {"exception": str(e)}

# Define Test Cases
trace_id = "trace-test-001"

case_a = {
    "trace_id": trace_id,
    "submission_id": "sub-test-001",
    "evaluation_result": "PASS",
    "failure_type": None,
    "current_task_id": "T-GOV-001"
}

case_b = {
    "trace_id": trace_id,
    "submission_id": "sub-test-001",
    "evaluation_result": "FAIL",
    "failure_type": "incomplete",
    "current_task_id": "T-GOV-001"
}

case_c = {
    "trace_id": trace_id,
    "submission_id": "sub-test-001",
    "evaluation_result": "FAIL",
    "failure_type": "incorrect_logic",
    "current_task_id": "T-GOV-001"
}

case_d = {
    "trace_id": trace_id,
    "submission_id": "sub-test-001",
    "evaluation_result": "FAIL",
    "failure_type": "integration_fail",
    "current_task_id": "T-GOV-001"
}

edge_test = {
    "trace_id": trace_id,
    "submission_id": "sub-test-001",
    "evaluation_result": "PASS",
    "failure_type": None,
    "current_task_id": "UNKNOWN_TASK"
}

# Run Case A
out_a = run_test("Case A (PASS)", case_a)

# Run Case B
out_b = run_test("Case B (incomplete)", case_b)

# Run Case C
out_c = run_test("Case C (incorrect_logic)", case_c)

# Run Case D
out_d = run_test("Case D (integration_fail)", case_d)

# Run Determinism Test (Case A, 3 times)
print("\n--- Determinism Test (Case A) ---")
res1 = json.dumps(run_test("A-1", case_a), sort_keys=True)
res2 = json.dumps(run_test("A-2", case_a), sort_keys=True)
res3 = json.dumps(run_test("A-3", case_a), sort_keys=True)
if res1 == res2 == res3:
    print("DETERMINISM: PASS")
else:
    print("DETERMINISM: FAIL")

# Run Edge Test
out_edge = run_test("Edge Test (Unknown Mapping)", edge_test)
