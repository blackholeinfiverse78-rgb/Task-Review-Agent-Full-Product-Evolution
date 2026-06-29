"""
Automated Test Suite for Parikshak Phase IV Production Readiness Certification
"""
import sys
import os
import unittest
from fastapi.testclient import TestClient

# Add project root to path
sys.path.append(os.getcwd())

from production_certification_engine import ProductionCertificationEngine
from ecosystem_participation_validator import EcosystemParticipationValidator
from security.middleware import SecurityConfig
from main import app

class TestProductionCertification(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.traces_dir = "storage/traces"
        cls.engine = ProductionCertificationEngine(cls.traces_dir)
        cls.validator = EcosystemParticipationValidator(cls.traces_dir)
        cls.client = TestClient(app)
        # Generate token and inject header
        token = SecurityConfig.create_access_token({"sub": "Akash", "role": "Governor"})
        cls.client.headers = {"Authorization": f"Bearer {token}"}

    def test_ready_system(self):
        """Test a fully ready system has a score of 100% and verdict READY"""
        report = self.engine.certify_system("trace-prod-ready")
        self.assertEqual(report["certification_decision"], "READY")
        self.assertEqual(report["production_score"], 100)
        self.assertEqual(len(report["critical_failures"]), 0)

        # Test ecosystem validator accepts it
        val_report = self.validator.generate_participation_report("trace-prod-ready")
        self.assertEqual(val_report["verdict"], "ACCEPTED")

    def test_needs_review_system(self):
        """Test a system missing validation decision (critical) and recovery results in NEEDS REVIEW"""
        report = self.engine.certify_system("trace-prod-needs-review")
        self.assertEqual(report["certification_decision"], "NEEDS REVIEW")
        self.assertEqual(report["production_score"], 75) # 3 unknowns (governance, recovery, human approval = 25% total weight missing)
        self.assertIn("Governance", report["dimensions"])
        self.assertEqual(report["dimensions"]["Governance"], "UNKNOWN")

    def test_rejected_system(self):
        """Test a system with critical security vulnerabilities and dependency cycles is rejected"""
        report = self.engine.certify_system("trace-prod-rejected")
        self.assertEqual(report["certification_decision"], "NOT PRODUCTION READY")
        self.assertEqual(report["dimensions"]["Security"], "FAIL")
        self.assertEqual(report["dimensions"]["Dependency Integrity"], "FAIL")
        self.assertGreater(len(report["critical_failures"]), 0)

        # Test ecosystem validator rejects it
        val_report = self.validator.generate_participation_report("trace-prod-rejected")
        self.assertEqual(val_report["verdict"], "REJECTED")

    def test_nonexistent_trace(self):
        """Test that a nonexistent trace fails gracefully"""
        report = self.engine.certify_system("trace-non-existent-12345")
        self.assertEqual(report["certification_decision"], "NOT PRODUCTION READY")
        self.assertIn("not found", report["risk_summary"])

    def test_api_certification_ready(self):
        """Test API endpoint GET /api/v1/production/certification/trace-prod-ready"""
        response = self.client.get("/api/v1/production/certification/trace-prod-ready")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["certification_decision"], "READY")
        self.assertEqual(data["production_score"], 100)

    def test_api_ecosystem_participation_rejected(self):
        """Test API endpoint GET /api/v1/production/ecosystem-participation/trace-prod-rejected"""
        response = self.client.get("/api/v1/production/ecosystem-participation/trace-prod-rejected")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["verdict"], "REJECTED")

if __name__ == "__main__":
    unittest.main()
