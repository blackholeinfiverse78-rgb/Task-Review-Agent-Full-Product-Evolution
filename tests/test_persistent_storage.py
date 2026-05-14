"""
Product Core v1 - Storage Layer Tests
Tests for deterministic storage models and operations.
"""
import pytest
from datetime import datetime
from db.persistent_storage import (
    TaskSubmission,
    ReviewRecord,
    NextTaskRecord,
    TaskStatus,
    ProductStorage
)


def test_task_submission_creation():
    """Test explicit TaskSubmission creation"""
    submission = TaskSubmission(
        submission_id="sub-test-001",
        task_id="task-001",
        task_title="Test Task Title",
        task_description="This is a test task description with sufficient length.",
        submitted_by="Test User",
        submitted_at=datetime(2026, 2, 5, 10, 0, 0),
        status=TaskStatus.SUBMITTED
    )
    
    assert submission.submission_id == "sub-test-001"
    assert submission.task_id == "task-001"
    assert submission.status == TaskStatus.SUBMITTED
    assert submission.submitted_by == "Test User"


def test_review_record_creation():
    """Test explicit ReviewRecord creation"""
    review = ReviewRecord(
        review_id="rev-test-001",
        submission_id="sub-test-001",
        score=85,
        readiness_percent=85,
        status="pass",
        failure_reasons=[],
        improvement_hints=["Keep up the good work"],
        analysis={
            "technical_quality": 90,
            "clarity": 85,
            "discipline_signals": 80
        },
        reviewed_at=datetime(2026, 2, 5, 10, 1, 0),
        evaluation_time_ms=120
    )
    
    assert review.review_id == "rev-test-001"
    assert review.submission_id == "sub-test-001"
    assert review.score == 85
    assert review.status == "pass"


def test_next_task_record_creation():
    """Test explicit NextTaskRecord creation"""
    next_task = NextTaskRecord(
        next_task_id="next-test-001",
        review_id="rev-test-001",
        previous_submission_id="sub-test-001",
        task_type="advancement",
        title="Advanced Challenge",
        objective="Complete advanced system design",
        focus_area="Architecture",
        difficulty="advanced",
        reason="Score above pass threshold",
        assigned_at=datetime(2026, 2, 5, 10, 2, 0)
    )
    
    assert next_task.next_task_id == "next-test-001"
    assert next_task.review_id == "rev-test-001"
    assert next_task.difficulty == "advanced"
    assert next_task.task_type == "advancement"


def test_product_storage_operations():
    """Test ProductStorage CRUD operations"""
    storage = ProductStorage()
    
    # Create test data
    submission = TaskSubmission(
        submission_id="sub-001",
        task_id="task-001",
        task_title="Storage Test",
        task_description="Testing storage operations with explicit data.",
        submitted_by="Tester",
        submitted_at=datetime.now(),
        status=TaskStatus.SUBMITTED
    )
    
    review = ReviewRecord(
        review_id="rev-001",
        submission_id="sub-001",
        score=75,
        readiness_percent=75,
        status="borderline",
        failure_reasons=["Needs more detail"],
        improvement_hints=["Add technical specifics"],
        analysis={"technical_quality": 70, "clarity": 75, "discipline_signals": 80},
        reviewed_at=datetime.now(),
        evaluation_time_ms=120
    )
    
    next_task = NextTaskRecord(
        next_task_id="next-001",
        review_id="rev-001",
        previous_submission_id="sub-001",
        task_type="reinforcement",
        title="Intermediate Task",
        objective="Improve technical documentation",
        focus_area="Documentation",
        difficulty="intermediate",
        reason="Score in reinforcement range",
        assigned_at=datetime.now()
    )
    
    # Store
    storage.store_submission(submission)
    storage.store_review(review)
    storage.store_next_task(next_task)
    
    # Retrieve
    retrieved_submission = storage.get_submission("sub-001")
    retrieved_review = storage.get_review("rev-001")
    retrieved_next_task = storage.get_next_task("next-001")
    
    assert retrieved_submission.submission_id == "sub-001"
    assert retrieved_review.review_id == "rev-001"
    assert retrieved_next_task.next_task_id == "next-001"
    
    # Test relationship lookup
    linked_review = storage.get_review_by_submission("sub-001")
    assert linked_review.review_id == "rev-001"
    
    # Clear
    storage.clear_all()
    assert storage.get_submission("sub-001") is None


def test_storage_isolation():
    """Test that storage instances are isolated"""
    storage1 = ProductStorage()
    storage2 = ProductStorage()
    
    submission = TaskSubmission(
        submission_id="sub-iso-001",
        task_id="task-iso-001",
        task_title="Isolation Test",
        task_description="Testing storage isolation between instances.",
        submitted_by="Tester",
        submitted_at=datetime.now(),
        status=TaskStatus.SUBMITTED
    )
    
    storage1.store_submission(submission)
    
    # storage2 should not have the submission
    assert storage1.get_submission("sub-iso-001") is not None
    assert storage2.get_submission("sub-iso-001") is None


def test_task_status_enum():
    """Test TaskStatus enum values"""
    assert TaskStatus.ASSIGNED == "assigned"
    assert TaskStatus.SUBMITTED == "submitted"
    assert TaskStatus.REVIEWED == "reviewed"


def test_validation_constraints():
    """Test Pydantic validation on storage models"""
    # Test invalid score (out of range)
    with pytest.raises(Exception):
        ReviewRecord(
            review_id="rev-invalid",
            submission_id="sub-001",
            score=150,  # Invalid: > 100
            readiness_percent=85,
            status="pass",
            failure_reasons=[],
            improvement_hints=[],
            analysis={"technical_quality": 90, "clarity": 85, "discipline_signals": 80},
            reviewed_at=datetime.now(),
            evaluation_time_ms=120
        )
    
    # Test invalid status pattern
    with pytest.raises(Exception):
        ReviewRecord(
            review_id="rev-invalid",
            submission_id="sub-001",
            score=85,
            readiness_percent=85,
            status="invalid_status",  # Invalid: not in pattern
            failure_reasons=[],
            improvement_hints=[],
            analysis={"technical_quality": 90, "clarity": 85, "discipline_signals": 80},
            reviewed_at=datetime.now(),
            evaluation_time_ms=120
        )
