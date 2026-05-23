"""
Test scoring components to verify they're working
"""
import sys
import os

# Add paths for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'intelligence-integration-module-main'))

from task_selector.final_convergence import final_convergence

def test_scoring_with_good_task():
    """Test with a well-structured task that should get higher scores"""
    
    result = final_convergence.process_with_convergence(
        task_title="Advanced Microservices Auth API: JWT, OAuth2, RBAC, Rate Limiting, and Docker Containerization",
        task_description="""
        Build a comprehensive enterprise-grade authentication microservice with the following technical requirements:
        
        1. JWT Token Management:
           - Token generation with custom claims
           - Token validation and refresh mechanisms
           - Secure token storage and rotation
        
        2. OAuth2 Integration:
           - Authorization code flow implementation
           - Client credentials management
           - Scope-based access control
        
        3. Role-Based Access Control (RBAC):
           - Dynamic role assignment
           - Permission-based resource access
           - Hierarchical role inheritance
        
        4. Rate Limiting:
           - Token bucket algorithm implementation
           - Per-user and per-endpoint rate limits
           - Redis-based distributed rate limiting
        
        5. Docker Containerization:
           - Multi-stage Docker builds
           - Container orchestration with Docker Compose
           - Health checks and monitoring endpoints
        
        6. Security Features:
           - Password hashing with bcrypt
           - SQL injection prevention
           - CORS configuration
           - Input validation and sanitization
        
        7. Testing and Documentation:
           - Unit tests with 90%+ coverage
           - Integration tests for all endpoints
           - Comprehensive API documentation
           - Deployment guides and examples
        
        Technical Stack: Node.js, Express.js, PostgreSQL, Redis, Docker, Jest
        Architecture: Clean Architecture with dependency injection
        """,
        repository_url="https://github.com/user/enterprise-auth-api",
        module_id="task-review-agent",
        schema_version="v1.0"
    )
    
    print("=" * 60)
    print("SCORING TEST - COMPREHENSIVE TASK")
    print("=" * 60)
    print(f"Title Score: {result.get('supporting_signals', {}).get('technical_signals', {}).get('title_score', 0)}/20")
    print(f"Description Score: {result.get('supporting_signals', {}).get('technical_signals', {}).get('description_score', 0)}/40")
    print(f"Repository Score: {result.get('supporting_signals', {}).get('technical_signals', {}).get('repository_score', 0)}/40")
    print(f"Total Score: {result.get('score', 0)}/100")
    print(f"Status: {result.get('status')}")
    print(f"Task Type: {result.get('task_type')}")
    
    # Show evidence
    evidence = result.get('evidence_summary', {})
    print(f"\nEvidence Summary:")
    print(f"  Expected Features: {evidence.get('expected_features', 0)}")
    print(f"  Delivered Features: {evidence.get('delivered_features', 0)}")
    print(f"  Delivery Ratio: {evidence.get('delivery_ratio', 0.0):.2f}")
    
    return result

if __name__ == "__main__":
    test_scoring_with_good_task()