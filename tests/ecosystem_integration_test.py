"""
Parikshak Ecosystem Integration End-to-End Proof
======================================================
Tests the full flow:
  1. Intake Niyantran Task (process_niyantran_submission)
  2. Perform Evaluation (RuleEngine)
  3. Create Human-Approved Governance Envelope
  4. Propagate Governed Approval downstream via EcosystemIntegrator
  5. Verify that:
     - Canonical DB (Gov-OS journal) gets the event.
     - Saarthi visibility ledger gets the entry.
     - Niyantran assignments ledger gets the assignment.
     - Bucket log registry gets the entry.
"""
import os
import sys
import json
import pytest
from datetime import datetime, timezone

# Add project root to sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Monkeypatch IntegrityValidator to use a sandbox backup directory
from canonical_db.integrity import IntegrityValidator
original_init = IntegrityValidator.__init__
def patched_init(self, db_path, backup_dir=None):
    sandbox_backup_dir = os.path.join(project_root, "scratch", "temp_backups")
    os.makedirs(sandbox_backup_dir, exist_ok=True)
    original_init(self, db_path, backup_dir=sandbox_backup_dir)
IntegrityValidator.__init__ = patched_init

import canonical_db.integration
from canonical_db.integration import EcosystemIntegrator
from canonical_db.contracts import GovernanceEnvelope
from canonical_db.db import CanonicalDB
from task_selector.bucket_integration import bucket_integration
from evaluation_engine.rule_engine import RuleEngine

# Paths for testing
TEMP_DB_PATH = os.path.join(project_root, "scratch", "temp_integration_db.sqlite")
TEMP_SAARTHI_LEDGER = os.path.join(project_root, "scratch", "temp_saarthi_visibility.jsonl")
TEMP_NIYANTRAN_LEDGER = os.path.join(project_root, "scratch", "temp_niyantran_assignments.jsonl")
TEMP_BUCKET_PATH = os.path.join(project_root, "scratch", "temp_bucket_logs")

# Override global ledger paths in the integration module to sandbox the test
canonical_db.integration.SAARTHI_VISIBILITY_LEDGER = TEMP_SAARTHI_LEDGER
canonical_db.integration.NIYANTRAN_ASSIGNMENTS_LEDGER = TEMP_NIYANTRAN_LEDGER

ARTIFACT_DIR = r"C:\Users\black\.gemini\antigravity-ide\brain\b22567c1-6a04-41d3-911d-d496882aae10"


def clean_temp_files():
    for path in [TEMP_DB_PATH, TEMP_SAARTHI_LEDGER, TEMP_NIYANTRAN_LEDGER]:
        if os.path.exists(path):
            try:
                os.remove(path)
                if os.path.exists(path + "-wal"):
                    os.remove(path + "-wal")
                if os.path.exists(path + "-shm"):
                    os.remove(path + "-shm")
            except Exception:
                pass
    if os.path.exists(TEMP_BUCKET_PATH):
        try:
            import shutil
            shutil.rmtree(TEMP_BUCKET_PATH)
        except Exception:
            pass
    sandbox_backup_dir = os.path.join(project_root, "scratch", "temp_backups")
    if os.path.exists(sandbox_backup_dir):
        try:
            import shutil
            shutil.rmtree(sandbox_backup_dir)
        except Exception:
            pass


def test_ecosystem_propagation():
    clean_temp_files()
    
    # Configure sandboxed Bucket Path
    original_bucket_path = bucket_integration.bucket_path
    bucket_integration.bucket_path = TEMP_BUCKET_PATH
    os.makedirs(TEMP_BUCKET_PATH, exist_ok=True)
    with open(os.path.join(TEMP_BUCKET_PATH, "evaluation_index.jsonl"), "w") as f:
        pass

    try:
        # Initialize sandboxed DB and seed a profile event to establish integrity
        db = CanonicalDB(TEMP_DB_PATH)
        init_envelope = GovernanceEnvelope(
            trace_id="trace-seed-123",
            schema_version="v1.0",
            actor="Akash",
            actor_role="operator",
            timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            lineage_reference="genesis",
            authorized_by="Akash",
            event_type="candidate_profiles",
            payload={
                "candidate_id": "bhiv-cand-001",
                "name": "Akash",
                "github_handle": "blackholeinfiverse78-rgb",
                "skills": ["python", "fastapi"],
                "performance_score": 90.0
            },
            parent_event_hash="0" * 64
        )
        db.append_event(init_envelope, "Akash")
        head_event = db.get_last_event()
        head_hash = head_event["event_hash"]
        db.close()

        # Step 1: Instantiate EcosystemIntegrator and simulate Niyantran task intake
        integrator = EcosystemIntegrator(TEMP_DB_PATH)
        task_payload = {
            "task_id": "T-GOV-002",
            "task_title": "Implement Niyantran Connection Proof",
            "task_description": "Verify tasks are correctly propagated to Niyantran and Saarthi loggers.",
            "submitted_by": "Akash",
            "github_repo_link": "https://github.com/blackholeinfiverse78-rgb/test-repo"
        }
        trace_id = "trace-ecosystem-proof-999"
        
        intake_res = integrator.process_niyantran_submission(task_payload, trace_id=trace_id)
        assert intake_res["status"] == "INGESTED_AWAITING_REVIEW"
        assert intake_res.get("requires_human_approval") is True

        # Step 2: Run Evaluation via RuleEngine
        rule_engine = RuleEngine()
        signals = {
            "domain": "engineering",
            "repository_available": True,
            "description_signals": {"word_count": 120},
            "repository_signals": {
                "structure": {"total_files": 5},
                "quality": {"readme_val": 1},
                "components": {"tests": ["test_api.py"], "docs": []},
                "architecture": {"layer_count": 2, "modular": True},
                "metadata": {"name": "test-repo"}
            },
            "expected_vs_delivered_evidence": {"delivery_ratio": 1.0, "expected_count": 2},
            "missing_features": []
        }
        eval_out = rule_engine.evaluate(signals)
        assert eval_out["evaluation_result"] == "PASS"

        # Step 3: Create Human-Approved Governance Envelope
        payload_data = {
            "review_id": f"rev-{trace_id[:8]}",
            "submission_id": f"sub-{trace_id[:8]}",
            "trace_id": trace_id,
            "evaluation_result": "PASS",
            "failure_type": None,
            "decision": "APPROVED",
            "failure_reasons": [],
            "improvement_hints": [],
            "analysis": {"technical_quality": 95, "clarity": 95, "discipline_signals": 95},
            "reviewed_by": "Akash",
            "reviewed_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "evaluation_time_ms": 15,
            "missing_features": [],
            "evaluation_summary": "Passed evaluation requirements.",
            "selected_task_id": "T-GOV-003",
            "selection_reason": "Advancement to next evolutionary stage",
            "review_state": "APPROVED",
            "score": 95,
            "readiness_percent": 95,
            "status": "pass",
            "candidate_name": "Akash",
            "task_title": "Implement Niyantran Connection Proof"
        }

        # Setup approval envelope signed by Akash (Authorized Governor)
        envelope = GovernanceEnvelope(
            trace_id=trace_id,
            schema_version="v1.0",
            actor="Akash",
            actor_role="operator",
            timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            lineage_reference="genesis",
            authorized_by="Akash",
            event_type="review_history",
            payload=payload_data,
            parent_event_hash=head_hash
        )

        # Step 4: Propagate Governed Approval downstream
        prop_res = integrator.propagate_governed_approval(
            review_envelope=envelope,
            governor="Akash",
            eval_output={
                "evaluation_result": "PASS",
                "failure_type": None,
                "canonical_authority": True
            },
            supporting_signals=signals,
            graph_result={
                "selected_task_id": "T-GOV-003",
                "task_type": "advancement",
                "title": "Next Advanced Architecture Task",
                "difficulty": "intermediate"
            },
            task_data=task_payload
        )

        assert prop_res["status"] == "PROPAGATED"

        # Step 5: Verify downstream outputs
        
        # Verify Gov-OS event journal append
        db = CanonicalDB(TEMP_DB_PATH)
        events = db.get_all_events()
        assert len(events) == 2
        assert events[1]["event_type"] == "review_history"
        assert json.loads(events[1]["payload"])["decision"] == "APPROVED"
        db.close()

        # Verify Saarthi visibility ledger write
        assert os.path.exists(TEMP_SAARTHI_LEDGER)
        with open(TEMP_SAARTHI_LEDGER, "r", encoding="utf-8") as f:
            saarthi_lines = f.readlines()
        assert len(saarthi_lines) >= 1
        saarthi_data = json.loads(saarthi_lines[-1])
        assert saarthi_data["trace_id"] == trace_id
        assert saarthi_data["destination"] == "Saarthi"
        assert saarthi_data["payload"]["decision"] == "APPROVED"

        # Verify Niyantran assignments ledger write
        assert os.path.exists(TEMP_NIYANTRAN_LEDGER)
        with open(TEMP_NIYANTRAN_LEDGER, "r", encoding="utf-8") as f:
            niyantran_lines = f.readlines()
        assert len(niyantran_lines) >= 1
        niyantran_data = json.loads(niyantran_lines[-1])
        assert niyantran_data["trace_id"] == trace_id
        assert niyantran_data["task_id"] == "T-GOV-003"
        assert niyantran_data["assigned_by"] == "Akash"

        # Verify Bucket log write
        logs = bucket_integration.get_evaluation_logs()
        assert len(logs) >= 1
        bucket_log = next((l for l in logs if l.get("trace_id") == trace_id), None)
        assert bucket_log is not None
        assert bucket_log["decision"] == "APPROVED"
        assert bucket_log["candidate_id"] == "Akash"
        assert bucket_log["task_id"] == "T-GOV-002"

        # Write Verification Proof Report to Artifacts
        proof_report = f"""# Parikshak Ecosystem Integration Verification Report

This document records the end-to-end evidence of Parikshak's downstream integrations.

---

## 1. Downstream Propagation Log

| Downstream Target | Event Type | Target Output Ledger | Integration Status |
| :--- | :--- | :--- | :--- |
| **Gov-OS Event Journal** | `review_history` | `{TEMP_DB_PATH}` | **PASSED** (Appended at Seq 2) |
| **Saarthi Ledger** | `downstream_visibility` | `{TEMP_SAARTHI_LEDGER}` | **PASSED** (Line appended) |
| **Niyantran Ledger** | `assignment_dispatch` | `{TEMP_NIYANTRAN_LEDGER}` | **PASSED** (Assignment created) |
| **Bucket Service** | `task_review_evaluation` | `{TEMP_BUCKET_PATH}` | **PASSED** (Bucket index updated) |

---

## 2. Integrated Payload Records

### Saarthi Visibility Payload
```json
{json.dumps(saarthi_data, indent=2)}
```

### Niyantran Assignment Payload
```json
{json.dumps(niyantran_data, indent=2)}
```

### Bucket Ingestion Record
```json
{json.dumps(bucket_log, indent=2)}
```

*Verification timestamp: {datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")} UTC*
"""
        proof_report_path = os.path.join(ARTIFACT_DIR, "ecosystem_integration_proof.md")
        with open(proof_report_path, "w", encoding="utf-8") as f:
            f.write(proof_report)

        print(f"🎉 Ecosystem integration verified. Proof written to {proof_report_path}")

    finally:
        # Restore original bucket path and clean up
        bucket_integration.bucket_path = original_bucket_path
        clean_temp_files()
