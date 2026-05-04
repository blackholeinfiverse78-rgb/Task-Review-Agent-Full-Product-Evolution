from datetime import datetime
from typing import Dict, Any, Optional
import uuid
import hashlib
import logging
import time

from models.schemas import Task
from models.persistent_storage import (
    TaskSubmission, ReviewRecord, NextTaskRecord,
    TaskStatus, product_storage
)
from task_selector.final_convergence import final_convergence
from evaluation_engine.orchestrator import evaluation_orchestrator

logger = logging.getLogger("review_orchestrator")


class ReviewOrchestrator:

    def __init__(self, review_engine=None):
        self.convergence_enabled = True

    def process_submission(
        self,
        task: Task,
        previous_task_id: str = None,
        pdf_file_path: Optional[str] = None,
        pdf_extracted_text: Optional[str] = None
    ) -> Dict[str, Any]:

        logger.info(f"[ORCHESTRATOR] Processing: {task.task_title[:50]}")

        # Phase 3: Trace Discipline Fix
        trace_id = getattr(task, "trace_id", None)
        if not trace_id or len(trace_id) < 8:
            raise ValueError(
                "HARD_REJECT: trace_id missing or invalid. "
                "trace_id must come from upstream."
            )

        # Generate submission_id
        content_hash = hashlib.md5(
            f"{task.task_title}{task.task_description}".encode(), usedforsecurity=False
        ).hexdigest()[:12]
        attempt_hash = hashlib.md5(
            f"{task.task_title}{task.task_description}{time.time()}".encode(), usedforsecurity=False
        ).hexdigest()[:8]
        submission_id = f"sub-{content_hash}-{attempt_hash}"

        # 1. Sri Satya - Evaluation Engine
        eval_output = evaluation_orchestrator.evaluate_submission(
            task_title=task.task_title,
            task_description=task.task_description,
            repository_url=getattr(task, "github_repo_link", None),
            module_id=task.module_id,
            schema_version=task.schema_version,
            pdf_text=pdf_extracted_text or ""
        )

        evaluation_result = eval_output["evaluation_result"]
        failure_type = eval_output["failure_type"]

        # 2. Parikshak - Mapping & Graph Traversal
        convergence_result = final_convergence.process_with_convergence(
            evaluation_result=evaluation_result,
            failure_type=failure_type,
            submission_id=submission_id,
            trace_id=trace_id,
            current_task_id=previous_task_id
        )

        selected_task_id  = convergence_result["selected_task_id"]
        selection_reason  = convergence_result["selection_reason"]
        decision          = "APPROVED" if evaluation_result == "PASS" else "REJECTED"

        # Store submission
        submission = TaskSubmission(
            submission_id=submission_id,
            task_id=getattr(task, "task_id", submission_id),
            task_title=task.task_title,
            task_description=task.task_description,
            submitted_by=task.submitted_by,
            submitted_at=datetime.now(),
            status=TaskStatus.SUBMITTED,
            previous_task_id=previous_task_id,
            pdf_file_path=pdf_file_path,
            pdf_extracted_text=pdf_extracted_text,
            module_id=task.module_id,
            schema_version=task.schema_version,
            registry_validation_status="VALID"
        )
        product_storage.store_submission(submission)

        # Store review record
        review_id = f"rev-{uuid.uuid4().hex[:12]}"
        review_record = ReviewRecord(
            review_id=review_id,
            submission_id=submission_id,
            evaluation_result=evaluation_result,
            failure_type=failure_type,
            decision=decision,
            failure_reasons=[failure_type] if failure_type else [],
            improvement_hints=[],
            analysis={},
            reviewed_at=datetime.now(),
            evaluation_time_ms=0,
            missing_features=[],
            evaluation_summary=f"Parikshak Evaluation: {evaluation_result}",
            selected_task_id=selected_task_id,
            selection_reason=selection_reason
        )
        product_storage.store_review(review_record)

        # Store next task record
        next_task_record = NextTaskRecord(
            next_task_id=selected_task_id,
            review_id=review_id,
            previous_submission_id=submission_id,
            task_type="advancement" if evaluation_result == "PASS" else "correction",
            title=selected_task_id,
            objective=selection_reason,
            focus_area="evaluation",
            difficulty="beginner",
            reason=selection_reason,
            assigned_at=datetime.now()
        )
        product_storage.store_next_task(next_task_record)

        # Update submission status
        product_storage.store_submission(
            TaskSubmission(**{**submission.model_dump(), "status": TaskStatus.REVIEWED})
        )

        return {
            "submission_id": submission_id,
            "review_id": review_id,
            "next_task_id": selected_task_id,
            "review": {
                "evaluation_result": evaluation_result,
                "failure_type": failure_type,
                "decision": decision,
                "evaluation_summary": f"Parikshak Evaluation: {evaluation_result}",
                "failure_reasons": [failure_type] if failure_type else [],
                "improvement_hints": [],
                "missing_features": [],
            },
            "next_task": {
                "task_id": selected_task_id,
                "task_type": "advancement" if evaluation_result == "PASS" else "correction",
                "title": selected_task_id,
                "difficulty": "beginner",
                "selection_reason": selection_reason,
            }
        }
