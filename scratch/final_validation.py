import json
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import shutil
import asyncio
from datetime import datetime
from replay_audit.atomic_persistence import AUDIT_LOG_DIR, CHECKPOINT_DIR
from replay_audit.replay_engine import replay_engine
from task_selector.niyantran_connection import niyantran_connection
from governance_layer.governance import GovernanceRequest, OperatorRole, OverrideReason
from api.review_routes import approve_submission, modify_submission
from db.persistent_storage import product_storage
from fastapi import HTTPException

class FinalValidationSuite:
    def __init__(self):
        self.date_str = datetime.now().strftime("%Y-%m-%d")
        self.audit_path = os.path.join(AUDIT_LOG_DIR, f"audit_{self.date_str}.jsonl")
        self.backup_path = self.audit_path + ".bak"
        self.results = []

    def backup(self):
        if os.path.exists(self.audit_path):
            shutil.copy(self.audit_path, self.backup_path)

    def restore(self):
        if os.path.exists(self.backup_path):
            shutil.copy(self.backup_path, self.audit_path)

    def record(self, test_name, passed, detail):
        res = f"[{'PASS' if passed else 'FAIL'}] {test_name}: {detail}"
        print(res)
        self.results.append(res)

    def test_partial_write(self):
        self.backup()
        with open(self.audit_path, "a") as f:
            f.write('{"trace_id": "orphan", "action": "approve", "truncat\n')
        try:
            replay_engine.verify_audit_log(self.date_str)
            self.record("Partial Write", False, "Replay accepted corrupted log")
        except ValueError as e:
            self.record("Partial Write", True, "Caught corrupted log")
        
        recovery = replay_engine.partial_recovery(self.audit_path)
        if recovery['recovered']:
            self.record("Partial Write Recovery", True, f"Recovered entries, skipped corrupt")
        self.restore()

    def test_stale_checkpoint(self):
        ckpt_path = os.path.join(CHECKPOINT_DIR, "ckpt-stale.json")
        with open(ckpt_path, "w") as f:
            json.dump({"trace_id": "trace-stale", "state": {"review_state": "PENDING"}, "state_hash": "wronghash"}, f)
        try:
            replay_engine.verify_checkpoint_chain("trace-stale")
            self.record("Stale Checkpoint", False, "Accepted stale/corrupt checkpoint")
        except ValueError as e:
            self.record("Stale Checkpoint", True, "Caught stale checkpoint hash mismatch")
        os.unlink(ckpt_path)

    def test_hash_divergence(self):
        original = {"evaluation_result": "PASS", "failure_type": None, "selected_task_id": "T-GOV-001"}
        replayed = {"evaluation_result": "PASS", "failure_type": None, "selected_task_id": "T-GOV-002"}
        try:
            replay_engine.detect_divergence(original, replayed)
            self.record("Hash Divergence", False, "Missed divergence")
        except ValueError as e:
            self.record("Hash Divergence", True, "Caught output divergence")

    def test_concurrent_governance(self):
        from api.review_routes import _enforce_occ_lock
        class MockReview:
            version = 1
            review_state = "PENDING_REVIEW"
        review = MockReview()
        try:
            _enforce_occ_lock(review, 1)
            review.version = 2
            _enforce_occ_lock(review, 1)
            self.record("Concurrent Governance", False, "Accepted stale version lock")
        except HTTPException as e:
            self.record("Concurrent Governance", True, f"Caught lock race -> {e.detail}")

    def test_dashboard_isolation(self):
        from governance_layer.governance import constitutional_validator
        req = GovernanceRequest(
            trace_id="test", submission_id="test", operator_id="dash1",
            operator_role=OperatorRole.REVIEW_OPERATOR, action="modify",
            reason_taxonomy=OverrideReason.REQUIREMENT_CORRECTION,
            override_task_id="T-HACK"
        )
        try:
            constitutional_validator.validate(req, "PENDING_REVIEW")
            self.record("Dashboard Isolation", False, "Permitted unauthorized dashboard modification")
        except ValueError as e:
            self.record("Dashboard Isolation", True, "Caught authority bypass attempt")

    async def test_live_flow_and_duplicate(self):
        task_req = {
            "task_id": "T-GOV-001", "task_title": "Test Title", "task_description": "Test description is long enough",
            "submitted_by": "dev", "trace_id": "trace-val-001"
        }
        
        # 1. Deterministic eval
        eval_result = niyantran_connection.process_niyantran_task(task_req)
        sub_id = eval_result["submission_id"]
        review = product_storage.get_review_by_submission(sub_id)
        
        if review and review.review_state == "PENDING_REVIEW":
            self.record("Deterministic Eval", True, "Evaluated and queued to PENDING_REVIEW")
            
        # 2. First approval
        gov_req = GovernanceRequest(
            trace_id="trace-val-001", submission_id=sub_id, operator_id="admin-1",
            operator_role=OperatorRole.SENIOR_REVIEW_OPERATOR, action="approve",
            reason_taxonomy=OverrideReason.REQUIREMENT_CORRECTION, expected_version=1
        )
        await approve_submission(gov_req)
        if product_storage.get_review_by_submission(sub_id).review_state == "APPROVED":
            self.record("Approval Flow", True, "Successfully transitioned to APPROVED")
            
        # 3. Duplicate approval attempt
        gov_req.expected_version = 2
        try:
            await approve_submission(gov_req)
            self.record("Duplicate Approval", False, "Allowed duplicate approval")
        except HTTPException as e:
            if e.status_code == 409:
                self.record("Duplicate Approval", True, "Blocked via irreversible state enforcement")
            else:
                self.record("Duplicate Approval", False, "Failed with wrong code")

    def run_all(self):
        print("--- ADVERSARIAL & CONSTITUTIONAL VALIDATION ---")
        self.test_partial_write()
        self.test_stale_checkpoint()
        self.test_hash_divergence()
        self.test_concurrent_governance()
        self.test_dashboard_isolation()
        asyncio.run(self.test_live_flow_and_duplicate())
        
        print("\n--- SUMMARY ---")
        for r in self.results:
            print(r)

if __name__ == "__main__":
    suite = FinalValidationSuite()
    suite.run_all()
