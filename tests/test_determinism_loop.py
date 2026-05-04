import unittest
import hashlib
import json
from task_selector.review_orchestrator import ReviewOrchestrator
from models.schemas import Task
from datetime import datetime

class MockEngine:
    def evaluate(self, task_dict):
        # Deterministic Mock Engine
        return {
            "score": 90,
            "readiness_percent": 90,
            "status": "pass",
            "failure_reasons": [],
            "improvement_hints": [],
            "analysis": {"technical_quality": 100, "clarity": 100, "discipline_signals": 100},
            "meta": {"evaluation_time_ms": 120, "mode": "rule"}
        }

class MockGenerator:
    def generate_next_task(self, review, classification):
        from models.orchestration import V2NextTask
        return V2NextTask(
            title="Stable Task",
            objective="Stable Objective",
            focus_area="Testing",
            difficulty="easy"
        )

class TestDeterminismLoop(unittest.TestCase):
    def test_1000_run_consistency(self):
        """
        Audit Requirement: Verify bit-for-bit identical output over 1,000 runs.
        """
        orchestrator = ReviewOrchestrator(MockEngine(), MockGenerator())
        task = Task(
            task_id="audit-test-123",
            task_title="Verification Task",
            task_description="Testing determinism requirements.",
            submitted_by="Auditor",
            timestamp=datetime(2026, 2, 14, 12, 0, 0) # Fixed timestamp for determinism
        )
        
        hashes = set()
        
        for _ in range(1000):
            result = orchestrator.process_submission(task)
            # Serialize with sorted keys for canonical comparison
            canonical_json = json.dumps(result.model_dump(), sort_keys=True, default=str)
            result_hash = hashlib.sha256(canonical_json.encode()).hexdigest()
            hashes.add(result_hash)
            
        self.assertEqual(len(hashes), 1, f"NON-DETERMINISTIC BEHAVIOR: Detected {len(hashes)} unique outputs.")
        print(f"\n[DETERMINISM CHECK] Verified 1,000 runs. Unique hashes: {len(hashes)}")
        print(f"[DETERMINISM CHECK] Stable Hash: {list(hashes)[0]}")

if __name__ == "__main__":
    unittest.main()
