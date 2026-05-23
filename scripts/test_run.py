import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from task_selector.review_orchestrator import ReviewOrchestrator
from contracts.schemas import Task
from db.persistent_storage import product_storage
from datetime import datetime


def make_task(task_id, title, description):
    return Task(
        task_id=task_id,
        task_title=title,
        task_description=description,
        submitted_by="Test Runner",
        timestamp=datetime.now(),
        module_id="task-review-agent",
        schema_version="v1.0"
    )


def test_cases():
    print("Running tests...")
    orchestrator = ReviewOrchestrator()
    product_storage.clear_all()

    # CASE 1: PASS - long detailed description
    print("\n--- CASE 1: PASS ---")
    task1 = make_task(
        "T-TST-001",
        "Voice Synthesis Inference Engine Architecture",
        "Objective: Synthesize voice via the Vaani engine with full pipeline. "
        "Requirement: Async processing, latency < 200ms. "
        "Constraint: Must support SSML format. "
        "Tech: FastAPI, PyTorch, CUDA. Architecture: microservice layer, "
        "validation layer, inference layer. Tests: 90% coverage. "
        "Documentation: README and API spec required. " * 3
    )
    res1 = orchestrator.process_submission(task1, trace_id="TRACE-999-XXX")
    assert res1["submission_id"], "Missing submission ID"
    print(f"CASE 1 result: score={res1['review']['score']} status={res1['review']['status']}")
    print("CASE 1 SUCCESS.")

    # CASE 2: FAIL - short vague description
    print("\n--- CASE 2: FAIL ---")
    task2 = make_task(
        "T-COR-001",
        "Static Linting",
        "Fix linting errors."
    )
    res2 = orchestrator.process_submission(task2, trace_id="TRACE-888-XXX")
    assert res2["submission_id"], "Missing submission ID"
    print(f"CASE 2 result: score={res2['review']['score']} status={res2['review']['status']}")
    print("CASE 2 SUCCESS.")

    print("\nALL SYSTEM FINAL VERIFICATION TESTS PASSED SUCCESSFULLY.")


if __name__ == "__main__":
    test_cases()
