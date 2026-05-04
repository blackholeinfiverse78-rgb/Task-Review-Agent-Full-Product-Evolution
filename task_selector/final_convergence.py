from typing import Dict, Any, Optional
import logging
from datetime import datetime

from engine.task_graph_engine import task_graph_engine
from task_selector.production_decision_engine import production_decision_engine
from task_selector.human_in_loop import human_in_loop
from task_selector.bucket_integration import bucket_integration

logger = logging.getLogger("final_convergence")

_REQUIRED_OUTPUT_FIELDS = {
    "trace_id", "submission_id", "evaluation_result",
    "failure_type", "selected_task_id", "selection_reason", "source"
}

class FinalConvergenceOrchestrator:

    def process_with_convergence(
        self,
        evaluation_result: str,
        failure_type: Optional[str],
        submission_id: str,
        trace_id: str,
        current_task_id: Optional[str] = None
    ) -> Dict[str, Any]:

        logger.info(f"[PARIKSHAK] Starting mapping for trace: {trace_id}")

        # trace_id must exist and must not change
        if not trace_id or len(trace_id) < 8:
            raise ValueError(
                "CONVERGENCE_HARD_REJECT: trace_id missing. "
                "trace_id must come from Niyantran upstream."
            )

        # Step 4: Graph traversal — no fallback
        task_id = current_task_id or "T-GOV-001"
        graph_result = task_graph_engine.traverse(
            current_task_id=task_id,
            evaluation_result=evaluation_result,
            failure_type=failure_type
        )

        # Step 5: Decision engine (narrative only)
        # Decision engine needs minimal context now
        decision = "APPROVED" if evaluation_result == "PASS" else "REJECTED"

        # Step 7: Build strict output contract
        output = {
            "trace_id":          trace_id,
            "submission_id":     submission_id,
            "evaluation_result": evaluation_result,
            "failure_type":      failure_type,
            "selected_task_id":  graph_result["selected_task_id"],
            "selection_reason":  graph_result["selection_reason"],
            "source":            "task_graph",
        }

        # Validate output contract — reject if any field missing or extra
        self._enforce_output_contract(output)

        # Step 8: Bucket logging — non-fatal, log error but don't crash
        try:
            # Create a mock evaluation to pass to bucket logger for now
            mock_eval = {
                "evaluation_result": evaluation_result,
                "failure_type": failure_type
            }
            bucket_integration.log_evaluation(
                mock_eval, {}, decision,
                {"next_task_id": graph_result["selected_task_id"], **graph_result},
                {"task_id": task_id, "trace_id": trace_id, "submission_id": submission_id}
            )
        except Exception as e:
            logger.error(f"[CONVERGENCE] Bucket logging failed (non-fatal): {e}")

        logger.info(
            f"[PARIKSHAK] Done | trace_id={trace_id} | "
            f"result={evaluation_result} | selected={output['selected_task_id']}"
        )
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


# Global instance
final_convergence = FinalConvergenceOrchestrator()
