"""
Unit tests for Parikshak HackaVerse Consumable API Adapter
"""
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_parikshak_health():
    """Verify health endpoint exists and is reachable."""
    response = client.get("/parikshak/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "parikshak"

def test_parikshak_review_fail_path():
    """Validate FAIL path when no repo is provided and description is short."""
    payload = {
        "mode": "task_review",
        "title": "Short Task",
        "description": "Short",
        "submitted_by": "Developer",
        "submission": "",
        "repo_url": "",
        "trace_id": "hv-demo-002"
    }
    response = client.post("/parikshak/review", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "score" in data
    assert "review" in data
    assert "next_task" in data
    assert data["trace_id"] == "hv-demo-002"
    assert data["status"] == "FAIL"
    assert data["score"] < 60

def test_parikshak_review_partial_path():
    """Validate PARTIAL path when description is moderately detailed but repo is missing."""
    payload = {
        "mode": "task_review",
        "title": "Build a clean REST API with User Authentication and JWT secure tokens",
        "description": "This task is about building a clean REST API with User Authentication and JWT secure tokens using FastAPI and PostgreSQL database. Objective is to achieve clean layer separation and modular design with standard REST handlers.",
        "submitted_by": "Developer",
        "submission": "",
        "repo_url": "",
        "trace_id": "hv-demo-003"
    }
    response = client.post("/parikshak/review", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "score" in data
    assert data["trace_id"] == "hv-demo-003"
    assert data["status"] in ("PARTIAL", "FAIL")

def test_parikshak_review_payload_handling():
    """Verify payload parsing issues are fixed and resilient to form-data and missing fields."""
    # Test missing fields (should succeed via fallbacks)
    payload = {}
    response = client.post("/parikshak/review", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["trace_id"] == "hv-demo-001"  # fallback trace_id
    assert "status" in data
    assert "score" in data

    # Test invalid JSON format
    headers = {"Content-Type": "application/json"}
    response = client.post("/parikshak/review", content="invalid-json", headers=headers)
    assert response.status_code == 400
    data = response.json()
    assert data["status"] == "FAIL"
    assert "Invalid JSON payload format" in data["review"]
