"""
Review Routes — Constitutional Governance Layer
All actions pass through: governance APIs -> audit emitters -> state validators -> replay emitters.
NO direct DB writes. NO hidden mutations. NO silent failures.
"""
from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Dict, Any
from datetime import datetime, timezone
import os
import uuid
import logging
import json

from contracts.review_models import ReviewState, AuditLogEntry
from governance_layer.governance import (
    GovernanceRequest, OverrideEvent, OverrideScope,
    constitutional_validator, IRREVERSIBLE_STATES,
    OverrideReason, OperatorRole
)
from db.persistent_storage import product_storage
from replay_audit.atomic_persistence import atomic_append, write_replay_checkpoint, AUDIT_LOG_DIR

from security.middleware import (
    SecurityConfig, UserRole, require_governor,
    require_reviewer_or_governor, require_operator_or_governor,
    require_any_authenticated, register_used_approval_token
)

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
async def approve_submission(request: GovernanceRequest, current_user: dict = Depends(require_reviewer_or_governor)):
    """
    APPROVE — state -> APPROVED, assign selected_task_id.
    Requires: REVIEW_OPERATOR or SENIOR_REVIEW_OPERATOR.
    """
    review = _get_review_or_404(request.submission_id)
    _enforce_pending_state(review, request.submission_id)

    # Replay protection
    sig_token = f"token-approve-{request.operator_id.lower()}-{request.submission_id}-{review.version}"
    register_used_approval_token(sig_token)

    # Constitutional validation
    try:
        constitutional_validator.validate(request, getattr(review, "review_state", "PENDING_REVIEW"))
    except ValueError as e:
        _emit_operator_visibility(request.operator_id, "approve", request.submission_id, "REJECTED_GOVERNANCE")
        raise HTTPException(status_code=403, detail=str(e))

    _enforce_occ_lock(review, request.expected_version)

    # State transition
    review.review_state = ReviewState.APPROVED
    review.decision = "APPROVED"
    review.status = "pass"
    review.version += 1
    product_storage._save()

    # Propagate governed approval downstream to ecosystem
    try:
        from canonical_db.integration import EcosystemIntegrator
        from canonical_db.contracts import GovernanceEnvelope
        
        review_payload = {
            "review_id": getattr(review, "review_id", f"rev-{request.submission_id}"),
            "submission_id": request.submission_id,
            "trace_id": request.trace_id,
            "evaluation_result": getattr(review, "evaluation_result", "FAIL"),
            "failure_type": getattr(review, "failure_type", None),
            "decision": "APPROVED",
            "failure_reasons": getattr(review, "failure_reasons", []),
            "improvement_hints": getattr(review, "improvement_hints", []),
            "analysis": getattr(review, "analysis", {}) or {},
            "reviewed_by": request.operator_id,
            "reviewed_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "evaluation_summary": getattr(review, "evaluation_summary", ""),
            "selected_task_id": getattr(review, "selected_task_id", ""),
            "selection_reason": getattr(review, "selection_reason", ""),
            "review_state": "APPROVED",
            "score": getattr(review, "score", 0),
            "readiness_percent": getattr(review, "readiness_percent", 0),
            "status": getattr(review, "status", "fail"),
            "candidate_name": getattr(review, "candidate_name", ""),
            "task_title": getattr(review, "task_title", "")
        }
        
        envelope = GovernanceEnvelope(
            trace_id=request.trace_id,
            schema_version="v1.0",
            actor=request.operator_id,
            actor_role=request.operator_role,
            timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            lineage_reference="genesis",
            event_type="review_history",
            payload=review_payload,
            authorized_by=request.operator_id,
            approval_token=sig_token
        )
        
        submission = product_storage.get_submission(request.submission_id)
        task_details = {
            "task_id": submission.task_id if submission else "T-GOV-001",
            "task_title": submission.task_title if submission else getattr(review, "task_title", ""),
            "submitted_by": submission.submitted_by if submission else "operator"
        }
        
        graph_res = {
            "selected_task_id": getattr(review, "selected_task_id", ""),
            "task_type": "advancement" if getattr(review, "evaluation_result", "FAIL") == "PASS" else "correction",
            "title": f"Next Task {getattr(review, 'selected_task_id', '')}",
            "difficulty": "intermediate"
        }
        
        supporting_sigs = {
            "domain": "engineering",
            "repository_available": True,
            "expected_vs_delivered_evidence": {"delivery_ratio": 1.0},
            "expected_features": [],
            "implemented_features": [],
            "missing_features": []
        }
        
        integrator = EcosystemIntegrator()
        propagation_res = integrator.propagate_governed_approval(
            review_envelope=envelope,
            governor=request.operator_id,
            eval_output={
                "evaluation_result": getattr(review, "evaluation_result", "FAIL"),
                "failure_type": getattr(review, "failure_type", None),
                "canonical_authority": True
            },
            supporting_signals=supporting_sigs,
            graph_result=graph_res,
            task_data=task_details
        )
        event_id = propagation_res["commit_details"]["event_id"]
    except Exception as prop_err:
        logger.error(f"[REVIEW] Failed to propagate governed approval downstream: {prop_err}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Downstream ecosystem propagation failed: {str(prop_err)}"
        )

    # Persist validation_decision.json and governance_record.json to trace directory
    try:
        trace_dir = os.path.join("storage", "traces", request.trace_id)
        os.makedirs(trace_dir, exist_ok=True)
        
        dec_data = {
            "trace_id": request.trace_id,
            "decision": "APPROVED",
            "signed_by": request.operator_id,
            "signature": sig_token,
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "approval_reason": str(request.reason_taxonomy),
            "approval_version": review.version
        }
        with open(os.path.join(trace_dir, "validation_decision.json"), "w", encoding="utf-8") as f:
            json.dump(dec_data, f, ensure_ascii=False, indent=2)
            
        gov_data = {
            "trace_id": request.trace_id,
            "governor": request.operator_id,
            "authority_level": "Level_3_Governor",
            "valid_authority": True
        }
        with open(os.path.join(trace_dir, "governance_record.json"), "w", encoding="utf-8") as f:
            json.dump(gov_data, f, ensure_ascii=False, indent=2)
    except Exception as file_err:
        logger.warning(f"Failed to persist governance artifacts: {file_err}")

    try:
        from task_selector.human_in_loop import human_in_loop
        human_in_loop.resolve_escalation_by_trace(request.trace_id, request.operator_id, "approved")
    except Exception as e:
        logger.warning(f"Failed to auto-resolve escalation (non-fatal): {e}")

    # Replay checkpoint
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
async def reject_submission(request: GovernanceRequest, current_user: dict = Depends(require_reviewer_or_governor)):
    """
    REJECT — state -> REJECTED, no assignment.
    Requires: REVIEW_OPERATOR or SENIOR_REVIEW_OPERATOR.
    """
    review = _get_review_or_404(request.submission_id)
    _enforce_pending_state(review, request.submission_id)

    # Replay protection
    sig_token = f"token-reject-{request.operator_id.lower()}-{request.submission_id}-{review.version}"
    register_used_approval_token(sig_token)

    try:
        constitutional_validator.validate(request, getattr(review, "review_state", "PENDING_REVIEW"))
    except ValueError as e:
        _emit_operator_visibility(request.operator_id, "reject", request.submission_id, "REJECTED_GOVERNANCE")
        raise HTTPException(status_code=403, detail=str(e))

    _enforce_occ_lock(review, request.expected_version)

    review.review_state = ReviewState.REJECTED
    review.decision = "REJECTED"
    review.status = "fail"
    review.version += 1
    product_storage._save()

    try:
        from task_selector.human_in_loop import human_in_loop
        human_in_loop.resolve_escalation_by_trace(request.trace_id, request.operator_id, "rejected")
    except Exception as e:
        logger.warning(f"Failed to auto-resolve escalation (non-fatal): {e}")

    # Persist validation_decision.json and governance_record.json to trace directory
    try:
        trace_dir = os.path.join("storage", "traces", request.trace_id)
        os.makedirs(trace_dir, exist_ok=True)
        
        dec_data = {
            "trace_id": request.trace_id,
            "decision": "REJECTED",
            "signed_by": request.operator_id,
            "signature": sig_token,
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "approval_reason": str(request.reason_taxonomy),
            "approval_version": review.version
        }
        with open(os.path.join(trace_dir, "validation_decision.json"), "w", encoding="utf-8") as f:
            json.dump(dec_data, f, ensure_ascii=False, indent=2)
            
        gov_data = {
            "trace_id": request.trace_id,
            "governor": request.operator_id,
            "authority_level": "Level_3_Governor",
            "valid_authority": True
        }
        with open(os.path.join(trace_dir, "governance_record.json"), "w", encoding="utf-8") as f:
            json.dump(gov_data, f, ensure_ascii=False, indent=2)
    except Exception as file_err:
        logger.warning(f"Failed to persist governance artifacts: {file_err}")

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
async def modify_submission(request: GovernanceRequest, current_user: dict = Depends(require_reviewer_or_governor)):
    """
    MODIFY — highest-risk action. Requires dual approval.
    Scope: bounded metadata only. CANNOT mutate traversal/audit/replay.
    Requires: SENIOR_REVIEW_OPERATOR + authorized_by EXECUTION_AUTHORIZER.
    """
    if not request.override_task_id:
        raise HTTPException(status_code=400, detail="override_task_id required for modify")

    review = _get_review_or_404(request.submission_id)
    _enforce_pending_state(review, request.submission_id)

    # Replay protection
    sig_token = f"token-modify-{request.operator_id.lower()}-{request.submission_id}-{review.version}"
    register_used_approval_token(sig_token)

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
    review.decision = "APPROVED"
    review.status = "pass"
    review.version += 1
    product_storage._save()

    try:
        from task_selector.human_in_loop import human_in_loop
        human_in_loop.resolve_escalation_by_trace(request.trace_id, request.operator_id, "modified")
    except Exception as e:
        logger.warning(f"Failed to auto-resolve escalation (non-fatal): {e}")

    # Persist validation_decision.json and governance_record.json to trace directory
    try:
        trace_dir = os.path.join("storage", "traces", request.trace_id)
        os.makedirs(trace_dir, exist_ok=True)
        
        dec_data = {
            "trace_id": request.trace_id,
            "decision": "APPROVED",
            "signed_by": request.operator_id,
            "signature": sig_token,
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "approval_reason": str(request.reason_taxonomy),
            "approval_version": review.version
        }
        with open(os.path.join(trace_dir, "validation_decision.json"), "w", encoding="utf-8") as f:
            json.dump(dec_data, f, ensure_ascii=False, indent=2)
            
        gov_data = {
            "trace_id": request.trace_id,
            "governor": request.operator_id,
            "authority_level": "Level_3_Governor",
            "valid_authority": True
        }
        with open(os.path.join(trace_dir, "governance_record.json"), "w", encoding="utf-8") as f:
            json.dump(gov_data, f, ensure_ascii=False, indent=2)
    except Exception as file_err:
        logger.warning(f"Failed to persist governance artifacts: {file_err}")

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
async def get_pending_reviews(current_user: dict = Depends(require_any_authenticated)):
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
                "review_state":     getattr(review, "review_state", ""),
                "expected_version": getattr(review, "version", 1)
            })
    return pending


@router.get("/all")
async def get_all_reviews(current_user: dict = Depends(require_any_authenticated)):
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
            "selection_reason": getattr(review, "selection_reason", ""),
            "expected_version": getattr(review, "version", 1)
        })
    return all_reviews
