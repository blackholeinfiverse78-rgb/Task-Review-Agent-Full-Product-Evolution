import pytest
from evaluation_engine.review_engine import ReviewEngine
from contracts.schemas import Task
from datetime import datetime


def test_deterministic_scoring_full():
    """High-quality title+description should score well (BORDERLINE or PASS)"""
    engine = ReviewEngine()
    task = Task(
        task_id="test-score-1",
        task_title="REST API Authentication System with JWT and Database Integration",
        task_description="""Comprehensive authentication system implementation featuring:

## Core Features
- JWT token-based authentication with refresh tokens
- Secure password hashing using bcrypt
- Database integration with user management
- Role-based access control (RBAC)
- API rate limiting and security middleware

## Technical Stack
- Backend: Node.js with Express framework
- Database: PostgreSQL with Sequelize ORM
- Authentication: JWT with passport.js
- Security: Helmet.js, CORS, input validation

## Implementation Steps
1. Database schema design for users and roles
2. Authentication middleware development
3. JWT token generation and validation
4. Password encryption and verification
5. API endpoint protection and testing

## Architecture
Follows MVC pattern with clear separation:
- Controllers: Handle HTTP requests
- Services: Business logic implementation
- Models: Database entity definitions
- Middleware: Authentication and validation

Complete with comprehensive testing suite and documentation.""",
        submitted_by="Tester",
        timestamp=datetime.now()
    )
    result = engine.review_task(task)
    assert result.score >= 30, f"Expected >= 30, got {result.score}"
    assert result.status in ("pass", "borderline", "fail")


def test_deterministic_scoring_minimal():
    """Minimal vague input should score low (FAIL)"""
    engine = ReviewEngine()
    task = Task(
        task_id="test-score-2",
        task_title="My Project",
        task_description="I made a website. It works.",
        submitted_by="Tester",
        timestamp=datetime.now()
    )
    result = engine.review_task(task)
    assert result.score < 50, f"Expected < 50, got {result.score}"
    assert result.status == "fail"


def test_scoring_is_deterministic():
    """Same input must produce same score every time"""
    engine = ReviewEngine()
    task = Task(
        task_id="test-det",
        task_title="Build REST API with JWT Authentication",
        task_description="Create a secure REST API using JWT tokens for authentication with bcrypt password hashing and PostgreSQL database.",
        submitted_by="Tester",
        timestamp=datetime.now()
    )
    scores = [engine.review_task(task).score for _ in range(5)]
    assert len(set(scores)) == 1, f"Score variance: {set(scores)}"


def test_fail_has_failure_reasons():
    """FAIL status submissions must have failure_reasons populated"""
    engine = ReviewEngine()
    task = Task(
        task_id="test-fail",
        task_title="Fix bugs",
        task_description="Fix the issues in the code.",
        submitted_by="Dev",
        timestamp=datetime.now()
    )
    result = engine.review_task(task)
    assert result.status == "fail"
    assert len(result.failure_reasons) > 0
