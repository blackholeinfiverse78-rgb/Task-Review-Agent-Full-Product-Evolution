#!/usr/bin/env python3
"""
Live Task Review Agent - Scoring Test Script
Demonstrates PASS, BORDERLINE, and FAIL scoring scenarios
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from evaluation_engine.title_analyzer import TitleAnalyzer
from evaluation_engine.description_analyzer import DescriptionAnalyzer
from evaluation_engine.repository_analyzer import RepositoryAnalyzer
from app.services.scoring_engine import ScoringEngine

def test_pass_scenario():
    """Test case designed to achieve PASS score (80+ points)"""
    print("🎯 TEST CASE 1: PASS Score (Target: 80-90 points)")
    print("=" * 60)
    
    title = "REST API Authentication System with JWT and Database Integration"
    description = """Comprehensive authentication system implementation featuring:

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

Complete with comprehensive testing suite and documentation."""

    # Analyze components
    title_analyzer = TitleAnalyzer()
    desc_analyzer = DescriptionAnalyzer()
    scoring_engine = ScoringEngine()
    
    title_result = title_analyzer.analyze(title, description)
    desc_result = desc_analyzer.analyze(description)
    
    # Mock repository analysis for high-quality repo
    repo_result = {
        'repository_score': 32.5,
        'metrics': {
            'code_quality': 0.85,
            'architecture_score': 0.80,
            'documentation_quality': 0.75,
            'file_structure_score': 0.90
        }
    }
    
    total_score = title_result['title_score'] + desc_result['description_score'] + repo_result['repository_score']
    status = scoring_engine.classify_score(total_score)
    
    print(f"Title: {title}")
    print(f"Description Length: {len(description)} characters")
    print()
    print("SCORING BREAKDOWN:")
    print(f"📝 Title Analysis: {title_result['title_score']:.1f}/20 points")
    print(f"   - Technical Keywords: {len(title_result['signals']['technical_terms_found'])}")
    print(f"   - Word Count: {title_result['metrics']['title_word_count']}")
    print(f"   - Alignment Score: {title_result['metrics']['alignment_score']:.3f}")
    print()
    print(f"📄 Description Analysis: {desc_result['description_score']:.1f}/40 points")
    print(f"   - Word Count: {desc_result['metrics']['word_count']}")
    print(f"   - Technical Terms: {len(desc_result['signals']['technical_terms_found'])}")
    print(f"   - Structure Score: {desc_result['metrics']['structure_score']:.3f}")
    print()
    print(f"🏗️ Repository Analysis: {repo_result['repository_score']:.1f}/40 points")
    print(f"   - Code Quality: {repo_result['metrics']['code_quality']:.2f}")
    print(f"   - Architecture: {repo_result['metrics']['architecture_score']:.2f}")
    print(f"   - Documentation: {repo_result['metrics']['documentation_quality']:.2f}")
    print()
    print(f"🎯 TOTAL SCORE: {total_score:.1f}/100")
    print(f"📊 STATUS: {status}")
    print()

def test_borderline_scenario():
    """Test case designed to achieve BORDERLINE score (50-79 points)"""
    print("⚠️ TEST CASE 2: BORDERLINE Score (Target: 50-70 points)")
    print("=" * 60)
    
    title = "User Login System"
    description = """Built a basic login system for users. The system allows users to register and login with username and password. Used some security features and database to store user information. The frontend has forms for registration and login. Backend handles the authentication process.

Features:
- User registration
- User login
- Password storage
- Basic security

Technology used: JavaScript, HTML, CSS, Node.js, and database."""

    # Analyze components
    title_analyzer = TitleAnalyzer()
    desc_analyzer = DescriptionAnalyzer()
    scoring_engine = ScoringEngine()
    
    title_result = title_analyzer.analyze(title, description)
    desc_result = desc_analyzer.analyze(description)
    
    # Mock repository analysis for medium-quality repo
    repo_result = {
        'repository_score': 22.0,
        'metrics': {
            'code_quality': 0.60,
            'architecture_score': 0.50,
            'documentation_quality': 0.45,
            'file_structure_score': 0.65
        }
    }
    
    total_score = title_result['title_score'] + desc_result['description_score'] + repo_result['repository_score']
    status = scoring_engine.classify_score(total_score)
    
    print(f"Title: {title}")
    print(f"Description Length: {len(description)} characters")
    print()
    print("SCORING BREAKDOWN:")
    print(f"📝 Title Analysis: {title_result['title_score']:.1f}/20 points")
    print(f"   - Technical Keywords: {len(title_result['signals']['technical_terms_found'])}")
    print(f"   - Word Count: {title_result['metrics']['title_word_count']}")
    print(f"   - Alignment Score: {title_result['metrics']['alignment_score']:.3f}")
    print()
    print(f"📄 Description Analysis: {desc_result['description_score']:.1f}/40 points")
    print(f"   - Word Count: {desc_result['metrics']['word_count']}")
    print(f"   - Technical Terms: {len(desc_result['signals']['technical_terms_found'])}")
    print(f"   - Structure Score: {desc_result['metrics']['structure_score']:.3f}")
    print()
    print(f"🏗️ Repository Analysis: {repo_result['repository_score']:.1f}/40 points")
    print(f"   - Code Quality: {repo_result['metrics']['code_quality']:.2f}")
    print(f"   - Architecture: {repo_result['metrics']['architecture_score']:.2f}")
    print(f"   - Documentation: {repo_result['metrics']['documentation_quality']:.2f}")
    print()
    print(f"🎯 TOTAL SCORE: {total_score:.1f}/100")
    print(f"📊 STATUS: {status}")
    print()

def test_fail_scenario():
    """Test case designed to achieve FAIL score (< 50 points)"""
    print("❌ TEST CASE 3: FAIL Score (Target: 20-40 points)")
    print("=" * 60)
    
    title = "My Project"
    description = "I made a website. It works and has some features. Users can do things on it. I used some programming languages to build it."

    # Analyze components
    title_analyzer = TitleAnalyzer()
    desc_analyzer = DescriptionAnalyzer()
    scoring_engine = ScoringEngine()
    
    title_result = title_analyzer.analyze(title, description)
    desc_result = desc_analyzer.analyze(description)
    
    # Mock repository analysis for low-quality repo
    repo_result = {
        'repository_score': 8.5,
        'metrics': {
            'code_quality': 0.25,
            'architecture_score': 0.15,
            'documentation_quality': 0.10,
            'file_structure_score': 0.30
        }
    }
    
    total_score = title_result['title_score'] + desc_result['description_score'] + repo_result['repository_score']
    status = scoring_engine.classify_score(total_score)
    
    print(f"Title: {title}")
    print(f"Description Length: {len(description)} characters")
    print()
    print("SCORING BREAKDOWN:")
    print(f"📝 Title Analysis: {title_result['title_score']:.1f}/20 points")
    print(f"   - Technical Keywords: {len(title_result['signals']['technical_terms_found'])}")
    print(f"   - Word Count: {title_result['metrics']['title_word_count']}")
    print(f"   - Alignment Score: {title_result['metrics']['alignment_score']:.3f}")
    print()
    print(f"📄 Description Analysis: {desc_result['description_score']:.1f}/40 points")
    print(f"   - Word Count: {desc_result['metrics']['word_count']}")
    print(f"   - Technical Terms: {len(desc_result['signals']['technical_terms_found'])}")
    print(f"   - Structure Score: {desc_result['metrics']['structure_score']:.3f}")
    print()
    print(f"🏗️ Repository Analysis: {repo_result['repository_score']:.1f}/40 points")
    print(f"   - Code Quality: {repo_result['metrics']['code_quality']:.2f}")
    print(f"   - Architecture: {repo_result['metrics']['architecture_score']:.2f}")
    print(f"   - Documentation: {repo_result['metrics']['documentation_quality']:.2f}")
    print()
    print(f"🎯 TOTAL SCORE: {total_score:.1f}/100")
    print(f"📊 STATUS: {status}")
    print()

def main():
    """Run all test scenarios"""
    print("🧪 LIVE TASK REVIEW AGENT - SCORING TEST SCENARIOS")
    print("=" * 80)
    print("Testing dynamic scoring model with three classification levels")
    print()
    
    test_pass_scenario()
    test_borderline_scenario()
    test_fail_scenario()
    
    print("📋 SUMMARY:")
    print("- PASS (≥80): Comprehensive technical content with clear structure")
    print("- BORDERLINE (50-79): Basic technical content with moderate detail")
    print("- FAIL (<50): Vague content with minimal technical information")
    print()
    print("🎯 Key Success Factors:")
    print("1. Technical keywords in title (API, database, authentication, etc.)")
    print("2. Detailed description with structure (headers, lists, steps)")
    print("3. Well-organized repository with documentation")

if __name__ == "__main__":
    main()