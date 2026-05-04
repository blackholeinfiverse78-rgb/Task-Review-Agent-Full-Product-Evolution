"""
Product Core v1 - Lifecycle API Tests
Tests for stable API contracts and response consistency.
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime

from main import app
from models.persistent_storage import product_storage

client = TestClient(app)

VALID_FORM = {
    "task_title": "Test API Submission",
    "task_description": "Objective: Test API contract stability.",
    "submitted_by": "API Tester",
    "github_repo_link": "https://github.com/example/repo",
    "module_id": "task-review-agent",
    "schema_version": "v1.0",
}

@pytest.fixture(autouse=True)
def clear_storage():
    product_storage.clear_all()
    yield
    product_storage.clear_all()


def test_submit_task_stable_contract():
    response = client.post("/api/v1/lifecycle/submit", data=VALID_FORM)
    assert response.status_code == 200
    data = response.json()
    assert "submission_id" in data
    assert "review_summary" in data
    assert "next_task_summary" in data
    assert "score" in data["review_summary"]
    assert "status" in data["review_summary"]
    assert "readiness_percent" in data["review_summary"]
    assert "task_id" in data["next_task_summary"]
    assert "task_type" in data["next_task_summary"]
    assert "title" in data["next_task_summary"]
    assert "difficulty" in data["next_task_summary"]


def test_submit_task_with_previous():
    form = {**VALID_FORM, "task_title": "Test Lifecycle Tracking",
            "task_description": "Objective: Verify previous task tracking.",
            "previous_task_id": "prev-123"}
    response = client.post("/api/v1/lifecycle/submit", data=form)
    assert response.status_code == 200
    assert "submission_id" in response.json()


def test_get_history_deterministic_sorting():
    for i in range(3):
        client.post("/api/v1/lifecycle/submit", data={
            **VALID_FORM,
            "task_title": f"Task Number {i} Test",
            "task_description": f"Objective: Test task {i} description.",
        })
    response = client.get("/api/v1/lifecycle/history")
    assert response.status_code == 200
    history = response.json()
    assert len(history) == 3
    timestamps = [item["submitted_at"] for item in history]
    assert timestamps == sorted(timestamps)
    for item in history:
        for field in ["submission_id", "task_title", "submitted_by", "submitted_at", "score", "status"]:
            assert field in item


def test_get_review_stable_contract():
    submit_response = client.post("/api/v1/lifecycle/submit", data=VALID_FORM)
    submission_id = submit_response.json()["submission_id"]
    response = client.get(f"/api/v1/lifecycle/review/{submission_id}")
    assert response.status_code == 200
    data = response.json()
    for field in ["review_id", "submission_id", "score", "readiness_percent",
                  "status", "failure_reasons", "improvement_hints", "analysis", "reviewed_at"]:
        assert field in data


def test_get_next_task_stable_contract():
    submit_response = client.post("/api/v1/lifecycle/submit", data=VALID_FORM)
    submission_id = submit_response.json()["submission_id"]
    response = client.get(f"/api/v1/lifecycle/next/{submission_id}")
    assert response.status_code == 200
    data = response.json()
    for field in ["next_task_id", "review_id", "task_type", "title",
                  "objective", "focus_area", "difficulty", "reason", "assigned_at"]:
        assert field in data


def test_review_not_found():
    response = client.get("/api/v1/lifecycle/review/nonexistent")
    assert response.status_code == 404


def test_next_task_not_found():
    response = client.get("/api/v1/lifecycle/next/nonexistent")
    assert response.status_code == 404


def test_no_response_drift():
    responses = []
    for _ in range(3):
        product_storage.clear_all()
        response = client.post("/api/v1/lifecycle/submit", data=VALID_FORM)
        responses.append(response.json())
    scores = [r["review_summary"]["score"] for r in responses]
    assert len(set(scores)) == 1
    statuses = [r["review_summary"]["status"] for r in responses]
    assert len(set(statuses)) == 1
    task_types = [r["next_task_summary"]["task_type"] for r in responses]
    assert len(set(task_types)) == 1


def test_no_silent_failures():
    response = client.post("/api/v1/lifecycle/submit", data={
        "task_title": "Test",
        "submitted_by": "Tester",
        "github_repo_link": "https://github.com/example/repo",
    })
    assert response.status_code == 422


def test_field_ordering_stable():
    response1 = client.post("/api/v1/lifecycle/submit", data=VALID_FORM)
    product_storage.clear_all()
    response2 = client.post("/api/v1/lifecycle/submit", data={
        **VALID_FORM, "task_title": "Field Order Test Two"
    })
    assert list(response1.json().keys()) == list(response2.json().keys())
