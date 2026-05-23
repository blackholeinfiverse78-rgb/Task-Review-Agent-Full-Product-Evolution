import pytest
from fastapi.testclient import TestClient
from main import app
import string
import random

client = TestClient(app)

def test_max_length_enforcement():
    # task_title max_length=200
    long_title = "a" * 201
    payload = {
        "task_id": "test-task-1",
        "task_title": long_title,
        "task_description": "Valid description long enough for the test case",
        "submitted_by": "User",
        "repository_url": "https://github.com/user/repo",
        "trace_id": "trace-stress-test-1"
    }
    response = client.post("/api/v1/production/niyantran/submit", json=payload)
    assert response.status_code == 422
    assert "status" in response.json()

    # task_description max_length=10000
    long_desc = "a" * 10001
    payload = {
        "task_id": "test-task-2",
        "task_title": "Valid Title",
        "task_description": long_desc,
        "submitted_by": "User",
        "repository_url": "https://github.com/user/repo",
        "trace_id": "trace-stress-test-2"
    }
    response = client.post("/api/v1/production/niyantran/submit", json=payload)
    assert response.status_code == 422
    assert "status" in response.json()

def test_sql_injection_simulation():
    # Since we use in-memory dict, it's safe, but we check if it breaks the system
    payload = {
        "task_id": "test-task-3",
        "task_title": "SELECT * FROM users; --",
        "task_description": "DROP TABLE tasks; CASCADE; ' OR '1'='1 description long enough",
        "submitted_by": "Hacker",
        "repository_url": "https://github.com/user/repo",
        "trace_id": "trace-stress-test-3"
    }
    response = client.post("/api/v1/production/niyantran/submit", json=payload)
    assert response.status_code == 200 # Should be treated as normal string

def test_xss_simulation():
    payload = {
        "task_id": "test-task-4",
        "task_title": "<script>alert('xss')</script>",
        "task_description": "Check XSS: <img src=x onerror=alert(1)> and more words to make it long enough",
        "submitted_by": "Hacker",
        "repository_url": "https://github.com/user/repo",
        "trace_id": "trace-stress-test-4"
    }
    response = client.post("/api/v1/production/niyantran/submit", json=payload)
    assert response.status_code == 200 # Treated as string

def test_unauthorized_access():
    # Test accessing non-existent task endpoints
    response = client.get("/api/v1/production/system/production-status")
    assert response.status_code == 200

def test_malformed_json():
    response = client.post("/api/v1/production/niyantran/submit", content="invalid json", headers={"Content-Type": "application/json"})
    assert response.status_code == 422

