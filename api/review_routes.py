from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
from datetime import datetime
import os
import json
import logging

from models.review_models import ReviewActionRequest, ReviewState, AuditLogEntry
from models.persistent_storage import product_storage
from task_selector.niyantran_connection import niyantran_connection

logger = logging.getLogger("review_routes")

router = APIRouter(prefix="/api/v1/review", tags=["review"])

AUDIT_LOG_DIR = "storage/audit_logs"
os.makedirs(AUDIT_LOG_DIR, exist_ok=True)

def log_audit(entry: AuditLogEntry):
    """Write audit log entry in a deterministic format."""
    date_str = datetime.now().strftime("%Y-%m-%d")
    log_file = os.path.join(AUDIT_LOG_DIR, f"audit_{date_str}.jsonl")
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry.model_dump(), default=str) + "\n")

@router.post("/approve")
async def approve_submission(request: ReviewActionRequest):
    """
    APPROVE:
    - state -> APPROVED
    - send selected_task_id to Niyantran
    - NO re-evaluation
    - NO graph traversal rerun
    """
    review = product_storage.get_review_by_submission(request.submission_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review record not found")
    
    review.review_state = ReviewState.APPROVED
    product_storage._save()
    
    # Audit Log
    audit_entry = AuditLogEntry(
        trace_id=request.trace_id,
        submission_id=request.submission_id,
        system_task=review.selected_task_id,
        final_task=review.selected_task_id,
        action="approve"
    )
    log_audit(audit_entry)
    
    logger.info(f"[REVIEW] Approved submission {request.submission_id}")
    
    return {
        "status": "APPROVED",
        "submission_id": request.submission_id,
        "assigned_task": review.selected_task_id
    }

@router.post("/reject")
async def reject_submission(request: ReviewActionRequest):
    """
    REJECT:
    - state -> REJECTED
    - DO NOT assign anything
    """
    review = product_storage.get_review_by_submission(request.submission_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review record not found")
    
    review.review_state = ReviewState.REJECTED
    product_storage._save()
    
    # Audit Log
    audit_entry = AuditLogEntry(
        trace_id=request.trace_id,
        submission_id=request.submission_id,
        system_task=review.selected_task_id,
        final_task="NONE",
        action="reject"
    )
    log_audit(audit_entry)
    
    logger.info(f"[REVIEW] Rejected submission {request.submission_id}")
    
    return {
        "status": "REJECTED",
        "submission_id": request.submission_id
    }

@router.post("/modify")
async def modify_submission(request: ReviewActionRequest):
    """
    MODIFY:
    - state -> MODIFIED
    - replace selected_task_id with override_task_id
    - send overridden task to Niyantran
    - DO NOT re-run selection
    """
    if not request.override_task_id:
        raise HTTPException(status_code=400, detail="override_task_id is required for modify action")
        
    review = product_storage.get_review_by_submission(request.submission_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review record not found")
    
    original_task = review.selected_task_id
    review.selected_task_id = request.override_task_id
    review.review_state = ReviewState.MODIFIED
    product_storage._save()
    
    # Audit Log
    audit_entry = AuditLogEntry(
        trace_id=request.trace_id,
        submission_id=request.submission_id,
        system_task=original_task,
        final_task=request.override_task_id,
        action="modify"
    )
    log_audit(audit_entry)
    
    logger.info(f"[REVIEW] Modified submission {request.submission_id} with task {request.override_task_id}")
    
    return {
        "status": "MODIFIED",
        "submission_id": request.submission_id,
        "assigned_task": request.override_task_id
    }

@router.get("/pending")
async def get_pending_reviews():
    """List all submissions pending review."""
    pending = []
    for sub_id, review in product_storage.reviews.items():
        if review.review_state == ReviewState.PENDING_REVIEW:
            submission = product_storage.get_submission(review.submission_id)
            pending.append({
                "submission_id": review.submission_id,
                "candidate_name": submission.submitted_by if submission else "Unknown",
                "task_title": submission.task_title if submission else "Unknown",
                "evaluation_result": review.evaluation_result,
                "failure_type": review.failure_type,
                "selected_task_id": review.selected_task_id,
                "trace_id": review.trace_id,
                "review_state": review.review_state
            })
    return pending

@router.get("/all")
async def get_all_reviews():
    """List all reviews for the dashboard."""
    all_reviews = []
    for sub_id, review in product_storage.reviews.items():
        submission = product_storage.get_submission(review.submission_id)
        all_reviews.append({
            "submission_id": review.submission_id,
            "candidate_name": submission.submitted_by if submission else "Unknown",
            "task_title": submission.task_title if submission else "Unknown",
            "evaluation_result": review.evaluation_result,
            "failure_type": review.failure_type,
            "selected_task_id": review.selected_task_id,
            "trace_id": review.trace_id,
            "review_state": review.review_state,
            "selection_reason": review.selection_reason,
            "full_response": review.model_dump()
        })
    return all_reviews
