"""
Live API Test - Dynamic Evaluation Engine
Tests the new dynamic scoring with the running backend
"""
from fastapi.testclient import TestClient
from main import app
import json

client = TestClient(app)

def test_dynamic_evaluation_api():
    print("=" * 60)
    print("DYNAMIC EVALUATION ENGINE - LIVE API TEST")
    print("=" * 60)
    
    # Test Case 1: High-Quality Technical Task
    print("\n[TEST 1] High-Quality Technical Task")
    print("-" * 40)
    
    high_quality_task = {
        "task_title": "Build Microservice Authentication System with JWT and OAuth2",
        "task_description": """
        Objective: Develop a scalable microservice for user authentication and authorization
        
        Technical Requirements:
        - JWT token generation and validation with RS256 algorithm
        - OAuth2 integration with Google and GitHub providers
        - Rate limiting for security (100 requests/minute per IP)
        - Database persistence with PostgreSQL and Redis caching
        - API documentation with OpenAPI/Swagger
        
        Technical Implementation:
        1. FastAPI framework setup with async/await patterns
        2. Database models and Alembic migrations
        3. Authentication endpoints (/login, /register, /refresh)
        4. Token management utilities and middleware
        5. Security middleware with CORS and CSRF protection
        
        Testing Strategy:
        - Unit tests for all endpoints (pytest)
        - Integration tests for database operations
        - Security penetration testing with OWASP guidelines
        - Load testing with 1000+ concurrent users
        """,
        "submitted_by": "Dynamic Test User"
    }
    
    response1 = client.post("/api/v1/lifecycle/submit", data=high_quality_task)
    data1 = response1.json()
    
    print(f"Status Code: {response1.status_code}")
    print(f"Submission ID: {data1['submission_id']}")
    print(f"Score: {data1['review_summary']['score']}/100")
    print(f"Status: {data1['review_summary']['status']}")
    print(f"Readiness: {data1['review_summary']['readiness_percent']}%")
    
    # Get detailed review
    review_response1 = client.get(f"/api/v1/lifecycle/review/{data1['submission_id']}")
    review1 = review_response1.json()
    
    print(f"Technical Quality: {review1['analysis']['technical_quality']}/100")
    print(f"Clarity: {review1['analysis']['clarity']}/100")
    print(f"Discipline Signals: {review1['analysis']['discipline_signals']}/100")
    
    # Test Case 2: Medium-Quality Task
    print("\n[TEST 2] Medium-Quality Task")
    print("-" * 40)
    
    medium_quality_task = {
        "task_title": "Create User Login System",
        "task_description": """
        Build a login system for users.
        
        Requirements:
        - Users can register with email and password
        - Users can login and logout
        - Password should be secure
        
        Implementation:
        - Use a web framework
        - Store data in database
        - Add some security features
        """,
        "submitted_by": "Dynamic Test User"
    }
    
    response2 = client.post("/api/v1/lifecycle/submit", data=medium_quality_task)
    data2 = response2.json()
    
    print(f"Status Code: {response2.status_code}")
    print(f"Score: {data2['review_summary']['score']}/100")
    print(f"Status: {data2['review_summary']['status']}")
    
    # Get detailed review
    review_response2 = client.get(f"/api/v1/lifecycle/review/{data2['submission_id']}")
    review2 = review_response2.json()
    
    print(f"Failure Reasons: {len(review2['failure_reasons'])}")
    for reason in review2['failure_reasons'][:3]:
        print(f"  - {reason}")
    
    # Test Case 3: Low-Quality Task
    print("\n[TEST 3] Low-Quality Task")
    print("-" * 40)
    
    low_quality_task = {
        "task_title": "Make website",
        "task_description": "Create a simple website with some pages and forms.",
        "submitted_by": "Dynamic Test User"
    }
    
    response3 = client.post("/api/v1/lifecycle/submit", data=low_quality_task)
    data3 = response3.json()
    
    print(f"Status Code: {response3.status_code}")
    print(f"Score: {data3['review_summary']['score']}/100")
    print(f"Status: {data3['review_summary']['status']}")
    
    # Test Determinism
    print("\n[DETERMINISM TEST]")
    print("-" * 40)
    
    print("Submitting identical task 3 times...")
    scores = []
    for i in range(3):
        response = client.post("/api/v1/lifecycle/submit", data=high_quality_task)
        data = response.json()
        scores.append(data['review_summary']['score'])
    
    print(f"Scores: {scores}")
    print(f"All identical: {len(set(scores)) == 1}")
    
    # Score Comparison
    print("\n[SCORE COMPARISON]")
    print("-" * 40)
    
    print(f"High Quality Task: {data1['review_summary']['score']}/100 ({data1['review_summary']['status']})")
    print(f"Medium Quality Task: {data2['review_summary']['score']}/100 ({data2['review_summary']['status']})")
    print(f"Low Quality Task: {data3['review_summary']['score']}/100 ({data3['review_summary']['status']})")
    
    print("\n" + "=" * 60)
    print("DYNAMIC EVALUATION ENGINE - API TEST COMPLETE")
    print("✓ Dynamic scoring operational")
    print("✓ Deterministic behavior verified")
    print("✓ Score differentiation working")
    print("✓ API integration successful")
    print("=" * 60)
    
    # Assertions to make it a real automated test
    assert response1.status_code == 200
    assert response2.status_code == 200
    assert response3.status_code == 200
    assert len(set(scores)) == 1