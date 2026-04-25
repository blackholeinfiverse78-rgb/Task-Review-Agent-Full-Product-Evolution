"""
Final Convergence Orchestrator
Enforces: Assignment Engine → Decision Engine → Validation Gate
No numeric scoring. No fallback scoring. No partial scoring.
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
from .task_selection_engine import task_selection_engine

logger = logging.getLogger("final_convergence")


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

        # Step 0: REVIEW_PACKET hard gate
        packet_result = review_packet_parser.enforce_packet_requirement(".")
        if not packet_result["valid"]:
            return self._hard_reject(
                task_title, task_description, trace_id,
                failure_type="schema_violation",
                reason=f"REVIEW_PACKET hard gate: {packet_result['reason']}"
            )

        # Step 1: Registry validation
        registry_result = registry_validator.validate_complete(module_id, schema_version)
        if registry_result.status == ValidationStatus.INVALID:
            return self._hard_reject(
                task_title, task_description, trace_id,
                failure_type="schema_violation",
                reason=f"Registry validation failed: {registry_result.reason}"
            )

        # Step 2: Signal collection
        supporting_signals = signal_collector.collect_supporting_signals(
            task_title=task_title,
            task_description=task_description,
            repository_url=repository_url,
            pdf_text=pdf_text
        )

        # Step 2.5: Domain routing
        supporting_signals = domain_router.enrich_signals(
            supporting_signals, task_title, task_description
        )

        # Step 3: Assignment Engine — SINGLE AUTHORITY
        evaluation = assignment_engine.evaluate_and_assign(
            task_title=task_title,
            task_description=task_description,
            supporting_signals=supporting_signals
        )

        # Step 4: Decision Engine
        decision = production_decision_engine.make_decision(
            evaluation, supporting_signals, packet_result.get("parsed_data")
        )

        # Step 5: Human-in-loop
        active_trace_id = trace_id or f"trace-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        enhanced = human_in_loop.process_with_human_loop(
            evaluation, decision, supporting_signals, active_trace_id
        )

        # Step 6: Task selection
        result_value = evaluation.get("evaluation_result", "FAIL")
        next_task = task_selection_engine.select_next_task(
            score_10=10.0 if result_value == "PASS" else 0.0,
            decision=decision.get("decision", "REJECTED"),
            current_difficulty="beginner"
        )

        # Build final output
        content_hash = hashlib.md5(
            f"{task_title}{task_description}{module_id}{schema_version}".encode(),
            usedforsecurity=False
        ).hexdigest()[:12]
        attempt_hash = hashlib.md5(
            f"{task_title}{task_description}{time.time()}".encode(),
            usedforsecurity=False
        ).hexdigest()[:8]

        output = {
            "submission_id":      f"sub-{content_hash}-{attempt_hash}",
            "trace_id":           active_trace_id,
            "evaluation_result":  result_value,
            "failure_type":       evaluation.get("failure_type"),
            "decision":           decision.get("decision"),
            "task_type":          decision.get("task_type"),
            "pac":                evaluation.get("pac"),
            "rubric":             evaluation.get("rubric"),
            "strengths":          decision.get("strengths", []),
            "failures":           decision.get("failures", []),
            "root_cause":         decision.get("root_cause", ""),
            "learning_feedback":  decision.get("learning_feedback", []),
            "next_direction":     decision.get("next_direction", ""),
            "next_task":          next_task,
            "requires_human_review": enhanced.get("requires_human_review", False),
            "evaluation_summary": f"Parikshak Evaluation: {result_value}",
            "module_id":          module_id,
            "schema_version":     schema_version,
        }

        # Step 7: Bucket logging
        try:
            bucket_integration.log_evaluation(
                evaluation, supporting_signals, decision, output,
                {"task_title": task_title, "task_description": task_description,
                 "submitted_by": submitted_by, "github_repo_link": repository_url}
            )
        except Exception as e:
            logger.error(f"[CONVERGENCE] Bucket logging failed: {e}")
            output["failure_type"] = "integration_fail"
            output["evaluation_result"] = "FAIL"

        # Step 8: Validation gate
        return validation_gate.validate_final_output(output, "production_pipeline")

    def _hard_reject(
        self,
        task_title: str,
        task_description: str,
        trace_id: Optional[str],
        failure_type: str,
        reason: str
    ) -> Dict[str, Any]:
        content_hash = hashlib.md5(
            f"{task_title}{task_description}".encode(), usedforsecurity=False
        ).hexdigest()[:12]
        result = {
            "submission_id":     f"rejected-{content_hash}",
            "trace_id":          trace_id or "unknown",
            "evaluation_result": "FAIL",
            "failure_type":      failure_type,
            "decision":          "REJECTED",
            "task_type":         "correction",
            "root_cause":        reason,
            "failures":          [reason],
            "strengths":         [],
            "learning_feedback": ["Fix the reported issue and resubmit"],
            "next_direction":    "Resolve the rejection reason before resubmitting",
        }
        return validation_gate.validate_final_output(result, "hard_reject")


# Global instance
final_convergence = FinalConvergenceOrchestrator()
