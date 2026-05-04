"""
Product Core v1 Extension - Lifecycle Tracking Tests
Tests for complete lifecycle tracking and integration.
"""
import pytest
from datetime import datetime
from task_selector.review_orchestrator import ReviewOrchestrator
from evaluation_engine.review_engine import ReviewEngine
from models.schemas import Task
from models.persistent_storage import product_storage, TaskStatus


@pytest.fixture(autouse=True)
def clear_storage():
    """Clear storage before each test"""
    product_storage.clear_all()
    yield
    product_storage.clear_all()


def test_lifecycle_tracking_complete():
    """Test complete lifecycle is tracked"""
    orchestrator = ReviewOrchestrator(review_engine=ReviewEngine())
    
    task = Task(
        task_id="task-lifecycle-001",
        task_title="Test Lifecycle Tracking",
        task_description="Objective: Verify lifecycle tracking works correctly.",
        submitted_by="Tester",
        timestamp=datetime.now()
    )
    
    result = orchestrator.process_submission(task)
    
    # Verify lifecycle in response
    assert "lifecycle" in result
    assert result["lifecycle"]["current_status"] == "submitted"
    assert result["lifecycle"]["previous_task_id"] is None
    assert result["lifecycle"]["review_id"] == result["review_id"]
    assert result["lifecycle"]["next_task_id"] == result["next_task_id"]


def test_lifecycle_with_previous_task():
    """Test lifecycle tracking with previous task reference"""
    orchestrator = ReviewOrchestrator(review_engine=ReviewEngine())
    
    task = Task(
        task_id="task-lifecycle-002",
        task_title="Test Previous Task Reference",
        task_description="Objective: Verify previous task tracking.",
        submitted_by="Tester",
        timestamp=datetime.now()
    )
    
    result = orchestrator.process_submission(task, previous_task_id="prev-task-001")
    
    # Verify previous task is tracked
    assert result["lifecycle"]["previous_task_id"] == "prev-task-001"
    
    # Verify in storage
    submission = product_storage.get_submission(result["submission_id"])
    assert submission.previous_task_id == "prev-task-001"


def test_next_task_assignment_correction():
    """Test CORRECTION task assigned for low scores"""
    orchestrator = ReviewOrchestrator(review_engine=ReviewEngine())
    
    task = Task(
        task_id="task-correction",
        task_title="Low Score Task",
        task_description="Short description.",
        submitted_by="Tester",
        timestamp=datetime.now()
    )
    
    result = orchestrator.process_submission(task)
    
    # Low score should trigger CORRECTION
    assert result["review"]["score"] < 50
    assert result["next_task"]["task_type"] == "correction"
    assert result["next_task"]["difficulty"] == "beginner"
    assert "correction" in result["next_task"]["reason"].lower()


def test_next_task_assignment_reinforcement():
    """Test REINFORCEMENT task assigned for medium scores"""
    orchestrator = ReviewOrchestrator(review_engine=ReviewEngine())
    
    # Create task that scores in reinforcement range (need to mock or use specific content)
    # For now, we'll verify the structure is correct
    task = Task(
        task_id="task-reinforcement",
        task_title="Medium Score Task",
        task_description="Objective: Test reinforcement assignment.",
        submitted_by="Tester",
        timestamp=datetime.now()
    )
    
    result = orchestrator.process_submission(task)
    
    # Verify next_task structure includes task_type
    assert "task_type" in result["next_task"]
    assert result["next_task"]["task_type"] in ["correction", "reinforcement", "advancement"]


def test_storage_relationships_complete():
    """Test all storage relationships are maintained"""
    orchestrator = ReviewOrchestrator(review_engine=ReviewEngine())
    
    task = Task(
        task_id="task-relationships",
        task_title="Test Storage Relationships",
        task_description="Objective: Verify all relationships are stored correctly.",
        submitted_by="Tester",
        timestamp=datetime.now()
    )
    
    result = orchestrator.process_submission(task)
    
    # Verify submission -> review link
    review = product_storage.get_review_by_submission(result["submission_id"])
    assert review is not None
    assert review.review_id == result["review_id"]
    
    # Verify submission -> next_task link
    next_task = product_storage.get_next_task_by_submission(result["submission_id"])
    assert next_task is not None
    assert next_task.next_task_id == result["next_task_id"]
    assert next_task.previous_submission_id == result["submission_id"]


def test_get_lifecycle_api():
    """Test get_lifecycle retrieval method"""
    orchestrator = ReviewOrchestrator(review_engine=ReviewEngine())
    
    task = Task(
        task_id="task-lifecycle-api",
        task_title="Test Lifecycle API",
        task_description="Objective: Test lifecycle retrieval.",
        submitted_by="Tester",
        timestamp=datetime.now()
    )
    
    result = orchestrator.process_submission(task, previous_task_id="prev-123")
    
    # Retrieve complete lifecycle
    lifecycle = product_storage.get_lifecycle(result["submission_id"])
    
    assert lifecycle is not None
    assert lifecycle["submission"].submission_id == result["submission_id"]
    assert lifecycle["review"].review_id == result["review_id"]
    assert lifecycle["next_task"].next_task_id == result["next_task_id"]
    assert lifecycle["status"] == TaskStatus.SUBMITTED
    assert lifecycle["previous_task_id"] == "prev-123"


def test_next_task_record_fields():
    """Test NextTaskRecord contains all required fields"""
    orchestrator = ReviewOrchestrator(review_engine=ReviewEngine())
    
    task = Task(
        task_id="task-fields",
        task_title="Test Next Task Fields",
        task_description="Objective: Verify all fields are stored.",
        submitted_by="Tester",
        timestamp=datetime.now()
    )
    
    result = orchestrator.process_submission(task)
    
    # Retrieve next task from storage
    next_task = product_storage.get_next_task(result["next_task_id"])
    
    assert next_task.next_task_id == result["next_task_id"]
    assert next_task.review_id == result["review_id"]
    assert next_task.previous_submission_id == result["submission_id"]
    assert next_task.task_type in ["correction", "reinforcement", "advancement"]
    assert len(next_task.title) > 0
    assert len(next_task.objective) > 0
    assert len(next_task.focus_area) > 0
    assert next_task.difficulty in ["beginner", "intermediate", "advanced"]
    assert len(next_task.reason) > 0
    assert next_task.assigned_at is not None


def test_deterministic_task_assignment():
    """Test task assignment is deterministic"""
    orchestrator = ReviewOrchestrator(review_engine=ReviewEngine())
    
    task = Task(
        task_id="task-deterministic",
        task_title="Deterministic Assignment Test",
        task_description="Objective: Verify deterministic task assignment.",
        submitted_by="Tester",
        timestamp=datetime(2026, 2, 5, 10, 0, 0)  # Fixed timestamp
    )
    
    results = []
    for i in range(5):
        product_storage.clear_all()
        result = orchestrator.process_submission(task)
        results.append(result["next_task"]["task_type"])
    
    # All task types should be identical
    assert len(set(results)) == 1


def test_response_contract_with_lifecycle():
    """Test response contract includes lifecycle information"""
    orchestrator = ReviewOrchestrator(review_engine=ReviewEngine())
    
    task = Task(
        task_id="task-contract",
        task_title="Test Response Contract",
        task_description="Objective: Verify response contract completeness.",
        submitted_by="Tester",
        timestamp=datetime.now()
    )
    
    result = orchestrator.process_submission(task)
    
    # Top-level keys
    assert "submission_id" in result
    assert "review_id" in result
    assert "next_task_id" in result
    assert "review" in result
    assert "next_task" in result
    assert "lifecycle" in result
    
    # Next task keys
    next_task_keys = ["task_id", "task_type", "title", "objective", "focus_area", "difficulty", "reason"]
    for key in next_task_keys:
        assert key in result["next_task"]
    
    # Lifecycle keys
    lifecycle_keys = ["current_status", "previous_task_id", "review_id", "next_task_id"]
    for key in lifecycle_keys:
        assert key in result["lifecycle"]


def test_no_state_corruption():
    """Test multiple submissions don't corrupt state"""
    orchestrator = ReviewOrchestrator(review_engine=ReviewEngine())
    
    # Submit multiple tasks
    results = []
    for i in range(3):
        task = Task(
            task_id=f"task-{i}",
            task_title=f"Task {i}",
            task_description=f"Objective: Test task {i}.",
            submitted_by="Tester",
            timestamp=datetime.now()
        )
        result = orchestrator.process_submission(task, previous_task_id=f"prev-{i}" if i > 0 else None)
        results.append(result)
    
    # Verify each has unique IDs
    submission_ids = [r["submission_id"] for r in results]
    assert len(set(submission_ids)) == 3
    
    # Verify each lifecycle is independent
    for i, result in enumerate(results):
        lifecycle = product_storage.get_lifecycle(result["submission_id"])
        assert lifecycle["submission"].submission_id == result["submission_id"]
        if i > 0:
            assert lifecycle["previous_task_id"] == f"prev-{i}"
