"""
SECURITY ANALYSIS REPORT - Task Review Agent
Comprehensive security assessment and recommendations
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from datetime import datetime
from pathlib import Path

def analyze_authentication_security():
    """Analyze authentication and authorization security"""
    print("AUTHENTICATION & AUTHORIZATION ANALYSIS")
    print("-" * 50)
    
    issues = []
    
    # Check main.py for authentication middleware
    try:
        with open("app/main.py", 'r') as f:
            main_content = f.read()
        
        if "authentication" not in main_content.lower():
            issues.append({
                "severity": "CRITICAL",
                "issue": "No authentication mechanism implemented",
                "file": "app/main.py",
                "recommendation": "Implement JWT or API key authentication"
            })
        
        if "authorization" not in main_content.lower():
            issues.append({
                "severity": "CRITICAL", 
                "issue": "No authorization mechanism implemented",
                "file": "app/main.py",
                "recommendation": "Implement role-based access control"
            })
            
    except FileNotFoundError:
        issues.append({
            "severity": "HIGH",
            "issue": "Main application file not found",
            "file": "app/main.py",
            "recommendation": "Ensure main.py exists and is properly configured"
        })
    
    return issues

def analyze_input_validation():
    """Analyze input validation security"""
    print("INPUT VALIDATION ANALYSIS")
    print("-" * 50)
    
    issues = []
    
    # Check API endpoints for input validation
    try:
        with open("app/api/lifecycle.py", 'r') as f:
            api_content = f.read()
        
        # Check for Pydantic validation
        if "BaseModel" in api_content and "Field" in api_content:
            print("PASS: Pydantic validation implemented")
        else:
            issues.append({
                "severity": "HIGH",
                "issue": "Insufficient input validation",
                "file": "app/api/lifecycle.py", 
                "recommendation": "Implement comprehensive Pydantic validation"
            })
        
        # Check for SQL injection protection
        if "sql" in api_content.lower() and "execute" in api_content.lower():
            issues.append({
                "severity": "CRITICAL",
                "issue": "Potential SQL injection vulnerability",
                "file": "app/api/lifecycle.py",
                "recommendation": "Use parameterized queries only"
            })
            
    except FileNotFoundError:
        issues.append({
            "severity": "HIGH",
            "issue": "API file not found",
            "file": "app/api/lifecycle.py",
            "recommendation": "Ensure API files exist"
        })
    
    return issues

def analyze_file_upload_security():
    """Analyze file upload security"""
    print("FILE UPLOAD SECURITY ANALYSIS")
    print("-" * 50)
    
    issues = []
    
    # Check PDF analyzer for security
    try:
        with open("app/services/pdf_analyzer.py", 'r') as f:
            pdf_content = f.read()
        
        # Check for file type validation
        if ".pdf" in pdf_content.lower():
            print("PASS: PDF file type validation exists")
        else:
            issues.append({
                "severity": "HIGH",
                "issue": "No file type validation",
                "file": "app/services/pdf_analyzer.py",
                "recommendation": "Implement strict file type validation"
            })
        
        # Check for path traversal protection
        if "../" in pdf_content or "..\\" in pdf_content:
            issues.append({
                "severity": "CRITICAL",
                "issue": "Potential path traversal vulnerability",
                "file": "app/services/pdf_analyzer.py",
                "recommendation": "Sanitize all file paths"
            })
        
        # Check for file size limits
        if "size" not in pdf_content.lower():
            issues.append({
                "severity": "MEDIUM",
                "issue": "No file size limits implemented",
                "file": "app/services/pdf_analyzer.py",
                "recommendation": "Implement file size limits"
            })
            
    except FileNotFoundError:
        issues.append({
            "severity": "MEDIUM",
            "issue": "PDF analyzer not found",
            "file": "app/services/pdf_analyzer.py",
            "recommendation": "Ensure PDF analyzer exists if file upload is supported"
        })
    
    return issues

def analyze_data_exposure():
    """Analyze sensitive data exposure"""
    print("DATA EXPOSURE ANALYSIS")
    print("-" * 50)
    
    issues = []
    
    # Check for .env file
    if os.path.exists(".env"):
        issues.append({
            "severity": "MEDIUM",
            "issue": ".env file present",
            "file": ".env",
            "recommendation": "Ensure .env is in .gitignore and not committed"
        })
    
    # Check for hardcoded secrets
    files_to_check = [
        "app/main.py",
        "app/services/repository_analyzer.py",
        "app/api/lifecycle.py"
    ]
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Check for hardcoded secrets
            secret_patterns = ['password', 'secret', 'key', 'token', 'api_key']
            for pattern in secret_patterns:
                if f'{pattern}=' in content.lower() or f'"{pattern}"' in content.lower():
                    issues.append({
                        "severity": "HIGH",
                        "issue": f"Potential hardcoded {pattern}",
                        "file": file_path,
                        "recommendation": f"Move {pattern} to environment variables"
                    })
    
    return issues

def analyze_cors_security():
    """Analyze CORS configuration"""
    print("CORS SECURITY ANALYSIS")
    print("-" * 50)
    
    issues = []
    
    try:
        with open("app/main.py", 'r') as f:
            main_content = f.read()
        
        if "CORSMiddleware" in main_content:
            if 'allow_origins=["*"]' in main_content:
                issues.append({
                    "severity": "HIGH",
                    "issue": "CORS allows all origins",
                    "file": "app/main.py",
                    "recommendation": "Restrict CORS to specific domains"
                })
            else:
                print("PASS: CORS properly configured")
        else:
            issues.append({
                "severity": "MEDIUM",
                "issue": "No CORS configuration found",
                "file": "app/main.py",
                "recommendation": "Configure CORS middleware"
            })
            
    except FileNotFoundError:
        pass
    
    return issues

def analyze_error_handling():
    """Analyze error handling security"""
    print("ERROR HANDLING ANALYSIS")
    print("-" * 50)
    
    issues = []
    
    # Check for proper error handling
    files_to_check = [
        "app/services/assignment_authority.py",
        "app/services/signal_engine.py",
        "app/api/lifecycle.py"
    ]
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Check for bare except clauses
            if "except:" in content:
                issues.append({
                    "severity": "MEDIUM",
                    "issue": "Bare except clause found",
                    "file": file_path,
                    "recommendation": "Use specific exception handling"
                })
            
            # Check for stack trace exposure
            if "traceback" in content.lower():
                issues.append({
                    "severity": "HIGH",
                    "issue": "Potential stack trace exposure",
                    "file": file_path,
                    "recommendation": "Log errors without exposing stack traces to users"
                })
    
    return issues

def analyze_dependency_security():
    """Analyze dependency security"""
    print("DEPENDENCY SECURITY ANALYSIS")
    print("-" * 50)
    
    issues = []
    
    if os.path.exists("requirements.txt"):
        with open("requirements.txt", 'r') as f:
            requirements = f.read()
        
        # Check for known vulnerable packages (simplified check)
        vulnerable_patterns = [
            ("django<3.2", "Django version may have vulnerabilities"),
            ("flask<2.0", "Flask version may have vulnerabilities"),
            ("requests<2.25", "Requests version may have vulnerabilities"),
            ("urllib3<1.26", "urllib3 version may have vulnerabilities")
        ]
        
        for pattern, description in vulnerable_patterns:
            if pattern.split('<')[0] in requirements.lower():
                issues.append({
                    "severity": "MEDIUM",
                    "issue": description,
                    "file": "requirements.txt",
                    "recommendation": f"Update {pattern.split('<')[0]} to latest version"
                })
    else:
        issues.append({
            "severity": "LOW",
            "issue": "No requirements.txt found",
            "file": "requirements.txt",
            "recommendation": "Create requirements.txt for dependency management"
        })
    
    return issues

def test_core_functionality():
    """Test core functionality"""
    print("CORE FUNCTIONALITY TESTS")
    print("-" * 50)
    
    functionality_results = []
    
    # Test Assignment Authority
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
            functionality_results.append({
                "component": "Assignment Authority",
                "status": "PASS",
                "details": "Working correctly"
            })
        else:
            functionality_results.append({
                "component": "Assignment Authority", 
                "status": "FAIL",
                "details": "Authority level incorrect"
            })
            
    except Exception as e:
        functionality_results.append({
            "component": "Assignment Authority",
            "status": "FAIL", 
            "details": f"Error: {str(e)}"
        })
    
    # Test Signal Collector
    try:
        from evaluation_engine.signal_engine import signal_engine
        
        signals = signal_engine.collect_supporting_signals(
            "Test Task",
            "Test Description with technical requirements",
            None
        )
        
        if signals.get("signal_authority") == "SUPPORTING_ONLY":
            functionality_results.append({
                "component": "Signal Collector",
                "status": "PASS",
                "details": "Working correctly - supporting only"
            })
        else:
            functionality_results.append({
                "component": "Signal Collector",
                "status": "FAIL",
                "details": "Authority level incorrect"
            })
            
    except Exception as e:
        functionality_results.append({
            "component": "Signal Collector",
            "status": "FAIL",
            "details": f"Error: {str(e)}"
        })
    
    # Test Validation Gate
    try:
        from evaluation_engine.shraddha_validation import validation_gate
        
        test_result = {
            "submission_id": "test-123",
            "score": 75,
            "status": "borderline", 
            "readiness_percent": 75,
            "next_task_id": "next-123",
            "task_type": "reinforcement",
            "title": "Test Task",
            "difficulty": "targeted"
        }
        
        validated = validation_gate.validate_final_output(test_result, "test")
        
        if validated.get("validation_metadata", {}).get("validation_level") == "FINAL_AUTHORITATIVE":
            functionality_results.append({
                "component": "Validation Gate",
                "status": "PASS", 
                "details": "Working correctly"
            })
        else:
            functionality_results.append({
                "component": "Validation Gate",
                "status": "FAIL",
                "details": "Validation level incorrect"
            })
            
    except Exception as e:
        functionality_results.append({
            "component": "Validation Gate",
            "status": "FAIL",
            "details": f"Error: {str(e)}"
        })
    
    return functionality_results

def generate_comprehensive_report():
    """Generate comprehensive security and functionality report"""
    print("\n" + "="*80)
    print("COMPREHENSIVE SECURITY & FUNCTIONALITY REPORT")
    print("="*80)
    
    # Collect all security issues
    all_issues = []
    all_issues.extend(analyze_authentication_security())
    all_issues.extend(analyze_input_validation())
    all_issues.extend(analyze_file_upload_security())
    all_issues.extend(analyze_data_exposure())
    all_issues.extend(analyze_cors_security())
    all_issues.extend(analyze_error_handling())
    all_issues.extend(analyze_dependency_security())
    
    # Test functionality
    functionality_results = test_core_functionality()
    
    # Categorize issues by severity
    critical_issues = [i for i in all_issues if i["severity"] == "CRITICAL"]
    high_issues = [i for i in all_issues if i["severity"] == "HIGH"]
    medium_issues = [i for i in all_issues if i["severity"] == "MEDIUM"]
    low_issues = [i for i in all_issues if i["severity"] == "LOW"]
    
    # Count functionality results
    func_passed = len([r for r in functionality_results if r["status"] == "PASS"])
    func_failed = len([r for r in functionality_results if r["status"] == "FAIL"])
    
    print(f"\nSECURITY ISSUES SUMMARY:")
    print(f"Critical: {len(critical_issues)}")
    print(f"High: {len(high_issues)}")
    print(f"Medium: {len(medium_issues)}")
    print(f"Low: {len(low_issues)}")
    print(f"Total: {len(all_issues)}")
    
    print(f"\nFUNCTIONALITY TEST SUMMARY:")
    print(f"Passed: {func_passed}")
    print(f"Failed: {func_failed}")
    print(f"Total: {len(functionality_results)}")
    
    # Display critical issues
    if critical_issues:
        print(f"\nCRITICAL SECURITY ISSUES:")
        for issue in critical_issues:
            print(f"  - {issue['issue']} ({issue['file']})")
            print(f"    Recommendation: {issue['recommendation']}")
    
    # Display high issues
    if high_issues:
        print(f"\nHIGH PRIORITY SECURITY ISSUES:")
        for issue in high_issues:
            print(f"  - {issue['issue']} ({issue['file']})")
            print(f"    Recommendation: {issue['recommendation']}")
    
    # Display functionality results
    print(f"\nFUNCTIONALITY TEST RESULTS:")
    for result in functionality_results:
        status_symbol = "PASS" if result["status"] == "PASS" else "FAIL"
        print(f"  {status_symbol}: {result['component']} - {result['details']}")
    
    # Calculate security score
    total_issues = len(all_issues)
    critical_weight = len(critical_issues) * 4
    high_weight = len(high_issues) * 3
    medium_weight = len(medium_issues) * 2
    low_weight = len(low_issues) * 1
    
    max_possible_score = 100
    penalty = critical_weight + high_weight + medium_weight + low_weight
    security_score = max(0, max_possible_score - penalty)
    
    # Calculate functionality score
    functionality_score = (func_passed / len(functionality_results)) * 100 if functionality_results else 0
    
    print(f"\nOVERALL SCORES:")
    print(f"Security Score: {security_score:.1f}/100")
    print(f"Functionality Score: {functionality_score:.1f}/100")
    print(f"Combined Score: {(security_score + functionality_score) / 2:.1f}/100")
    
    # Security recommendations
    print(f"\nTOP SECURITY RECOMMENDATIONS:")
    print("1. CRITICAL: Implement authentication and authorization")
    print("2. HIGH: Add input validation and sanitization")
    print("3. HIGH: Implement rate limiting")
    print("4. MEDIUM: Configure proper CORS policies")
    print("5. MEDIUM: Add comprehensive error handling")
    print("6. MEDIUM: Implement file upload security")
    print("7. LOW: Regular dependency updates")
    
    # Overall assessment
    if security_score >= 80 and functionality_score >= 90:
        overall_status = "EXCELLENT - Ready for production"
    elif security_score >= 60 and functionality_score >= 80:
        overall_status = "GOOD - Minor improvements needed"
    elif security_score >= 40 and functionality_score >= 70:
        overall_status = "MODERATE - Significant improvements needed"
    else:
        overall_status = "POOR - Major security and functionality issues"
    
    print(f"\nOVERALL ASSESSMENT: {overall_status}")
    
    # Save detailed report
    report_data = {
        "timestamp": datetime.now().isoformat(),
        "security_issues": {
            "critical": critical_issues,
            "high": high_issues,
            "medium": medium_issues,
            "low": low_issues
        },
        "functionality_results": functionality_results,
        "scores": {
            "security_score": security_score,
            "functionality_score": functionality_score,
            "combined_score": (security_score + functionality_score) / 2
        },
        "overall_status": overall_status
    }
    
    with open("security_analysis_report.json", "w") as f:
        json.dump(report_data, f, indent=2)
    
    print(f"\nDetailed report saved to: security_analysis_report.json")
    
    return report_data

if __name__ == "__main__":
    print("TASK REVIEW AGENT - COMPREHENSIVE SECURITY ANALYSIS")
    print("="*80)
    
    try:
        report = generate_comprehensive_report()
        print(f"\nAnalysis complete. Check security_analysis_report.json for details.")
        
    except Exception as e:
        print(f"ANALYSIS FAILED: {e}")
        import traceback
        traceback.print_exc()