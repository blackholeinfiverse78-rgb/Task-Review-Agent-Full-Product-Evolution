"""
Product Core v1 - Determinism Verification
"""
import pytest
from datetime import datetime
from task_selector.review_orchestrator import ReviewOrchestrator
from evaluation_engine.review_engine import ReviewEngine
from contracts.schemas import Task
from db.persistent_storage import product_storage


@pytest.fixture(autouse=True)
def clear_storage():
    product_storage.clear_all()
    yield
    product_storage.clear_all()


FIXED_TASK = Task(
    task_id="task-det-100",
    task_title="Determinism Verification Task with Specific Requirements",
    task_description="""
    Objective: Verify absolute determinism across iterations.
    Requirement: Same input must yield identical output every time.
    Constraint: Zero randomness, zero variance allowed.
    Technical Stack: FastAPI, PostgreSQL, Redis, Docker.
    """,
    submitted_by="QA Engineer",
    timestamp=datetime(2026, 2, 5, 10, 0, 0)
)


def test_determinism_100_iterations():
    orchestrator = ReviewOrchestrator(review_engine=ReviewEngine())
    results = []
    for _ in range(100):
        product_storage.clear_all()
        results.append(orchestrator.process_submission(FIXED_TASK))

    scores = [r["review"]["score"] for r in results]
    assert len(set(scores)) == 1, f"Score variance: {set(scores)}"

    statuses = [r["review"]["status"] for r in results]
    assert len(set(statuses)) == 1, f"Status variance: {set(statuses)}"

    next_titles = [r["next_task"]["title"] for r in results]
    assert len(set(next_titles)) == 1, f"Next task variance: {set(next_titles)}"


def test_determinism_multiple_tasks():
    orchestrator = ReviewOrchestrator(review_engine=ReviewEngine())
    tasks = [
        Task(task_id="t1", task_title="Short Task", task_description="Objective: Test short.",
             submitted_by="U1", timestamp=datetime.now()),
        Task(task_id="t2", task_title="Medium Length Task with More Details",
             task_description="Objective: Test medium. Requirement: Include structure. Constraint: Clarity.",
             submitted_by="U2", timestamp=datetime.now()),
    ]
    for task in tasks:
        task_results = []
        for _ in range(10):
            product_storage.clear_all()
            task_results.append(orchestrator.process_submission(task))
        scores = [r["review"]["score"] for r in task_results]
        assert len(set(scores)) == 1, f"Task {task.task_id} score variance: {set(scores)}"


def test_storage_determinism():
    orchestrator = ReviewOrchestrator(review_engine=ReviewEngine())
    task = Task(
        task_id="task-storage-det",
        task_title="Storage Determinism Test",
        task_description="Objective: Verify storage operations are deterministic.",
        submitted_by="Tester",
        timestamp=datetime(2026, 2, 5, 12, 0, 0)
    )
    product_storage.clear_all()
    r1 = orchestrator.process_submission(task)
    s1 = product_storage.get_submission(r1["submission_id"])
    rev1 = product_storage.get_review(r1["review_id"])

    product_storage.clear_all()
    r2 = orchestrator.process_submission(task)
    s2 = product_storage.get_submission(r2["submission_id"])
    rev2 = product_storage.get_review(r2["review_id"])

    assert s1.task_title == s2.task_title
    assert s1.submitted_by == s2.submitted_by
    assert rev1.score == rev2.score
    assert rev1.status == rev2.status
    assert rev1.analysis == rev2.analysis


def test_evaluation_time_is_non_negative():
    """Evaluation time must be >= 0 (not hardcoded, just valid)"""
    orchestrator = ReviewOrchestrator(review_engine=ReviewEngine())
    task = Task(
        task_id="task-time-det",
        task_title="Evaluation Time Test",
        task_description="Objective: Verify evaluation time is recorded.",
        submitted_by="Tester",
        timestamp=datetime.now()
    )
    result = orchestrator.process_submission(task)
    review = product_storage.get_review(result["review_id"])
    assert review.evaluation_time_ms >= 0
