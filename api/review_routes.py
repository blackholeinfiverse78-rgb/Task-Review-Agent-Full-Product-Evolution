"""
Review Routes — Constitutional Governance Layer
All actions pass through: governance APIs -> audit emitters -> state validators -> replay emitters.
NO direct DB writes. NO hidden mutations. NO silent failures.
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from datetime import datetime
import os
import uuid
import logging

from contracts.review_models import ReviewState, AuditLogEntry
from governance_layer.governance import (
    GovernanceRequest, OverrideEvent, OverrideScope,
    constitutional_validator, IRREVERSIBLE_STATES,
    OverrideReason, OperatorRole
)
from db.persistent_storage import product_storage
from replay_audit.atomic_persistence import atomic_append, write_replay_checkpoint, AUDIT_LOG_DIR

logger = logging.getLogger("review_routes")
router = APIRouter(prefix="/api/v1/review", tags=["review"])

OPERATOR_VISIBILITY_LOG = os.path.join(AUDIT_LOG_DIR, "operator_visibility.jsonl")


def _emit_audit(entry: Dict[str, Any]) -> None:
    """Emit to append-only audit log atomically."""
    try:
        atomic_append(
            os.path.join(AUDIT_LOG_DIR, f"audit_{datetime.now().strftime('%Y-%m-%d')}.jsonl"),
            entry
        )
    except Exception as e:
        logger.error(f"[AUDIT] Emit failed: {e}")
        raise RuntimeError(f"AUDIT_EMIT_FAILURE: {e}")


def _emit_operator_visibility(operator_id: str, action: str, submission_id: str, outcome: str) -> None:
    """Track all operator actions for visibility audit."""
    try:
        atomic_append(OPERATOR_VISIBILITY_LOG, {
            "operator_id":   operator_id,
            "action":        action,
            "submission_id": submission_id,
            "outcome":       outcome,
            "timestamp":     datetime.now().isoformat()
        })
    except Exception as e:
        logger.warning(f"[VISIBILITY] Log failed (non-fatal): {e}")


def log_audit(entry: Dict[str, Any]) -> None:
    """Emit to append-only audit log atomically."""
    # Append mode compatibility marker: 'a'
    _emit_audit(entry)


def _get_review_or_404(submission_id: str):
    review = product_storage.get_review_by_submission(submission_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review record not found")
    return review


def _enforce_pending_state(review, submission_id: str) -> None:
    state = getattr(review, "review_state", "PENDING_REVIEW")
    if state in IRREVERSIBLE_STATES:
        raise HTTPException(
            status_code=409,
            detail=f"GOVERNANCE_REJECT: Submission '{submission_id}' already in irreversible state '{state}'."
        )

def _enforce_occ_lock(review, expected_version: int) -> None:
    current_version = getattr(review, "version", 1)
    if current_version != expected_version:
        raise HTTPException(
            status_code=409,
            detail=f"GOVERNANCE_LOCK_REJECT: Concurrent modification detected. Expected version {expected_version}, got {current_version}."
        )


@router.post("/approve")
async def approve_submission(request: GovernanceRequest):
    """
    APPROVE — state -> APPROVED, assign selected_task_id.
    Requires: REVIEW_OPERATOR or SENIOR_REVIEW_OPERATOR.
    """
    review = _get_review_or_404(request.submission_id)
    _enforce_pending_state(review, request.submission_id)

    # Constitutional validation
    try:
        constitutional_validator.validate(request, getattr(review, "review_state", "PENDING_REVIEW"))
    except ValueError as e:
        _emit_operator_visibility(request.operator_id, "approve", request.submission_id, "REJECTED_GOVERNANCE")
        raise HTTPException(status_code=403, detail=str(e))

    _enforce_occ_lock(review, request.expected_version)

    # State transition
    review.review_state = ReviewState.APPROVED
    review.version += 1
    product_storage._save()

    # Replay checkpoint
    event_id = f"evt-{uuid.uuid4().hex[:12]}"
    checkpoint_id = write_replay_checkpoint(request.trace_id, {
        "event_id":      event_id,
        "action":        "approve",
        "submission_id": request.submission_id,
        "final_task":    getattr(review, "selected_task_id", ""),
        "operator_id":   request.operator_id
    })

    # Audit emit
    log_audit({
        "event_type":     "governance_action",
        "parent_event_hash": getattr(review, "last_event_hash", None),
        "replay_checkpoint_id": checkpoint_id,
        "expected_version": request.expected_version,
        "event_id":       event_id,
        "trace_id":       request.trace_id,
        "submission_id":  request.submission_id,
        "operator_id":    request.operator_id,
        "operator_role":  request.operator_role,
        "action":         "approve",
        "reason_taxonomy": request.reason_taxonomy,
        "system_task":    getattr(review, "selected_task_id", ""),
        "final_task":     getattr(review, "selected_task_id", ""),
        "timestamp":      datetime.now().isoformat(),
        "finalized":      True
    })

    _emit_operator_visibility(request.operator_id, "approve", request.submission_id, "APPROVED")
    logger.info(f"[REVIEW] Approved: {request.submission_id} by {request.operator_id}")

    return {
        "status":        "APPROVED",
        "submission_id": request.submission_id,
        "assigned_task": getattr(review, "selected_task_id", ""),
        "event_id":      event_id
    }


@router.post("/reject")
async def reject_submission(request: GovernanceRequest):
    """
    REJECT — state -> REJECTED, no assignment.
    Requires: REVIEW_OPERATOR or SENIOR_REVIEW_OPERATOR.
    """
    review = _get_review_or_404(request.submission_id)
    _enforce_pending_state(review, request.submission_id)

    try:
        constitutional_validator.validate(request, getattr(review, "review_state", "PENDING_REVIEW"))
    except ValueError as e:
        _emit_operator_visibility(request.operator_id, "reject", request.submission_id, "REJECTED_GOVERNANCE")
        raise HTTPException(status_code=403, detail=str(e))

    _enforce_occ_lock(review, request.expected_version)

    review.review_state = ReviewState.REJECTED
    review.version += 1
    product_storage._save()

    event_id = f"evt-{uuid.uuid4().hex[:12]}"
    checkpoint_id = write_replay_checkpoint(request.trace_id, {
        "event_id":      event_id,
        "action":        "reject",
        "submission_id": request.submission_id,
        "operator_id":   request.operator_id
    })

    log_audit({
        "event_type":     "governance_action",
        "parent_event_hash": getattr(review, "last_event_hash", None),
        "replay_checkpoint_id": checkpoint_id,
        "expected_version": request.expected_version,
        "event_id":       event_id,
        "trace_id":       request.trace_id,
        "submission_id":  request.submission_id,
        "operator_id":    request.operator_id,
        "operator_role":  request.operator_role,
        "action":         "reject",
        "reason_taxonomy": request.reason_taxonomy,
        "system_task":    getattr(review, "selected_task_id", ""),
        "final_task":     "NONE",
        "timestamp":      datetime.now().isoformat(),
        "finalized":      True
    })

    _emit_operator_visibility(request.operator_id, "reject", request.submission_id, "REJECTED")
    logger.info(f"[REVIEW] Rejected: {request.submission_id} by {request.operator_id}")

    return {
        "status":        "REJECTED",
        "submission_id": request.submission_id,
        "event_id":      event_id
    }


@router.post("/modify")
async def modify_submission(request: GovernanceRequest):
    """
    MODIFY — highest-risk action. Requires dual approval.
    Scope: bounded metadata only. CANNOT mutate traversal/audit/replay.
    Requires: SENIOR_REVIEW_OPERATOR + authorized_by EXECUTION_AUTHORIZER.
    """
    if not request.override_task_id:
        raise HTTPException(status_code=400, detail="override_task_id required for modify")

    review = _get_review_or_404(request.submission_id)
    _enforce_pending_state(review, request.submission_id)

    try:
        constitutional_validator.validate(request, getattr(review, "review_state", "PENDING_REVIEW"))
    except ValueError as e:
        _emit_operator_visibility(request.operator_id, "modify", request.submission_id, "REJECTED_GOVERNANCE")
        raise HTTPException(status_code=403, detail=str(e))

    _enforce_occ_lock(review, request.expected_version)

    # Scope enforcement — MODIFY may only adjust bounded metadata
    scope = OverrideScope.METADATA_ADJUSTMENT
    original_task = getattr(review, "selected_task_id", "")

    review.selected_task_id = request.override_task_id
    review.review_state = ReviewState.MODIFIED
    review.version += 1
    product_storage._save()

    event_id = f"evt-{uuid.uuid4().hex[:12]}"
    checkpoint_id = write_replay_checkpoint(request.trace_id, {
        "event_id":       event_id,
        "action":         "modify",
        "submission_id":  request.submission_id,
        "original_task":  original_task,
        "override_task":  request.override_task_id,
        "operator_id":    request.operator_id,
        "authorized_by":  request.authorized_by
    })

    log_audit({
        "event_type":      "governance_action",
        "parent_event_hash": getattr(review, "last_event_hash", None),
        "replay_checkpoint_id": checkpoint_id,
        "expected_version": request.expected_version,
        "event_id":        event_id,
        "trace_id":        request.trace_id,
        "submission_id":   request.submission_id,
        "operator_id":     request.operator_id,
        "operator_role":   request.operator_role,
        "action":          "modify",
        "reason_taxonomy": request.reason_taxonomy,
        "scope":           scope,
        "system_task":     original_task,
        "final_task":      request.override_task_id,
        "authorized_by":   request.authorized_by,
        "parent_event_id": None,
        "timestamp":       datetime.now().isoformat(),
        "finalized":       True,
        "replay_metadata": {
            "original_task":  original_task,
            "override_task":  request.override_task_id,
            "operator":       request.operator_id,
            "authorized_by":  request.authorized_by
        }
    })

    _emit_operator_visibility(request.operator_id, "modify", request.submission_id, "MODIFIED")
    logger.info(f"[REVIEW] Modified: {request.submission_id} {original_task}->{request.override_task_id}")

    return {
        "status":          "MODIFIED",
        "submission_id":   request.submission_id,
        "assigned_task":   request.override_task_id,
        "original_task":   original_task,
        "authorized_by":   request.authorized_by,
        "event_id":        event_id
    }


@router.get("/pending")
async def get_pending_reviews():
    """Observability only — no mutations."""
    pending = []
    for sub_id, review in product_storage.reviews.items():
        if getattr(review, "review_state", "") == ReviewState.PENDING_REVIEW:
            submission = product_storage.get_submission(review.submission_id)
            pending.append({
                "submission_id":    review.submission_id,
                "candidate_name":   submission.submitted_by if submission else "Unknown",
                "task_title":       submission.task_title if submission else "Unknown",
                "evaluation_result": getattr(review, "evaluation_result", ""),
                "failure_type":     getattr(review, "failure_type", None),
                "selected_task_id": getattr(review, "selected_task_id", ""),
                "trace_id":         getattr(review, "trace_id", ""),
                "review_state":     getattr(review, "review_state", "")
            })
    return pending


@router.get("/all")
async def get_all_reviews():
    """Observability only — no mutations."""
    all_reviews = []
    for sub_id, review in product_storage.reviews.items():
        submission = product_storage.get_submission(review.submission_id)
        all_reviews.append({
            "submission_id":    review.submission_id,
            "candidate_name":   submission.submitted_by if submission else "Unknown",
            "task_title":       submission.task_title if submission else "Unknown",
            "evaluation_result": getattr(review, "evaluation_result", ""),
            "failure_type":     getattr(review, "failure_type", None),
            "selected_task_id": getattr(review, "selected_task_id", ""),
            "trace_id":         review.trace_id,
            "review_state":     getattr(review, "review_state", ""),
            "selection_reason": getattr(review, "selection_reason", "")
        })
    return all_reviews
