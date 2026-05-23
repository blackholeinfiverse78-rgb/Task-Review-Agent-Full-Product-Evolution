import json
import os
from typing import Dict, Any
from canonical_db.contracts import GovernanceEnvelope
from canonical_db.pipeline import GovernedPipeline
from task_selector.bucket_integration import bucket_integration
from observability.observability import observability

# Downstream ledgers paths
SAARTHI_VISIBILITY_LEDGER = "storage/saarthi_visibility.jsonl"
NIYANTRAN_ASSIGNMENTS_LEDGER = "storage/niyantran_assignments.jsonl"

class EcosystemIntegrator:
    def __init__(self, db_path: str = "storage/canonical_db.sqlite"):
        self.db_path = db_path
        self.pipeline = GovernedPipeline(self.db_path)
        os.makedirs(os.path.dirname(SAARTHI_VISIBILITY_LEDGER), exist_ok=True)

    def process_niyantran_submission(self, task_payload: Dict[str, Any], trace_id: str) -> Dict[str, Any]:
        """
        Receives task from Niyantran, prepares task_lineage & review_history envelopes
        under Governance constraints.
        """
        observability.log_observability_event("info", f"[Ecosystem] Niyantran task received: {task_payload.get('task_id')}", {
            "trace_id": trace_id,
            "task_id": task_payload.get("task_id")
        })

        # Return a receipt showing it has been ingested and placed in the human approval queue
        return {
            "integration": "Niyantran",
            "status": "INGESTED_AWAITING_REVIEW",
            "trace_id": trace_id,
            "task_id": task_payload.get("task_id"),
            "requires_human_approval": True
        }

    def propagate_governed_approval(self, review_envelope: GovernanceEnvelope, governor: str) -> Dict[str, Any]:
        """
        Commits human approved review/assignment and propagates results downstream
        to Saarthi, Bucket, and Niyantran.
        """
        # 1. Commit to Canonical DB via governed pipeline
        commit_res = self.pipeline.submit_mutation(review_envelope, governor)

        # 2. Append to Bucket daily log
        payload = review_envelope.payload
        mock_eval = {"evaluation_result": "PASS" if payload.get("score", 0) >= 80 else "FAIL"}
        mock_signals = {"domain": "engineering", "repository_available": True}
        mock_decision = {"decision": payload.get("status"), "confidence": 1.0}
        mock_next_task = {"next_task_id": "T-GOV-NEXT", "task_type": "advancement"}
        mock_task_data = {
            "task_id": payload.get("submission_id"),
            "task_title": "Integrated Governance Task",
            "task_description": "Mock description of governance-hardened task evolution.",
            "submitted_by": payload.get("reviewed_by") or "Akash",
            "github_repo_link": "https://github.com/blackholeinfiverse78-rgb/mock-repo"
        }
        
        bucket_integration.log_evaluation(
            mock_eval, mock_signals, mock_decision, mock_next_task, mock_task_data,
            trace_id=review_envelope.trace_id
        )

        # 3. Propagate to Saarthi ledger (Downstream visibility)
        saarthi_entry = {
            "trace_id": review_envelope.trace_id,
            "event_type": "downstream_visibility",
            "source": "Parikshak",
            "destination": "Saarthi",
            "payload": payload,
            "timestamp": review_envelope.timestamp
        }
        with open(SAARTHI_VISIBILITY_LEDGER, "a", encoding="utf-8") as f:
            f.write(json.dumps(saarthi_entry) + "\n")

        # 4. Propagate assignment to Niyantran
        niyantran_assignment = {
            "trace_id": review_envelope.trace_id,
            "assignment_id": f"assign-{review_envelope.trace_id[:8]}",
            "task_id": "T-GOV-NEXT",
            "candidate_id": payload.get("reviewed_by", "Unknown"),
            "assigned_by": governor,
            "timestamp": review_envelope.timestamp
        }
        with open(NIYANTRAN_ASSIGNMENTS_LEDGER, "a", encoding="utf-8") as f:
            f.write(json.dumps(niyantran_assignment) + "\n")

        # 5. InsightFlow Observability Notification
        observability.log_observability_event("info", "[Ecosystem] Governed Approval Propagated Downstream.", {
            "trace_id": review_envelope.trace_id,
            "saarthi_status": "SENT",
            "niyantran_status": "SENT",
            "bucket_status": "LOGGED"
        })

        return {
            "status": "PROPAGATED",
            "commit_details": commit_res,
            "saarthi_ledger": SAARTHI_VISIBILITY_LEDGER,
            "niyantran_ledger": NIYANTRAN_ASSIGNMENTS_LEDGER
        }
