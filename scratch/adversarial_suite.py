import json
import os
import shutil
from datetime import datetime
from replay_audit.atomic_persistence import AUDIT_LOG_DIR, CHECKPOINT_DIR
from replay_audit.replay_engine import replay_engine

class AdversarialSuite:
    def __init__(self):
        self.date_str = datetime.now().strftime("%Y-%m-%d")
        self.audit_path = os.path.join(AUDIT_LOG_DIR, f"audit_{self.date_str}.jsonl")
        self.backup_path = self.audit_path + ".bak"

    def backup(self):
        if os.path.exists(self.audit_path):
            shutil.copy(self.audit_path, self.backup_path)

    def restore(self):
        if os.path.exists(self.backup_path):
            shutil.copy(self.backup_path, self.audit_path)

    def simulate_partial_write(self):
        print("\n--- SIMULATE PARTIAL WRITE ---")
        self.backup()
        with open(self.audit_path, "a") as f:
            f.write('{"trace_id": "orphan", "action": "approve", "truncat\n')
        
        try:
            res = replay_engine.verify_audit_log(self.date_str)
            print(f"FAILED: Replay engine accepted corrupted log: {res}")
        except ValueError as e:
            print(f"SUCCESS: Caught partial write corruption -> {e}")
            
        print("Running partial recovery:")
        recovery = replay_engine.partial_recovery(self.audit_path)
        print(f"Recovery status: {recovery}")
        self.restore()

    def simulate_stale_checkpoint(self):
        print("\n--- SIMULATE STALE CHECKPOINT ---")
        ckpt_path = os.path.join(CHECKPOINT_DIR, "ckpt-stale.json")
        with open(ckpt_path, "w") as f:
            json.dump({"trace_id": "trace-stale", "state": {"review_state": "PENDING"}, "state_hash": "wronghash"}, f)
            
        try:
            replay_engine.verify_checkpoint_chain("trace-stale")
            print("FAILED: Accepted stale/corrupt checkpoint")
        except ValueError as e:
            print(f"SUCCESS: Caught stale checkpoint -> {e}")
            
        os.unlink(ckpt_path)

    def simulate_hash_divergence(self):
        print("\n--- SIMULATE HASH DIVERGENCE ---")
        original = {"evaluation_result": "PASS", "failure_type": None, "selected_task_id": "T-GOV-001"}
        replayed = {"evaluation_result": "PASS", "failure_type": None, "selected_task_id": "T-GOV-002"}
        
        try:
            replay_engine.detect_divergence(original, replayed)
            print("FAILED: Missed divergence")
        except ValueError as e:
            print(f"SUCCESS: Caught divergence -> {e}")

    def simulate_concurrent_governance(self):
        print("\n--- SIMULATE CONCURRENT GOVERNANCE (LOCK RACING) ---")
        from api.review_routes import _enforce_occ_lock
        from fastapi import HTTPException
        
        class MockReview:
            version = 1
            review_state = "PENDING_REVIEW"
            
        review = MockReview()
        
        try:
            _enforce_occ_lock(review, 1) # First request succeeds
            print("SUCCESS: Valid version accepted")
            
            # Simulate another request that didn't know version was updated
            review.version = 2
            _enforce_occ_lock(review, 1)
            print("FAILED: Accepted stale version lock")
        except HTTPException as e:
            print(f"SUCCESS: Caught concurrent modification -> {e.detail}")

    def prove_dashboard_isolation(self):
        print("\n--- PROVE DASHBOARD ISOLATION ---")
        from governance_layer.governance import constitutional_validator, GovernanceRequest, OperatorRole, OverrideReason
        from fastapi import HTTPException
        
        # Dashboard trying to modify traversal
        req = GovernanceRequest(
            trace_id="test", submission_id="test", operator_id="dash1",
            operator_role=OperatorRole.REVIEW_OPERATOR, action="modify",
            reason_taxonomy=OverrideReason.REQUIREMENT_CORRECTION,
            override_task_id="T-HACK"
        )
        
        try:
            constitutional_validator.validate(req, "PENDING_REVIEW")
            print("FAILED: Permitted unauthorized dashboard modification")
        except ValueError as e:
            print(f"SUCCESS: Caught authority bypass attempt -> {e}")

if __name__ == "__main__":
    suite = AdversarialSuite()
    suite.simulate_partial_write()
    suite.simulate_stale_checkpoint()
    suite.simulate_hash_divergence()
    suite.simulate_concurrent_governance()
    suite.prove_dashboard_isolation()
