import pytest
from fastapi.testclient import TestClient
from main import app
import io

client = TestClient(app)

def test_github_review_valid(monkeypatch):
    import requests
    
    class MockResponse:
        def __init__(self, json_data, status_code, headers=None):
            self.json_data = json_data
            self.status_code = status_code
            self.headers = headers or {}
        def json(self): return self.json_data
        def raise_for_status(self): pass

    def mock_get(url, *args, **kwargs):
        if "/repos/fastapi/fastapi/languages" in url:
            return MockResponse({"Python": 100}, 200)
        if "/repos/fastapi/fastapi/commits" in url:
            return MockResponse([{}], 200, {"Link": 'page=50>; rel="last"'})
        if "/git/trees" in url:
            return MockResponse({"tree": [{"path": "README.md", "type": "blob"}]}, 200)
        if "/repos/fastapi/fastapi" in url:
            return MockResponse({"full_name": "fastapi/fastapi", "default_branch": "master", "stargazers_count": 10}, 200)
        return MockResponse({}, 404)

    monkeypatch.setattr(requests, "get", mock_get)

    response = client.post(
        "/api/v1/task/review",
        data={
            "github_url": "https://github.com/fastapi/fastapi",
            "description": "A very long and descriptive project explanation for testing."
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "analysis" in data

def test_github_review_invalid_url():
    response = client.post(
        "/api/v1/task/review",
        data={
            "github_url": "invalid-url",
            "description": "Valid description"
        }
    )
    assert response.status_code == 400
    assert "GitHub repository URL" in response.json()["detail"]

def test_github_review_missing_description():
    response = client.post(
        "/api/v1/task/review",
        data={
            "github_url": "https://github.com/fastapi/fastapi"
        }
    )
    assert response.status_code == 400
    assert "Description is required" in response.json()["detail"]

def test_github_review_not_found(monkeypatch):
    import requests
    class MockResponse:
        def __init__(self, status_code): self.status_code = status_code
        def json(self): return {}
    
    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: MockResponse(404))

    response = client.post(
        "/api/v1/task/review",
        data={
            "github_url": "https://github.com/invalid/repo",
            "description": "Attempting to review a non-existent repository."
        }
    )
    assert response.status_code == 404
    assert "not found or is private" in response.json()["detail"]

def test_pdf_review_valid():
    from reportlab.pdfgen import canvas
    
    # Generate a real valid PDF in memory
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer)
    c.drawString(100, 750, "Requirement: Implement a secure login system.")
    c.drawString(100, 730, "Objective: Protect user data and prevent unauthorized access.")
    c.save()
    
    buffer.seek(0)
    
    response = client.post(
        "/api/v1/task/review",
        files={"pdf_file": ("test.pdf", buffer, "application/pdf")},
        data={"description": "Reviewing this PDF file for testing purpose"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    # The score should be influenced by the extracted text
    assert data["readiness_percent"] >= 0

def test_pdf_review_invalid_type():
    # Simulate a non-PDF upload
    txt_content = b"not a pdf"
    txt_file = io.BytesIO(txt_content)
    
    response = client.post(
        "/api/v1/task/review",
        files={"pdf_file": ("test.txt", txt_file, "text/plain")},
        data={"description": "Should fail as it's not a pdf"}
    )
    assert response.status_code == 400
    assert "Only PDF files are allowed" in response.json()["detail"]

def test_empty_description():
    response = client.post(
        "/api/v1/task/review",
        data={
            "github_url": "https://github.com/user/repo",
            "description": "   "
        }
    )
    assert response.status_code == 400
    # Description fails min_length validation or prevent_empty_whitespace in TaskBase? 
    # ExtendedReviewRequest uses Field(..., min_length=10)
    assert "at least 10 characters" in response.json()["detail"] or "cannot be empty" in response.json()["detail"]
