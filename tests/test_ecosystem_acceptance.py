"""
Ecosystem Acceptance Test Suite — Parikshak Production Convergence
Verifies trust chains, persistent replay protection, and end-to-end ecosystem convergence.
"""
import sys
import os
import unittest
import json
import uuid
import shutil
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from fastapi import HTTPException

# Add project root to path
sys.path.append(os.getcwd())

from main import app
from security.middleware import SecurityConfig, UserRole, register_used_approval_token, USED_APPROVAL_TOKENS
from production_certification_engine import ProductionCertificationEngine
from ecosystem_participation_validator import EcosystemParticipationValidator
from db.db_config import SessionLocal, init_db
from db.models import SpentTokenModel, Base

class TestEcosystemAcceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.traces_dir = "storage/traces"
        cls.engine = ProductionCertificationEngine(cls.traces_dir)
        cls.validator = EcosystemParticipationValidator(cls.traces_dir)
        
        # Ensure database tables are created (including spent_tokens)
        init_db()

        # Pre-generate valid Governor token
        token = SecurityConfig.create_access_token({"sub": "Akash", "role": UserRole.GOVERNOR.value})
        cls.client.headers = {"Authorization": f"Bearer {token}"}

        # Setup mock trace directories for trust chain testing
        cls.parent_trace_id = f"trace-acceptance-parent-{uuid.uuid4().hex[:6]}"
        cls.child_trace_id = f"trace-acceptance-child-{uuid.uuid4().hex[:6]}"
        cls.parent_path = os.path.join(cls.traces_dir, cls.parent_trace_id)
        cls.child_path = os.path.join(cls.traces_dir, cls.child_trace_id)
        
        os.makedirs(cls.parent_path, exist_ok=True)
        os.makedirs(cls.child_path, exist_ok=True)

        # Write parent trace governance approval (governor: Akash, approved)
        with open(os.path.join(cls.parent_path, "validation_decision.json"), "w") as f:
            json.dump({
                "trace_id": cls.parent_trace_id,
                "decision": "APPROVED",
                "signed_by": "Akash",
                "signature": f"sig-{cls.parent_trace_id}"
            }, f)
        with open(os.path.join(cls.parent_path, "governance_record.json"), "w") as f:
            json.dump({
                "trace_id": cls.parent_trace_id,
                "governor": "Akash",
                "authority_level": "Level_3_Governor",
                "valid_authority": True
            }, f)

        # Write Child trace artifacts (12-dimensions ready files + lineage pointing to parent)
        with open(os.path.join(cls.child_path, "evidence_bundle.json"), "w") as f:
            json.dump({"trace_id": cls.child_trace_id, "files": [], "checksum": "checksum-123"}, f)
        with open(os.path.join(cls.child_path, "handover_bundle.json"), "w") as f:
            json.dump({"trace_id": cls.child_trace_id, "handover_status": "COMPLETE"}, f)
        with open(os.path.join(cls.child_path, "replay_bundle.json"), "w") as f:
            json.dump({"trace_id": cls.child_trace_id, "replay_status": "SUCCESS", "replay_logs": "OpenTelemetry spans verified"}, f)
        with open(os.path.join(cls.child_path, "replay_verification.json"), "w") as f:
            json.dump({"trace_id": cls.child_trace_id, "verified_status": "VERIFIED"}, f)
        with open(os.path.join(cls.child_path, "governance_record.json"), "w") as f:
            json.dump({
                "trace_id": cls.child_trace_id,
                "governor": "Akash",
                "authority_level": "Level_3_Governor",
                "valid_authority": True
            }, f)
        with open(os.path.join(cls.child_path, "validation_decision.json"), "w") as f:
            json.dump({
                "trace_id": cls.child_trace_id,
                "decision": "APPROVED",
                "signed_by": "Akash",
                "signature": f"sig-{cls.child_trace_id}"
            }, f)
        with open(os.path.join(cls.child_path, "lineage_chain.json"), "w") as f:
            json.dump({
                "trace_id": cls.child_trace_id,
                "chain": [cls.child_trace_id, cls.parent_trace_id],
                "valid_chain": True
            }, f)
        with open(os.path.join(cls.child_path, "lineage_bundle.json"), "w") as f:
            json.dump({"trace_id": cls.child_trace_id, "parent_trace_id": cls.parent_trace_id}, f)
        with open(os.path.join(cls.child_path, "lineage_registration.json"), "w") as f:
            json.dump({"trace_id": cls.child_trace_id, "registered": True}, f)
        with open(os.path.join(cls.child_path, "tms_convergence_status.json"), "w") as f:
            json.dump({
                "trace_id": cls.child_trace_id,
                "convergence_status": "CONVERGED",
                "registration_exists": True
            }, f)
        with open(os.path.join(cls.child_path, "ecosystem_placement.json"), "w") as f:
            json.dump({
                "layer": "Core",
                "authority_boundary": "consensus",
                "ownership_declaration": {"owner_team": "Core Engineering"}
            }, f)
        with open(os.path.join(cls.child_path, "consumer_registration.json"), "w") as f:
            json.dump({"registered": True, "consumer_id": "consumer-123"}, f)
        with open(os.path.join(cls.child_path, "architectural_participation.json"), "w") as f:
            json.dump({
                "upstream_systems": ["Pravah"],
                "downstream_systems": ["Saarthi", "Niyantran"],
                "runtime_participants": ["TANTRA"]
            }, f)
        with open(os.path.join(cls.child_path, "schema_metadata.json"), "w") as f:
            json.dump({"schema_drift": False, "schema_version": "v1.0"}, f)
        with open(os.path.join(cls.child_path, "registration_reference.json"), "w") as f:
            json.dump({"schema_version": "v1.0"}, f)
        with open(os.path.join(cls.child_path, "observability_telemetry.json"), "w") as f:
            json.dump({"otel_initialized": True, "metrics_active": True}, f)
        with open(os.path.join(cls.child_path, "recovery_metadata.json"), "w") as f:
            json.dump({"recovery_tested": True, "rollback_anchors_count": 2, "recovery_status": "SUCCESS"}, f)
        with open(os.path.join(cls.child_path, "security_metadata.json"), "w") as f:
            json.dump({
                "critical_vulnerabilities": 0,
                "high_vulnerabilities": 0,
                "medium_vulnerabilities": 0,
                "signature_verified": True
            }, f)

    @classmethod
    def tearDownClass(cls):
        # Cleanup mock trace folders
        if os.path.exists(cls.parent_path):
            shutil.rmtree(cls.parent_path)
        if os.path.exists(cls.child_path):
            shutil.rmtree(cls.child_path)

    def test_trust_chain_validation(self):
        """Verify that child trace correctly validates parent traces in lineage trust chain"""
        # Test trace-acceptance-child
        report = self.engine.certify_system(self.child_trace_id)
        self.assertEqual(report["certification_decision"], "READY")
        self.assertEqual(report["dimensions"]["Human Approval"], "PASS")
        self.assertEqual(report["production_score"], 100)

        # Break parent trust chain (make parent validation decision REJECTED)
        with open(os.path.join(self.parent_path, "validation_decision.json"), "w") as f:
            json.dump({
                "trace_id": self.parent_trace_id,
                "decision": "REJECTED",
                "signed_by": "Akash",
                "signature": f"sig-{self.parent_trace_id}"
            }, f)

        # Child trace should fail due to trust chain compromise (Human Approval dimension -> FAIL)
        compromised_report = self.engine.certify_system(self.child_trace_id)
        self.assertEqual(compromised_report["dimensions"]["Human Approval"], "FAIL")
        self.assertEqual(compromised_report["certification_decision"], "NOT PRODUCTION READY")

        # Restore parent trust chain for subsequent tests
        with open(os.path.join(self.parent_path, "validation_decision.json"), "w") as f:
            json.dump({
                "trace_id": self.parent_trace_id,
                "decision": "APPROVED",
                "signed_by": "Akash",
                "signature": f"sig-{self.parent_trace_id}"
            }, f)

    def test_persistent_replay_protection(self):
        """Verify that spent tokens are persisted to SQL database and survive process-local cache clears"""
        test_token = f"token-acceptance-test-{uuid.uuid4().hex[:6]}"
        
        # 1. First register should succeed
        register_used_approval_token(test_token)
        
        # 2. Duplicate registration should raise 409 Conflict
        with self.assertRaises(HTTPException) as context:
            register_used_approval_token(test_token)
        self.assertEqual(context.exception.status_code, 409)
        self.assertIn("REPLAY_REJECT", context.exception.detail)

        # 3. Simulate process-restart cache clear (clear memory set)
        USED_APPROVAL_TOKENS.clear()
        
        # 4. Duplicate registration after cache clear should STILL raise 409 Conflict because of DB persistence
        with self.assertRaises(HTTPException) as context:
            register_used_approval_token(test_token)
        self.assertEqual(context.exception.status_code, 409)
        self.assertIn("REPLAY_REJECT", context.exception.detail)

    def test_governance_semantics_normalization(self):
        """Verify that PASS/APPROVED/FAIL are correctly mapped interchangeably in engine validation logic"""
        # Change parent validation decision to "PASS" instead of "APPROVED"
        with open(os.path.join(self.parent_path, "validation_decision.json"), "w") as f:
            json.dump({
                "trace_id": self.parent_trace_id,
                "decision": "PASS",
                "signed_by": "Akash",
                "signature": f"sig-{self.parent_trace_id}"
            }, f)

        # Verify certification engine accepts "PASS" as valid approval
        report = self.engine.certify_system(self.child_trace_id)
        self.assertEqual(report["dimensions"]["Human Approval"], "PASS")

        # Restore parent validation decision
        with open(os.path.join(self.parent_path, "validation_decision.json"), "w") as f:
            json.dump({
                "trace_id": self.parent_trace_id,
                "decision": "APPROVED",
                "signed_by": "Akash",
                "signature": f"sig-{self.parent_trace_id}"
            }, f)

if __name__ == "__main__":
    unittest.main()
