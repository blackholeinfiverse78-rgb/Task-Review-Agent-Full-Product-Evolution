"""
Product Core v1 - Orchestrator Tests
Integration tests for deterministic orchestration flow.
"""
import pytest
from datetime import datetime
from task_selector.review_orchestrator import ReviewOrchestrator
from evaluation_engine.review_engine import ReviewEngine
from contracts.schemas import Task
from db.persistent_storage import product_storage


@pytest.fixture(autouse=True)
def clear_storage():
    """Clear storage before each test"""
    product_storage.clear_all()
    yield
    product_storage.clear_all()


def test_process_submission_complete_flow():
    """Test complete orchestration flow from submission to storage"""
    orchestrator = ReviewOrchestrator(review_engine=ReviewEngine())
    
    task = Task(
        task_id="task-flow-001",
        task_title="Complete API Development with Database Integration",
        task_description="""
        Objective: Build a production-ready REST API with full CRUD operations.
        Requirement: Implement authentication and authorization.
        Constraint: Must support async operations.
        Technical Stack: FastAPI, PostgreSQL, Redis cache, JWT tokens.
        """,
        submitted_by="Developer",
        timestamp=datetime.now()
    )
    
    result = orchestrator.process_submission(task)
    
    # Verify response structure
    assert "submission_id" in result
    assert "review_id" in result
    assert "next_task_id" in result
    assert "review" in result
    assert "next_task" in result
    
    # Verify review content
    assert result["review"]["score"] >= 0
    assert result["review"]["score"] <= 100
    assert result["review"]["status"] in ["pass", "borderline", "fail"]
    
    # Verify next task content
    assert len(result["next_task"]["title"]) > 0
    assert result["next_task"]["difficulty"] in ["beginner", "intermediate", "advanced"]
    
    # Verify storage
    submission = product_storage.get_submission(result["submission_id"])
    assert submission is not None
    assert submission.task_title == task.task_title
    
    review = product_storage.get_review(result["review_id"])
    assert review is not None
    assert review.submission_id == result["submission_id"]
    
    next_task = product_storage.get_next_task(result["next_task_id"])
    assert next_task is not None
    assert next_task.review_id == result["review_id"]


def test_deterministic_orchestration():
    """Test that identical inputs produce identical outputs"""
    orchestrator = ReviewOrchestrator(review_engine=ReviewEngine())
    
    task = Task(
        task_id="task-det-001",
        task_title="Deterministic Test Task with Specific Requirements",
        task_description="""
        Objective: Verify deterministic behavior across multiple runs.
        Requirement: Same input must yield same score.
        Constraint: Zero randomness allowed.
        """,
        submitted_by="QA Engineer",
        timestamp=datetime.now()
    )
    
    # Run twice
    result1 = orchestrator.process_submission(task)
    
    # Clear storage and run again
    product_storage.clear_all()
    result2 = orchestrator.process_submission(task)
    
    # Scores must be identical
    assert result1["review"]["score"] == result2["review"]["score"]
    assert result1["review"]["status"] == result2["review"]["status"]
    assert result1["review"]["readiness_percent"] == result2["review"]["readiness_percent"]
    
    # Next task must be identical (based on score)
    assert result1["next_task"]["title"] == result2["next_task"]["title"]
    assert result1["next_task"]["difficulty"] == result2["next_task"]["difficulty"]


def test_pass_scenario():
    """Test high-quality task with description only (max 20 points)"""
    orchestrator = ReviewOrchestrator(review_engine=ReviewEngine())
    
    task = Task(
        task_id="task-pass-001",
        task_title="Enterprise-Grade Microservices Architecture Implementation",
        task_description="""
        Objective: Design and implement a scalable microservices architecture.
        Requirement: Support 10,000+ concurrent users with sub-100ms latency.
        Constraint: Zero downtime deployment required.
        
        Technical Stack:
        - API Gateway with load balancing
        - Database sharding and replication
        - Validation layer with schema enforcement
        - Security via OAuth2 and TLS
        - Async message queue for event processing
        - Caching strategy with Redis
        - Frontend integration with WebSocket support
        - Comprehensive documentation and README
        - Unit tests with 90%+ coverage
        - Integration tests for all endpoints
        """,
        submitted_by="Senior Architect",
        timestamp=datetime.now()
    )
    
    result = orchestrator.process_submission(task)
    
    # Description only can score max 20 points (no PDF/Repo data)
    assert result["review"]["score"] == 20
    assert result["review"]["status"] == "fail"  # < 50
    assert result["next_task"]["difficulty"] == "beginner"


def test_borderline_scenario():
    """Test moderate-quality task with description scoring"""
    orchestrator = ReviewOrchestrator(review_engine=ReviewEngine())
    
    task = Task(
        task_id="task-border-001",
        task_title="Basic API Implementation for User Management",
        task_description="""
        Requirement: Create API endpoints for user CRUD operations.
        Objective: Connect to database and handle requests.
        Constraint: Use REST principles.
        """,
        submitted_by="Junior Developer",
        timestamp=datetime.now()
    )
    
    result = orchestrator.process_submission(task)
    
    # Description with objective keyword gets 15 points (5 for length + 10 for keyword)
    assert result["review"]["score"] == 15
    assert result["review"]["status"] == "fail"  # < 50
    assert result["next_task"]["difficulty"] == "beginner"


def test_fail_scenario():
    """Test low-quality task yields FAIL status"""
    orchestrator = ReviewOrchestrator(review_engine=ReviewEngine())
    
    task = Task(
        task_id="task-fail-001",
        task_title="Fix bugs",
        task_description="Fix the issues in the code.",
        submitted_by="Lazy Dev",
        timestamp=datetime.now()
    )
    
    result = orchestrator.process_submission(task)
    
    assert result["review"]["status"] == "fail"
    assert result["review"]["score"] < 50
    assert result["next_task"]["difficulty"] == "beginner"
    assert len(result["review"]["failure_reasons"]) > 0


def test_storage_relationships():
    """Test that storage maintains proper relationships"""
    orchestrator = ReviewOrchestrator(review_engine=ReviewEngine())
    
    task = Task(
        task_id="task-rel-001",
        task_title="Relationship Test Task",
        task_description="Testing storage relationships between submission, review, and next task.",
        submitted_by="Tester",
        timestamp=datetime.now()
    )
    
    result = orchestrator.process_submission(task)
    
    # Verify submission → review link
    review = product_storage.get_review_by_submission(result["submission_id"])
    assert review is not None
    assert review.review_id == result["review_id"]
    
    # Verify review → next_task link
    next_task = product_storage.get_next_task(result["next_task_id"])
    assert next_task is not None
    assert next_task.review_id == result["review_id"]


def test_response_contract_stability():
    """Test that response contract is stable and complete"""
    orchestrator = ReviewOrchestrator(review_engine=ReviewEngine())
    
    task = Task(
        task_id="task-contract-001",
        task_title="Contract Stability Test",
        task_description="Objective: Verify response contract completeness.",
        submitted_by="QA",
        timestamp=datetime.now()
    )
    
    result = orchestrator.process_submission(task)
    
    # Top-level keys
    required_keys = ["submission_id", "review_id", "next_task_id", "review", "next_task"]
    for key in required_keys:
        assert key in result
    
    # Review keys
    review_keys = ["score", "readiness_percent", "status", "failure_reasons", 
                   "improvement_hints", "analysis"]
    for key in review_keys:
        assert key in result["review"]
    
    # Analysis keys
    analysis_keys = ["technical_quality", "clarity", "discipline_signals"]
    for key in analysis_keys:
        assert key in result["review"]["analysis"]
    
    # Next task keys
    next_task_keys = ["title", "objective", "focus_area", "difficulty"]
    for key in next_task_keys:
        assert key in result["next_task"]


def test_error_handling():
    """Test orchestrator handles errors gracefully"""
    # Create a mock failing engine
    class FailingEngine:
        def evaluate(self, task):
            raise Exception("Simulated engine failure")
    
    orchestrator = ReviewOrchestrator(review_engine=FailingEngine())
    
    task = Task(
        task_id="task-error-001",
        task_title="Error Handling Test",
        task_description="Testing error handling with failing engine.",
        submitted_by="Tester",
        timestamp=datetime.now()
    )
    
    result = orchestrator.process_submission(task)
    
    # Should return deterministic failure response
    assert result["review"]["status"] == "fail"
    assert result["review"]["score"] == 0
    assert "Review engine error" in result["review"]["failure_reasons"]
    
    # Storage should still work
    submission = product_storage.get_submission(result["submission_id"])
    assert submission is not None
