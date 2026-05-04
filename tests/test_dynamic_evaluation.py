"""
Test Dynamic Evaluation Engine
Verifies deterministic behavior and dynamic scoring
"""
import pytest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.evaluation_engine import EvaluationEngine
from evaluation_engine.title_analyzer import TitleAnalyzer
from evaluation_engine.description_analyzer import DescriptionAnalyzer
from app.services.scoring_engine import ScoringEngine

class TestDynamicEvaluationEngine:
    def setup_method(self):
        self.engine = EvaluationEngine()
        
    def test_title_analyzer_deterministic(self):
        """Test title analyzer produces consistent results"""
        analyzer = TitleAnalyzer()
        title = "Build REST API with JWT Authentication"
        description = "Create a secure REST API using JWT tokens for authentication with bcrypt password hashing"
        
        # Run analysis multiple times
        results = [analyzer.analyze(title, description) for _ in range(5)]
        
        # All results should be identical
        first_result = results[0]
        for result in results[1:]:
            assert result['title_score'] == first_result['title_score']
            assert result['metrics'] == first_result['metrics']
            
    def test_description_analyzer_deterministic(self):
        """Test description analyzer produces consistent results"""
        analyzer = DescriptionAnalyzer()
        description = """
        Objective: Build a secure user authentication system
        Requirements:
        1. JWT token-based authentication
        2. Password hashing with bcrypt
        3. Email validation
        
        Technical Stack:
        - FastAPI framework
        - PostgreSQL database
        - Redis for session management
        
        Implementation Steps:
        1. Set up database models
        2. Create authentication endpoints
        3. Implement JWT token generation
        4. Add password hashing utilities
        """
        
        # Run analysis multiple times
        results = [analyzer.analyze(description) for _ in range(5)]
        
        # All results should be identical
        first_result = results[0]
        for result in results[1:]:
            assert result['description_score'] == first_result['description_score']
            assert result['metrics'] == first_result['metrics']
            
    def test_scoring_engine_deterministic(self):
        """Test scoring engine produces consistent final scores"""
        engine = ScoringEngine()
        
        # Mock analysis results
        title_analysis = {
            'title_score': 16.5,
            'metrics': {'title_word_count': 8, 'technical_keyword_ratio': 0.375}
        }
        
        description_analysis = {
            'description_score': 32.8,
            'metrics': {'word_count': 150, 'technical_term_ratio': 0.25}
        }
        
        repo_analysis = {
            'repository_score': 28.4,
            'metrics': {'commit_count': 25, 'code_file_count': 12}
        }
        
        # Run scoring multiple times
        results = [engine.calculate_final_score(title_analysis, description_analysis, repo_analysis) for _ in range(5)]
        
        # All results should be identical
        first_result = results[0]
        for result in results[1:]:
            assert result['final_score'] == first_result['final_score']
            assert result['classification'] == first_result['classification']
            assert result['score_breakdown'] == first_result['score_breakdown']
            
    def test_evaluation_engine_complete_flow(self):
        """Test complete evaluation flow"""
        title = "Build Microservice Authentication System"
        description = """
        Objective: Develop a scalable microservice for user authentication
        
        Requirements:
        - JWT token generation and validation
        - OAuth2 integration
        - Rate limiting for security
        - Database persistence with PostgreSQL
        
        Technical Implementation:
        1. FastAPI framework setup
        2. Database models and migrations
        3. Authentication endpoints
        4. Token management utilities
        5. Security middleware
        
        Testing Strategy:
        - Unit tests for all endpoints
        - Integration tests for database
        - Security penetration testing
        """
        
        # Test without repository (should still work)
        result = self.engine.evaluate(title, description)
        
        assert 'final_score' in result
        assert 'classification' in result
        assert 'score_breakdown' in result
        assert 'signals' in result
        
        # Score should be deterministic
        result2 = self.engine.evaluate(title, description)
        assert result['final_score'] == result2['final_score']
        
    def test_score_classification_thresholds(self):
        """Test score classification boundaries"""
        engine = ScoringEngine()
        
        # Test FAIL threshold (< 50)
        title_analysis = {'title_score': 8.0, 'metrics': {}}
        desc_analysis = {'description_score': 15.0, 'metrics': {}}
        repo_analysis = {'repository_score': 20.0, 'metrics': {}}
        
        result = engine.calculate_final_score(title_analysis, desc_analysis, repo_analysis)
        assert result['classification'] == 'FAIL'
        
        # Test BORDERLINE threshold (50-74)
        title_analysis = {'title_score': 15.0, 'metrics': {}}
        desc_analysis = {'description_score': 25.0, 'metrics': {}}
        repo_analysis = {'repository_score': 25.0, 'metrics': {}}
        
        result = engine.calculate_final_score(title_analysis, desc_analysis, repo_analysis)
        assert result['classification'] == 'BORDERLINE'
        
        # Test PASS threshold (>= 75)
        title_analysis = {'title_score': 18.0, 'metrics': {}}
        desc_analysis = {'description_score': 35.0, 'metrics': {}}
        repo_analysis = {'repository_score': 32.0, 'metrics': {}}
        
        result = engine.calculate_final_score(title_analysis, desc_analysis, repo_analysis)
        assert result['classification'] == 'PASS'
        
    def test_technical_keyword_detection(self):
        """Test technical keyword detection in title and description"""
        title_analyzer = TitleAnalyzer()
        
        # High technical content
        tech_title = "Build REST API with JWT Authentication and Docker Deployment"
        tech_desc = "Implement microservice using FastAPI, PostgreSQL, Redis, and Kubernetes"
        
        result = title_analyzer.analyze(tech_title, tech_desc)
        assert result['metrics']['technical_keyword_ratio'] > 0.3
        
        # Low technical content
        simple_title = "Create a simple web application"
        simple_desc = "Build a basic website with some forms and pages"
        
        result2 = title_analyzer.analyze(simple_title, simple_desc)
        assert result2['metrics']['technical_keyword_ratio'] <= 0.2
        
    def test_no_repository_handling(self):
        """Test evaluation without repository URL"""
        title = "Build Authentication API"
        description = "Create JWT-based authentication with FastAPI and PostgreSQL"
        
        result = self.engine.evaluate(title, description, None)
        
        assert result['score_breakdown']['repository'] == 0
        
    def test_determinism_guarantee(self):
        """Test that identical inputs produce identical outputs"""
        title = "Develop Cloud-Native Microservice Architecture"
        description = """
        Objective: Design and implement a scalable microservice architecture
        
        Technical Requirements:
        - Container orchestration with Kubernetes
        - Service mesh with Istio
        - API Gateway integration
        - Distributed tracing
        - Circuit breaker patterns
        
        Implementation Steps:
        1. Service decomposition analysis
        2. API contract definition
        3. Database per service pattern
        4. Event-driven communication
        5. Monitoring and observability
        """
        
        # Run evaluation 10 times
        results = []
        for i in range(10):
            result = self.engine.evaluate(title, description)
            results.append(result)
        
        # All results must be identical
        first_result = results[0]
        for i, result in enumerate(results[1:], 1):
            assert result['final_score'] == first_result['final_score'], f"Score mismatch at iteration {i}"
            assert result['classification'] == first_result['classification'], f"Classification mismatch at iteration {i}"
            assert result['score_breakdown'] == first_result['score_breakdown'], f"Breakdown mismatch at iteration {i}"
            
if __name__ == "__main__":
    pytest.main([__file__, "-v"])