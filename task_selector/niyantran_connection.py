from typing import Dict, Any, Optional
import logging
from datetime import datetime
import hashlib
import time
from dataclasses import dataclass

from task_selector.final_convergence import final_convergence
from task_selector.bucket_integration import bucket_integration
from evaluation_engine.orchestrator import evaluation_orchestrator

logger = logging.getLogger("niyantran_connection")

_TRACE_ID_MIN_LEN = 8


@dataclass
class NiyantranTask:
    task_id: str
    task_title: str
    task_description: str
    submitted_by: str
    repository_url: Optional[str] = None
    module_id: str = "task-review-agent"
    schema_version: str = "v1.0"
    pdf_text: str = ""
    trace_id: str = ""
    current_task_id: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NiyantranTask":
        trace_id = data.get("trace_id", "").strip()
        if not trace_id or len(trace_id) < _TRACE_ID_MIN_LEN:
            raise ValueError(
                f"NIYANTRAN_HARD_REJECT: trace_id missing or too short "
                f"(got '{trace_id}', min {_TRACE_ID_MIN_LEN} chars). "
                "trace_id must come from Niyantran upstream."
            )
        return cls(
            task_id=data.get("task_id", ""),
            task_title=data.get("task_title", ""),
            task_description=data.get("task_description", ""),
            submitted_by=data.get("submitted_by", ""),
            repository_url=data.get("repository_url"),
            module_id=data.get("module_id", "task-review-agent"),
            schema_version=data.get("schema_version", "v1.0"),
            pdf_text=data.get("pdf_text", ""),
            trace_id=trace_id,
            current_task_id=data.get("current_task_id")
        )


class NiyantranConnectionService:

    def __init__(self):
        self.service_name = "niyantran_connection"
        self.version = "2.0"

    def process_niyantran_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Accept task from Niyantran, run through Parikshak pipeline.
        trace_id must be present in task_data — never generated here.
        """
        start_time = datetime.now()
        logger.info(f"[NIYANTRAN] Received: {task_data.get('task_title', '')[:50]}")

        # Enforce trace_id from upstream
        niyantran_task = NiyantranTask.from_dict(task_data)
        trace_id = niyantran_task.trace_id

        content_hash = hashlib.md5(
            f"{niyantran_task.task_title}{niyantran_task.task_description}".encode(), usedforsecurity=False
        ).hexdigest()[:12]
        attempt_hash = hashlib.md5(
            f"{niyantran_task.task_title}{niyantran_task.task_description}{time.time()}".encode(), usedforsecurity=False
        ).hexdigest()[:8]
        submission_id = f"sub-{content_hash}-{attempt_hash}"

        # Sri Satya Evaluation
        eval_output = evaluation_orchestrator.evaluate_submission(
            task_title=niyantran_task.task_title,
            task_description=niyantran_task.task_description,
            repository_url=niyantran_task.repository_url,
            module_id=niyantran_task.module_id,
            schema_version=niyantran_task.schema_version,
            pdf_text=niyantran_task.pdf_text
        )

        evaluation_result = eval_output["evaluation_result"]
        failure_type = eval_output["failure_type"]

        # Run Parikshak pipeline — trace_id passed unchanged
        convergence_result = final_convergence.process_with_convergence(
            evaluation_result=evaluation_result,
            failure_type=failure_type,
            submission_id=submission_id,
            trace_id=trace_id,
            current_task_id=niyantran_task.current_task_id
        )

        processing_time = int((datetime.now() - start_time).total_seconds() * 1000)

        logger.info(
            f"[NIYANTRAN] Done: trace_id={trace_id} "
            f"result={convergence_result['evaluation_result']} "
            f"selected={convergence_result['selected_task_id']}"
        )

        return {
            "task_id":    niyantran_task.task_id,
            "trace_id":   trace_id,
            "review": {
                "evaluation_result": convergence_result["evaluation_result"],
                "failure_type":      convergence_result["failure_type"],
                "decision":          "APPROVED" if convergence_result["evaluation_result"] == "PASS" else "REJECTED",
                "selected_task_id":  convergence_result["selected_task_id"],
                "selection_reason":  convergence_result["selection_reason"],
                "source":            convergence_result["source"],
            },
            "next_task": {
                "task_id":          convergence_result["selected_task_id"],
                "selection_reason": convergence_result["selection_reason"],
                "source":           convergence_result["source"],
            },
            "processing_metadata": {
                "processing_time_ms": processing_time,
                "timestamp":          datetime.now().isoformat(),
                "status":             "completed",
                "trace_id_source":    "niyantran_upstream",
                "trace_id_overridden": False
            }
        }

    def health_check(self) -> Dict[str, Any]:
        bucket_stats = bucket_integration.get_bucket_stats()
        return {
            "status":       "healthy",
            "service":      self.service_name,
            "version":      self.version,
            "timestamp":    datetime.now().isoformat(),
            "bucket_stats": bucket_stats
        }


# Global instance
niyantran_connection = NiyantranConnectionService()
