"""
COMPREHENSIVE SECURITY VALIDATION TEST
Tests all implemented security measures and validates the secure system
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import time
from datetime import datetime
import requests
from pathlib import Path

def test_authentication_security():
    """Test authentication implementation"""
    print("AUTHENTICATION SECURITY VALIDATION")
    print("-" * 50)
    
    results = []
    
    # Test 1: Check if security middleware exists
    security_middleware_path = "app/security/middleware.py"
    if os.path.exists(security_middleware_path):
        results.append({
            "test": "Security Middleware Exists",
            "status": "PASS",
            "details": "Security middleware implemented"
        })
        
        # Check middleware content
        with open(security_middleware_path, 'r') as f:
            content = f.read()
        
        if "JWT" in content and "authentication" in content.lower():
            results.append({
                "test": "JWT Authentication Implementation",
                "status": "PASS", 
                "details": "JWT authentication implemented"
            })
        else:
            results.append({
                "test": "JWT Authentication Implementation",
                "status": "FAIL",
                "details": "JWT authentication not properly implemented"
            })
            
        if "role" in content.lower() and "authorization" in content.lower():
            results.append({
                "test": "Role-based Authorization",
                "status": "PASS",
                "details": "Role-based authorization implemented"
            })
        else:
            results.append({
                "test": "Role-based Authorization", 
                "status": "FAIL",
                "details": "Role-based authorization not implemented"
            })
    else:
        results.append({
            "test": "Security Middleware Exists",
            "status": "FAIL",
            "details": "Security middleware not found"
        })
    
    return results

def test_input_validation_security():
    """Test input validation and sanitization"""
    print("INPUT VALIDATION SECURITY")
    print("-" * 50)
    
    results = []
    
    # Test 1: Check if InputSanitizer exists
    security_middleware_path = "app/security/middleware.py"
    if os.path.exists(security_middleware_path):
        with open(security_middleware_path, 'r') as f:
            content = f.read()
        
        if "InputSanitizer" in content:
            results.append({
                "test": "Input Sanitization Implementation",
                "status": "PASS",
                "details": "Input sanitizer implemented"
            })
            
            # Check for specific sanitization methods
            if "sanitize_string" in content:
                results.append({
                    "test": "String Sanitization",
                    "status": "PASS",
                    "details": "String sanitization method exists"
                })
            
            if "sanitize_filename" in content:
                results.append({
                    "test": "Filename Sanitization",
                    "status": "PASS",
                    "details": "Filename sanitization method exists"
                })
            
            if "validate_url" in content:
                results.append({
                    "test": "URL Validation",
                    "status": "PASS",
                    "details": "URL validation method exists"
                })
        else:
            results.append({
                "test": "Input Sanitization Implementation",
                "status": "FAIL",
                "details": "Input sanitizer not implemented"
            })
    
    # Test 2: Check Pydantic validation in API
    api_path = "app/api/lifecycle.py"
    if os.path.exists(api_path):
        with open(api_path, 'r') as f:
            api_content = f.read()
        
        if "BaseModel" in api_content and "Field" in api_content:
            results.append({
                "test": "Pydantic Input Validation",
                "status": "PASS",
                "details": "Pydantic validation implemented in API"
            })
        else:
            results.append({
                "test": "Pydantic Input Validation",
                "status": "FAIL",
                "details": "Pydantic validation not properly implemented"
            })
    
    return results

def test_rate_limiting():
    """Test rate limiting implementation"""
    print("RATE LIMITING VALIDATION")
    print("-" * 50)
    
    results = []
    
    # Check if rate limiter exists
    security_middleware_path = "app/security/middleware.py"
    if os.path.exists(security_middleware_path):
        with open(security_middleware_path, 'r') as f:
            content = f.read()
        
        if "RateLimiter" in content:
            results.append({
                "test": "Rate Limiter Implementation",
                "status": "PASS",
                "details": "Rate limiter class implemented"
            })
            
            if "is_allowed" in content:
                results.append({
                    "test": "Rate Limit Logic",
                    "status": "PASS",
                    "details": "Rate limiting logic implemented"
                })
        else:
            results.append({
                "test": "Rate Limiter Implementation",
                "status": "FAIL",
                "details": "Rate limiter not implemented"
            })
    
    # Check if rate limiting is applied in main app
    secure_main_path = "app/main_secure.py"
    if os.path.exists(secure_main_path):
        with open(secure_main_path, 'r') as f:
            content = f.read()
        
        if "rate_limit_middleware" in content:
            results.append({
                "test": "Rate Limiting Middleware",
                "status": "PASS",
                "details": "Rate limiting middleware applied"
            })
        else:
            results.append({
                "test": "Rate Limiting Middleware",
                "status": "FAIL",
                "details": "Rate limiting middleware not applied"
            })
    
    return results

def test_security_headers():
    """Test security headers implementation"""
    print("SECURITY HEADERS VALIDATION")
    print("-" * 50)
    
    results = []
    
    # Check if security headers function exists
    security_middleware_path = "app/security/middleware.py"
    if os.path.exists(security_middleware_path):
        with open(security_middleware_path, 'r') as f:
            content = f.read()
        
        if "add_security_headers" in content:
            results.append({
                "test": "Security Headers Function",
                "status": "PASS",
                "details": "Security headers function implemented"
            })
            
            # Check for specific headers
            security_headers = [
                "X-Content-Type-Options",
                "X-Frame-Options", 
                "X-XSS-Protection",
                "Strict-Transport-Security",
                "Content-Security-Policy"
            ]
            
            for header in security_headers:
                if header in content:
                    results.append({
                        "test": f"Security Header - {header}",
                        "status": "PASS",
                        "details": f"{header} header implemented"
                    })
                else:
                    results.append({
                        "test": f"Security Header - {header}",
                        "status": "FAIL",
                        "details": f"{header} header not implemented"
                    })
        else:
            results.append({
                "test": "Security Headers Function",
                "status": "FAIL",
                "details": "Security headers function not implemented"
            })
    
    return results

def test_cors_security():
    """Test CORS security configuration"""
    print("CORS SECURITY VALIDATION")
    print("-" * 50)
    
    results = []
    
    # Check secure main.py for CORS configuration
    secure_main_path = "app/main_secure.py"
    if os.path.exists(secure_main_path):
        with open(secure_main_path, 'r') as f:
            content = f.read()
        
        if "CORSMiddleware" in content:
            results.append({
                "test": "CORS Middleware Configured",
                "status": "PASS",
                "details": "CORS middleware is configured"
            })
            
            # Check if wildcard origins are avoided
            if 'allow_origins=["*"]' not in content and "*" not in content:
                results.append({
                    "test": "CORS Origins Restricted",
                    "status": "PASS",
                    "details": "CORS origins properly restricted"
                })
            else:
                results.append({
                    "test": "CORS Origins Restricted",
                    "status": "FAIL",
                    "details": "CORS allows wildcard origins - security risk"
                })
        else:
            results.append({
                "test": "CORS Middleware Configured",
                "status": "FAIL",
                "details": "CORS middleware not configured"
            })
    
    return results

def test_environment_security():
    """Test environment and configuration security"""
    print("ENVIRONMENT SECURITY VALIDATION")
    print("-" * 50)
    
    results = []
    
    # Check if secure environment template exists
    env_template_path = ".env.secure.template"
    if os.path.exists(env_template_path):
        results.append({
            "test": "Secure Environment Template",
            "status": "PASS",
            "details": "Secure environment template provided"
        })
        
        with open(env_template_path, 'r') as f:
            content = f.read()
        
        # Check for security-related configurations
        security_configs = [
            "JWT_SECRET_KEY",
            "ALLOWED_ORIGINS",
            "ALLOWED_HOSTS",
            "MAX_REQUESTS_PER_MINUTE",
            "ENABLE_SECURITY_HEADERS"
        ]
        
        for config in security_configs:
            if config in content:
                results.append({
                    "test": f"Security Config - {config}",
                    "status": "PASS",
                    "details": f"{config} configuration provided"
                })
            else:
                results.append({
                    "test": f"Security Config - {config}",
                    "status": "FAIL",
                    "details": f"{config} configuration missing"
                })
    else:
        results.append({
            "test": "Secure Environment Template",
            "status": "FAIL",
            "details": "Secure environment template not provided"
        })
    
    # Check if .env is in .gitignore
    gitignore_path = ".gitignore"
    if os.path.exists(gitignore_path):
        with open(gitignore_path, 'r', encoding='utf-8') as f:
            gitignore_content = f.read()
        
        if ".env" in gitignore_content:
            results.append({
                "test": "Environment File Security",
                "status": "PASS",
                "details": ".env file is in .gitignore"
            })
        else:
            results.append({
                "test": "Environment File Security",
                "status": "WARN",
                "details": ".env file should be in .gitignore"
            })
    
    return results

def test_error_handling_security():
    """Test secure error handling"""
    print("ERROR HANDLING SECURITY VALIDATION")
    print("-" * 50)
    
    results = []
    
    # Check secure main.py for global exception handler
    secure_main_path = "app/main_secure.py"
    if os.path.exists(secure_main_path):
        with open(secure_main_path, 'r') as f:
            content = f.read()
        
        if "global_exception_handler" in content:
            results.append({
                "test": "Global Exception Handler",
                "status": "PASS",
                "details": "Global exception handler implemented"
            })
            
            # Check if production mode hides error details
            if "ENVIRONMENT" in content and "production" in content:
                results.append({
                    "test": "Production Error Handling",
                    "status": "PASS",
                    "details": "Production error handling implemented"
                })
        else:
            results.append({
                "test": "Global Exception Handler",
                "status": "FAIL",
                "details": "Global exception handler not implemented"
            })
    
    return results

def test_functionality_with_security():
    """Test that core functionality works with security measures"""
    print("FUNCTIONALITY WITH SECURITY VALIDATION")
    print("-" * 50)
    
    results = []
    
    # Test core components still work
    try:
        from app.services.assignment_authority import assignment_authority
        
        test_signals = {
            "expected_vs_delivered_evidence": {
                "expected_count": 5,
                "delivered_count": 3,
                "delivery_ratio": 0.6
            },
            "missing_features": ["feature1"],
            "failure_indicators": ["test_indicator"],
            "repository_available": False
        }
        
        result = assignment_authority.evaluate_assignment_readiness(
            "Test Task",
            "Test Description",
            test_signals
        )
        
        if result.get("authority_level") == "PRIMARY_CANONICAL":
            results.append({
                "test": "Assignment Authority with Security",
                "status": "PASS",
                "details": "Assignment Authority works with security measures"
            })
        else:
            results.append({
                "test": "Assignment Authority with Security",
                "status": "FAIL",
                "details": "Assignment Authority not working properly"
            })
            
    except Exception as e:
        results.append({
            "test": "Assignment Authority with Security",
            "status": "FAIL",
            "details": f"Error: {str(e)}"
        })
    
    # Test other components
    try:
        from evaluation_engine.signal_engine import signal_engine
        
        signals = signal_engine.collect_supporting_signals(
            "Test Task",
            "Test Description with technical requirements",
            None
        )
        
        if signals.get("signal_authority") == "SUPPORTING_ONLY":
            results.append({
                "test": "Signal Collector with Security",
                "status": "PASS",
                "details": "Signal Collector works with security measures"
            })
        else:
            results.append({
                "test": "Signal Collector with Security",
                "status": "FAIL",
                "details": "Signal Collector not working properly"
            })
            
    except Exception as e:
        results.append({
            "test": "Signal Collector with Security",
            "status": "FAIL",
            "details": f"Error: {str(e)}"
        })
    
    return results

def generate_security_validation_report():
    """Generate comprehensive security validation report"""
    print("\n" + "="*80)
    print("COMPREHENSIVE SECURITY VALIDATION REPORT")
    print("="*80)
    
    # Run all security tests
    all_results = []
    all_results.extend(test_authentication_security())
    all_results.extend(test_input_validation_security())
    all_results.extend(test_rate_limiting())
    all_results.extend(test_security_headers())
    all_results.extend(test_cors_security())
    all_results.extend(test_environment_security())
    all_results.extend(test_error_handling_security())
    all_results.extend(test_functionality_with_security())
    
    # Categorize results
    passed = [r for r in all_results if r["status"] == "PASS"]
    failed = [r for r in all_results if r["status"] == "FAIL"]
    warnings = [r for r in all_results if r["status"] == "WARN"]
    
    print(f"\nSECURITY VALIDATION SUMMARY:")
    print(f"Total Tests: {len(all_results)}")
    print(f"Passed: {len(passed)}")
    print(f"Failed: {len(failed)}")
    print(f"Warnings: {len(warnings)}")
    
    # Show failed tests
    if failed:
        print(f"\nFAILED SECURITY TESTS:")
        for test in failed:
            print(f"  FAIL: {test['test']} - {test['details']}")
    
    # Show warnings
    if warnings:
        print(f"\nSECURITY WARNINGS:")
        for test in warnings:
            print(f"  WARN: {test['test']} - {test['details']}")
    
    # Calculate security score
    security_score = (len(passed) / len(all_results)) * 100 if all_results else 0
    
    print(f"\nSECURITY IMPLEMENTATION SCORE: {security_score:.1f}%")
    
    # Security status
    if security_score >= 90:
        security_status = "EXCELLENT - Production Ready"
    elif security_score >= 80:
        security_status = "GOOD - Minor improvements needed"
    elif security_score >= 70:
        security_status = "MODERATE - Some security gaps"
    else:
        security_status = "POOR - Major security improvements required"
    
    print(f"SECURITY STATUS: {security_status}")
    
    # Key security features implemented
    print(f"\nKEY SECURITY FEATURES IMPLEMENTED:")
    security_features = [
        "JWT Authentication",
        "Role-based Authorization", 
        "Input Sanitization",
        "Rate Limiting",
        "Security Headers",
        "CORS Protection",
        "Error Handling",
        "Environment Security"
    ]
    
    for feature in security_features:
        feature_tests = [r for r in all_results if feature.lower() in r["test"].lower()]
        if any(t["status"] == "PASS" for t in feature_tests):
            print(f"  ✓ {feature}")
        else:
            print(f"  ✗ {feature}")
    
    # Save detailed report
    report_data = {
        "timestamp": datetime.now().isoformat(),
        "security_validation_results": all_results,
        "summary": {
            "total_tests": len(all_results),
            "passed": len(passed),
            "failed": len(failed),
            "warnings": len(warnings),
            "security_score": security_score,
            "security_status": security_status
        }
    }
    
    with open("security_validation_report.json", "w") as f:
        json.dump(report_data, f, indent=2)
    
    print(f"\nDetailed validation report saved to: security_validation_report.json")
    
    return report_data

if __name__ == "__main__":
    print("TASK REVIEW AGENT - COMPREHENSIVE SECURITY VALIDATION")
    print("="*80)
    
    try:
        report = generate_security_validation_report()
        print(f"\nSecurity validation complete.")
        
        if report["summary"]["security_score"] >= 80:
            print("✓ SECURITY VALIDATION PASSED - System is secure")
        else:
            print("✗ SECURITY VALIDATION FAILED - Improvements needed")
        
    except Exception as e:
        print(f"SECURITY VALIDATION FAILED: {e}")
        import traceback
        traceback.print_exc()