"""
Final Convergence Orchestrator — Phase 5
Strict output contract. No scoring. No fallback. No inference.

Output contract (exact):
{
  "trace_id":          "...",
  "submission_id":     "...",
  "evaluation_result": "PASS" | "FAIL",
  "failure_type":      "..." | null,
  "selected_task_id":  "...",
  "selection_reason":  "...",
  "source":            "task_graph"
}
"""
from typing import Dict, Any, Optional
import logging
import hashlib
import time
from datetime import datetime

from .assignment_engine import assignment_engine
from .shraddha_validation import validation_gate
from .signal_engine import signal_engine as signal_collector
from .validator import validator as registry_validator, ValidationStatus
from .review_packet_parser import review_packet_parser
from .production_decision_engine import production_decision_engine
from .bucket_integration import bucket_integration
from .human_in_loop import human_in_loop
from .domain_router import domain_router

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from engine.task_graph_engine import task_graph_engine

logger = logging.getLogger("final_convergence")

_REQUIRED_OUTPUT_FIELDS = {
    "trace_id", "submission_id", "evaluation_result",
    "failure_type", "selected_task_id", "selection_reason", "source"
}


class FinalConvergenceOrchestrator:

    def process_with_convergence(
        self,
        task_title: str,
        task_description: str,
        repository_url: Optional[str] = None,
        module_id: str = "task-review-agent",
        schema_version: str = "v1.0",
        pdf_text: str = "",
        current_task_id: Optional[str] = None,
        submitted_by: str = "",
        trace_id: Optional[str] = None
    ) -> Dict[str, Any]:

        logger.info(f"[CONVERGENCE] Starting: {task_title[:50]}")

        # trace_id must exist and must not change
        if not trace_id:
            raise ValueError(
                "CONVERGENCE_HARD_REJECT: trace_id missing. "
                "trace_id must come from Niyantran upstream."
            )
        active_trace_id = trace_id

        # Step 0: REVIEW_PACKET hard gate
        packet_result = review_packet_parser.enforce_packet_requirement(".")
        if not packet_result["valid"]:
            return self._hard_reject(
                active_trace_id, task_title, task_description,
                failure_type="schema_violation",
                reason=f"REVIEW_PACKET hard gate: {packet_result['reason']}",
                current_task_id=current_task_id
            )

        # Step 1: Registry validation
        registry_result = registry_validator.validate_complete(module_id, schema_version)
        if registry_result.status == ValidationStatus.INVALID:
            return self._hard_reject(
                active_trace_id, task_title, task_description,
                failure_type="schema_violation",
                reason=f"Registry validation failed: {registry_result.reason}",
                current_task_id=current_task_id
            )

        # Step 2: Signal collection
        supporting_signals = signal_collector.collect_supporting_signals(
            task_title=task_title,
            task_description=task_description,
            repository_url=repository_url,
            pdf_text=pdf_text
        )

        # Step 2.5: Domain routing — raises on no match
        supporting_signals = domain_router.enrich_signals(
            supporting_signals, task_title, task_description
        )

        # Step 3: Rule Engine evaluation (via assignment_engine)
        evaluation = assignment_engine.evaluate_and_assign(
            task_title=task_title,
            task_description=task_description,
            supporting_signals=supporting_signals
        )

        evaluation_result = evaluation["evaluation_result"]
        failure_type      = evaluation["failure_type"]

        # Step 4: Graph traversal — no fallback
        task_id = current_task_id or "T-GOV-001"
        graph_result = task_graph_engine.traverse(
            current_task_id=task_id,
            evaluation_result=evaluation_result,
            failure_type=failure_type
        )

        # Step 5: Decision engine (narrative only)
        decision = production_decision_engine.make_decision(
            evaluation, supporting_signals, packet_result.get("parsed_data")
        )

        # Step 6: Human-in-loop
        human_in_loop.process_with_human_loop(
            evaluation, decision, supporting_signals, active_trace_id
        )

        # Step 7: Build strict output contract
        submission_id = self._make_submission_id(task_title, task_description)

        output = {
            "trace_id":          active_trace_id,
            "submission_id":     submission_id,
            "evaluation_result": evaluation_result,
            "failure_type":      failure_type,
            "selected_task_id":  graph_result["selected_task_id"],
            "selection_reason":  graph_result["selection_reason"],
            "source":            "task_graph",
        }

        # Validate output contract — reject if any field missing or extra
        self._enforce_output_contract(output)

        # Step 8: Bucket logging
        try:
            bucket_integration.log_evaluation(
                evaluation, supporting_signals, decision, graph_result,
                {"task_title": task_title, "task_description": task_description,
                 "submitted_by": submitted_by, "github_repo_link": repository_url,
                 "task_id": task_id}
            )
        except Exception as e:
            logger.error(f"[CONVERGENCE] Bucket logging failed: {e}")
            raise RuntimeError(f"BUCKET_WRITE_FAILURE: {e}")

        logger.info(
            f"[CONVERGENCE] Done | trace_id={active_trace_id} | "
            f"result={evaluation_result} | selected={output['selected_task_id']}"
        )
        return output

    def _hard_reject(
        self,
        trace_id: str,
        task_title: str,
        task_description: str,
        failure_type: str,
        reason: str,
        current_task_id: Optional[str] = None
    ) -> Dict[str, Any]:
        task_id = current_task_id or "T-GOV-001"
        graph_result = task_graph_engine.traverse(
            current_task_id=task_id,
            evaluation_result="FAIL",
            failure_type=failure_type
        )
        submission_id = self._make_submission_id(task_title, task_description)
        output = {
            "trace_id":          trace_id,
            "submission_id":     submission_id,
            "evaluation_result": "FAIL",
            "failure_type":      failure_type,
            "selected_task_id":  graph_result["selected_task_id"],
            "selection_reason":  f"hard_reject: {reason}",
            "source":            "task_graph",
        }
        self._enforce_output_contract(output)
        return output

    def _enforce_output_contract(self, output: Dict[str, Any]) -> None:
        missing = _REQUIRED_OUTPUT_FIELDS - set(output.keys())
        extra   = set(output.keys()) - _REQUIRED_OUTPUT_FIELDS
        if missing:
            raise ValueError(f"OUTPUT_CONTRACT_VIOLATION: missing fields {missing}")
        if extra:
            raise ValueError(f"OUTPUT_CONTRACT_VIOLATION: extra fields not allowed {extra}")
        if output["evaluation_result"] not in ("PASS", "FAIL"):
            raise ValueError(
                f"OUTPUT_CONTRACT_VIOLATION: evaluation_result must be PASS or FAIL"
            )
        if output["evaluation_result"] == "FAIL" and output["failure_type"] is None:
            raise ValueError(
                "OUTPUT_CONTRACT_VIOLATION: failure_type must not be null when FAIL"
            )
        if output["evaluation_result"] == "PASS" and output["failure_type"] is not None:
            raise ValueError(
                "OUTPUT_CONTRACT_VIOLATION: failure_type must be null when PASS"
            )
        if output["source"] != "task_graph":
            raise ValueError(
                "OUTPUT_CONTRACT_VIOLATION: source must be 'task_graph'"
            )

    def _make_submission_id(self, task_title: str, task_description: str) -> str:
        content_hash = hashlib.md5(
            f"{task_title}{task_description}".encode(), usedforsecurity=False
        ).hexdigest()[:12]
        attempt_hash = hashlib.md5(
            f"{task_title}{task_description}{time.time()}".encode(), usedforsecurity=False
        ).hexdigest()[:8]
        return f"sub-{content_hash}-{attempt_hash}"


# Global instance
final_convergence = FinalConvergenceOrchestrator()
