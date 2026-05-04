from evaluation_engine.review_engine import ReviewEngine
from models.schemas import Task
from datetime import datetime

def test_deterministic_scoring():
    task = Task(
        task_id="test-1",
        task_title="Build a Secure Async API with Pydantic and Database Schema",
        task_description="Objective: Implement a production-ready API. Requirement: Use async database. Constraint: Schema validation via pydantic. Tech: FastAPI, Cache, Security.",
        submitted_by="Tester",
        timestamp=datetime.now()
    )
    
    review1 = ReviewEngine.review_task(task)
    review2 = ReviewEngine.review_task(task)
    
    assert review1.score == review2.score
    assert review1.status == review2.status
    assert review1.analysis.technical_quality == review2.analysis.technical_quality

def test_pass_case():
    # Long title, detailed description, all markers, multiple tech keywords
    task = Task(
        task_id="pass-1",
        task_title="Complete Infrastructure Migration to Cloud-Native Kubernetes Cluster",
        task_description="""
        Objective: Migrate the existing legacy system to a modern Kubernetes-based cloud architecture.
        Requirement: The system must support high availability and auto-scaling.
        Constraint: Zero downtime during migration is mandatory.
        
        Technical Stack:
        - API Gateway for load balancing
        - Database migration using schema evolution tools
        - Validation of all data endpoints
        - Security implementation using JWT and TLS
        - Async processing for background tasks
        - Caching layer for performance
        - Frontend integration with new backend
        - Documentation and README coverage
        - Unit and Integration Tests for high coverage
        """,
        submitted_by="Senior Dev",
        timestamp=datetime.now()
    )
    review = ReviewEngine.review_task(task)
    assert review.status == "pass"
    assert review.score >= 85

def test_borderline_case():
    task = Task(
        task_id="border-1",
        task_title="Implementation of a basic API to handle standardized requests and responses",
        task_description="Requirement: Create an API to handle requests. Objective: Connect to database. Constraint: None.",
        submitted_by="Junior Dev",
        timestamp=datetime.now()
    )
    review = ReviewEngine.review_task(task)
    assert review.status == "borderline"

def test_fail_case():
    task = Task(
        task_id="fail-1",
        task_title="Fix bugs",
        task_description="Fix the issues in the code.",
        submitted_by="Lazy Dev",
        timestamp=datetime.now()
    )
    review = ReviewEngine.review_task(task)
    assert review.status == "fail"

def test_schema_completeness():
    task = Task(
        task_id="schema-1",
        task_title="Test Schema Valid Output Structure Format Check",
        task_description="Objective: Ensure JSON contract is respected. Requirement: All keys present.",
        submitted_by="QA",
        timestamp=datetime.now()
    )
    review = ReviewEngine.review_task(task)
    
    # Check all required keys exist (via pydantic validation already, but double check)
    output_dict = review.model_dump()
    required_keys = ["score", "readiness_percent", "status", "failure_reasons", "improvement_hints", "analysis", "meta"]
    for key in required_keys:
        assert key in output_dict
        
    analysis_keys = ["technical_quality", "clarity", "discipline_signals"]
    for key in analysis_keys:
        assert key in output_dict["analysis"]
        
    meta_keys = ["evaluation_time_ms", "mode"]
    for key in meta_keys:
        assert key in output_dict["meta"]
