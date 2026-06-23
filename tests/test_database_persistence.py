import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from main import app
from db.persistent_storage import product_storage, TaskSubmission, ReviewRecord, NextTaskRecord
from db.db_config import SessionLocal
from db.models import TaskSubmissionModel, ReviewModel, AssignmentModel, CertificationModel, DimensionResultModel, Product, Builder
from task_selector.assignment_generator import automatic_assignment_engine

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_and_teardown():
    # Clear database and state files before each test
    product_storage.clear_all()
    
    # Pre-populate defaults
    db = SessionLocal()
    product = Product(id="prod-tantra", name="TANTRA Core", description="Governance consensus layer")
    builder = Builder(id="Test_Builder", name="Test_Builder", email="test@bhiv.com")
    db.add(product)
    db.add(builder)
    db.commit()
    db.close()
    
    yield
    
    product_storage.clear_all()

def test_store_and_retrieve_submission_db():
    """Verify that storing a submission persists in SQL database."""
    sub = TaskSubmission(
        submission_id="sub-test-123",
        task_id="task-123",
        task_title="Verify Consensus Node Integrity",
        task_description="Build a verification pipeline checking validation hashes in TANTRA core nodes.",
        submitted_by="Test_Builder",
        submitted_at=datetime.utcnow(),
        status="submitted",
        module_id="task-review-agent",
        schema_version="v1.0"
    )
    product_storage.store_submission(sub)
    
    # Retrieve via product_storage repository
    retrieved = product_storage.get_submission("sub-test-123")
    assert retrieved is not None
    assert retrieved.task_title == "Verify Consensus Node Integrity"
    assert retrieved.submitted_by == "Test_Builder"

    # Query DB directly to verify persistence
    db = SessionLocal()
    db_row = db.query(TaskSubmissionModel).filter(TaskSubmissionModel.submission_id == "sub-test-123").first()
    assert db_row is not None
    assert db_row.task_title == "Verify Consensus Node Integrity"
    db.close()

def test_store_and_retrieve_review_and_next_task_db():
    """Verify that storing reviews and next tasks persists in SQL database."""
    review = ReviewRecord(
        review_id="rev-test-123",
        submission_id="sub-test-123",
        trace_id="trace-test-123",
        evaluation_result="FAIL",
        score=40,
        readiness_percent=40,
        status="fail",
        decision="REJECTED",
        reviewed_by="Akash",
        reviewed_at=datetime.utcnow(),
        candidate_name="Test_Builder",
        task_title="Verify Consensus Node Integrity"
    )
    product_storage.store_review(review)
    
    next_task = NextTaskRecord(
        next_task_id="NT-REI-123",
        review_id="rev-test-123",
        previous_submission_id="sub-test-123",
        task_type="correction",
        title="Consensus Verification Fix",
        objective="Fix missing consensus checks and re-run",
        focus_area="Runtime",
        difficulty="intermediate",
        reason="Score is below fail threshold",
        assigned_at=datetime.utcnow()
    )
    product_storage.store_next_task(next_task)
    
    # Retrieve and assert repository output
    retrieved_review = product_storage.get_review("rev-test-123")
    assert retrieved_review is not None
    assert retrieved_review.score == 40
    
    retrieved_next_task = product_storage.get_next_task("NT-REI-123")
    assert retrieved_next_task is not None
    assert retrieved_next_task.title == "Consensus Verification Fix"

def test_automatic_assignment_generation():
    """Verify that failing dimensions trigger automatic task generation in database."""
    mock_report = {
        "system_information": {
            "trace_id": "trace-failed-demo-1",
            "verifier": "Certification Engine"
        },
        "dimensions": {
            "Runtime": "PASS",
            "Security": "FAIL",
            "Observability": "WARNING"
        },
        "production_score": 60,
        "certification_decision": "NOT PRODUCTION READY"
    }
    
    # Store dummy review to link
    review = ReviewRecord(
        review_id="rev-failed-demo-1",
        submission_id="sub-failed-demo-1",
        trace_id="trace-failed-demo-1",
        evaluation_result="FAIL",
        score=60,
        readiness_percent=60,
        status="fail",
        decision="REJECTED",
        reviewed_by="Akash",
        reviewed_at=datetime.utcnow(),
        candidate_name="Test_Builder",
        task_title="Verify Consensus Node Integrity"
    )
    product_storage.store_review(review)

    assignments = automatic_assignment_engine.generate_assignments(mock_report, review_id="rev-failed-demo-1")
    assert len(assignments) == 2  # Security (FAIL) and Observability (WARNING)
    
    # Assert specific assignments fields
    security_assignment = next(a for a in assignments if a["dimension"] == "Security")
    assert security_assignment["priority"] == "Critical"
    assert security_assignment["difficulty"] == "advanced"
    
    observability_assignment = next(a for a in assignments if a["dimension"] == "Observability")
    assert observability_assignment["priority"] == "Medium"
    assert observability_assignment["difficulty"] == "intermediate"

    # Verify directly in DB
    db = SessionLocal()
    db_rows = db.query(AssignmentModel).filter(AssignmentModel.review_id == "rev-failed-demo-1").all()
    assert len(db_rows) == 2
    categories = [r.category for r in db_rows]
    assert "Security" in categories
    assert "Observability" in categories
    db.close()

def test_soft_delete():
    """Verify that soft-deleted entries are excluded from queries."""
    next_task = NextTaskRecord(
        next_task_id="NT-DEL-123",
        review_id="rev-test-123",
        previous_submission_id="sub-test-123",
        task_type="correction",
        title="Consensus Verification Fix",
        objective="Fix missing consensus checks and re-run",
        focus_area="Runtime",
        difficulty="intermediate",
        reason="Score is below fail threshold",
        assigned_at=datetime.utcnow()
    )
    product_storage.store_next_task(next_task)
    
    # Soft delete in DB
    db = SessionLocal()
    row = db.query(AssignmentModel).filter(AssignmentModel.id == "NT-DEL-123").first()
    assert row is not None
    row.deleted_at = datetime.utcnow()
    db.commit()
    db.close()
    
    # Repository should now return None
    assert product_storage.get_next_task("NT-DEL-123") is None

def test_dashboard_api_views():
    """Verify dashboard API endpoints return aggregated metrics correctly."""
    # Seed data
    sub = TaskSubmission(
        submission_id="sub-dash-1",
        task_id="task-dash-1",
        task_title="Node Synchronization",
        task_description="Implement peer synchronization protocol in consensus node",
        submitted_by="Test_Builder",
        submitted_at=datetime.utcnow(),
        status="submitted"
    )
    product_storage.store_submission(sub)
    
    review = ReviewRecord(
        review_id="rev-dash-1",
        submission_id="sub-dash-1",
        trace_id="trace-dash-1",
        evaluation_result="FAIL",
        score=40,
        readiness_percent=40,
        status="fail",
        decision="REJECTED",
        reviewed_by="Akash",
        reviewed_at=datetime.utcnow(),
        candidate_name="Test_Builder",
        task_title="Node Synchronization"
    )
    product_storage.store_review(review)

    # 1. Builder Quality API
    res = client.get("/api/v1/dashboard/builder-quality")
    assert res.status_code == 200
    data = res.json()
    assert len(data["builders"]) == 1
    assert data["builders"][0]["builder_name"] == "Test_Builder"
    assert data["builders"][0]["total_reviews"] == 1
    assert data["builders"][0]["average_score"] == 40.0

    # 2. Product Readiness API
    res = client.get("/api/v1/dashboard/product-readiness")
    assert res.status_code == 200
    data = res.json()
    assert len(data["products"]) == 1
    assert data["products"][0]["product_id"] == "prod-tantra"
    assert data["products"][0]["certification_status"] == "NOT CERTIFIED"

    # 3. Ecosystem Health API
    res = client.get("/api/v1/dashboard/ecosystem-health")
    assert res.status_code == 200
    data = res.json()
    assert data["total_products"] == 1
    assert data["compliance_ratio_percent"] == 0.0  # 0 passed reviews out of 1
