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
        Accept task from Niyantran, run through hardened ExecutionPipeline.
        trace_id must be present in task_data — never generated here.
        """
        from evaluation_engine.execution_pipeline import execution_pipeline
        
        logger.info(f"[NIYANTRAN] Received task for processing: {task_data.get('task_title', '')[:50]}")

        # Enforce trace_id from upstream (validated inside pipeline, but we can pre-check for early rejection)
        trace_id = task_data.get("trace_id")
        if not trace_id or len(str(trace_id)) < 8:
             raise ValueError("NIYANTRAN_HARD_REJECT: trace_id missing or too short from upstream.")

        # Run through unified pipeline
        result = execution_pipeline.execute(
            task_data=task_data,
            previous_task_id=task_data.get("current_task_id")
        )

        logger.info(
            f"[NIYANTRAN] Execution complete: trace_id={trace_id} "
            f"result={result['evaluation_result']} "
            f"selected={result['selected_task_id']}"
        )

        return result

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
