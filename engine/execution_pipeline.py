import logging
from typing import Dict, Any, Optional
import hashlib
import time

from evaluation_engine.orchestrator import evaluation_orchestrator
from engine.task_graph_engine import task_graph_engine
from task_selector.bucket_integration import bucket_integration

logger = logging.getLogger("execution_pipeline")

_REQUIRED_OUTPUT_FIELDS = {
    "trace_id", "submission_id", "evaluation_result",
    "failure_type", "selected_task_id", "selection_reason", "source"
}

class ExecutionPipeline:
    """
    SINGLE entry orchestrator for the entire system.
    Unifies Evaluation (Sri Satya) and Mapping/Graph (Parikshak).
    Implemented as a boundary-safe, deterministic execution unit.
    """

    def execute(
        self,
        task_data: Dict[str, Any],
        previous_task_id: Optional[str] = None,
        pdf_text: str = ""
    ) -> Dict[str, Any]:
        """
        Executes the full pipeline: Validation -> Evaluation -> Selection -> Output
        """
        logger.info("[PIPELINE] Execution cycle started")

        try:
            # 1. INPUT TYPE VALIDATION
            if not isinstance(task_data, dict):
                raise ValueError(f"HARD REJECT: Input task_data must be a dictionary, got {type(task_data)}")

            # 2. INPUT STATE VALIDATION (Phase 3: Input State Validation)
            for forbidden in ("evaluation_result", "failure_type"):
                if forbidden in task_data:
                    raise ValueError(f"HARD REJECT: Input contains injected evaluation field '{forbidden}'")

            # 3. UPSTREAM VALIDATION (Phase 3: Boundary Hardening)
            trace_id = task_data.get("trace_id")
            if not trace_id or not isinstance(trace_id, str) or len(trace_id) < 8:
                logger.error(f"HARD REJECT: trace_id missing, invalid type, or too short ({trace_id})")
                raise ValueError("HARD REJECT: trace_id missing, not a string, or too short (min 8 chars required)")

            # Generate deterministic submission_id
            try:
                title = str(task_data.get('task_title', ''))
                desc = str(task_data.get('task_description', ''))
                content_hash = hashlib.md5(
                    f"{title}{desc}".encode(),
                    usedforsecurity=False
                ).hexdigest()[:12]
            except Exception as e:
                logger.error(f"Hash generation failure: {e}")
                raise ValueError(f"HARD REJECT: Malformed input data cannot be hashed: {e}")

            submission_id = f"sub-{content_hash}-{trace_id[-8:]}"

            # 4. DETERMINISTIC EVALUATION (Phase 1: Sri Satya Logic)
            eval_output = evaluation_orchestrator.evaluate_submission(
                task_title=str(task_data.get("task_title", "")),
                task_description=str(task_data.get("task_description", "")),
                repository_url=task_data.get("github_repo_link"),
                module_id=str(task_data.get("module_id", "task-review-agent")),
                schema_version=str(task_data.get("schema_version", "v1.0")),
                pdf_text=str(pdf_text),
                task_id=task_data.get("task_id")
            )

            eval_res = eval_output.get("evaluation_result", "FAIL")
            failure_type = eval_output.get("failure_type")

            # 5. MAPPING & GRAPH TRAVERSAL (Phase 1: Parikshak Logic)
            current_task_id = previous_task_id or task_data.get("task_id") or "T-GOV-001"
            graph_result = task_graph_engine.traverse(
                current_task_id=current_task_id,
                evaluation_result=eval_res,
                failure_type=failure_type
            )

            # 6. OUTPUT CONSTRUCTION (Phase 3: Downstream Safety)
            output = {
                "trace_id":          str(trace_id),
                "submission_id":     submission_id,
                "evaluation_result": eval_res,
                "failure_type":      failure_type,
                "selected_task_id":  graph_result["selected_task_id"],
                "selection_reason":  graph_result["selection_reason"],
                "source":            "task_graph"
            }

            # 7. BOUNDARY ENFORCEMENT
            self._enforce_boundary(output)

            # 8. PERSISTENCE (Deterministic Logging)
            try:
                self._persist(output, task_data, eval_output, graph_result)
            except Exception as e:
                logger.warning(f"Persistence error (non-fatal): {e}")

            # 9. OBSERVABILITY (Success)
            try:
                from engine.observability import observer
                observer.log_execution(output)
            except Exception as e:
                logger.warning(f"Observability error: {e}")

            logger.info(f"[PIPELINE] Execution successful | Result: {eval_res} | Next: {output['selected_task_id']}")
            return output

        except Exception as e:
            # Observability: Log Hard Reject
            try:
                from engine.observability import observer
                observer.log_execution({"trace_id": task_data.get("trace_id")}, is_hard_reject=True)
            except:
                pass
            raise e

    def _enforce_boundary(self, output: Dict[str, Any]) -> None:
        """Strict validation of the 7-field contract and domain rules"""
        missing = _REQUIRED_OUTPUT_FIELDS - set(output.keys())
        if missing:
            raise ValueError(f"HARD_REJECT: Missing output fields {missing}")
        
        # 1. Trace ID Hard Reject
        trace_id = output.get("trace_id")
        if not trace_id or len(str(trace_id)) < 8:
            raise ValueError(f"HARD_REJECT: trace_id missing or invalid ({trace_id})")

        # 2. Evaluation Result Hard Reject
        if output["evaluation_result"] not in ("PASS", "FAIL"):
            raise ValueError(f"HARD_REJECT: Invalid evaluation_result: {output['evaluation_result']}")
        
        # 3. Failure Type Hard Reject
        valid_failures = {"schema_violation", "incomplete", "incorrect_logic", "integration_fail"}
        if output["evaluation_result"] == "FAIL":
            if output["failure_type"] not in valid_failures:
                raise ValueError(f"HARD_REJECT: Invalid failure_type for FAIL status: {output['failure_type']}")
        elif output["failure_type"] is not None:
            raise ValueError("HARD_REJECT: failure_type must be null for PASS status")

        # 4. Mapping Hard Reject (already handled by graph traversal, but verify result)
        if not output["selected_task_id"]:
            raise ValueError("HARD_REJECT: Missing task mapping. No alternative permitted.")

        # 5. Output contract size (exactly 7 fields)
        if len(output) != 7:
            extra = set(output.keys()) - _REQUIRED_OUTPUT_FIELDS
            raise ValueError(f"HARD_REJECT: Extra fields detected: {extra}")

    def _persist(self, output, task_data, eval_output, graph_result):
        decision = "APPROVED" if output["evaluation_result"] == "PASS" else "REJECTED"
        bucket_integration.log_evaluation(
            eval_output,
            {"repository_available": bool(task_data.get("github_repo_link"))},
            {"decision": decision},
            graph_result,
            {
                "task_id": task_data.get("task_id", "unknown"),
                "trace_id": output["trace_id"],
                "submission_id": output["submission_id"],
                "submitted_by": task_data.get("submitted_by", "system"),
                "task_title": task_data.get("task_title", "Automatic Pipeline Execution")
            },
            trace_id=output["trace_id"]
        )

execution_pipeline = ExecutionPipeline()
