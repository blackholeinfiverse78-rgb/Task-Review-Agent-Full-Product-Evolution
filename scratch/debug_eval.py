
import sys
import os

# Add workspace root to sys.path
sys.path.append("g:/Live Task Review Agent - 2")

from evaluation_engine.orchestrator import evaluation_orchestrator

res = evaluation_orchestrator.evaluate_submission(
    task_title="Test Task",
    task_description="Test Description"
)

print(f"Result: {res['evaluation_result']}")
print(f"Failure Type: {res.get('failure_type')}")
print(f"Reason: {res.get('reason')}")
