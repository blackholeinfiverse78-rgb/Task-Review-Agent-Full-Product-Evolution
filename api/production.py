"""
Production API - Parikshak Production Endpoints
Niyantran integration, human-in-loop, bucket access, and system monitoring
"""
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import logging
import os
import json

from task_selector.niyantran_connection import niyantran_connection
from task_selector.human_in_loop import human_in_loop
from task_selector.bucket_integration import bucket_integration
from evaluation_engine.review_packet_parser import review_packet_parser
from evaluation_engine.dataset_intake import dataset_intake
from evaluation_engine.bhiv_review_engine import bhiv_review_engine

from security.middleware import (
    SecurityConfig, UserRole, require_governor,
    require_reviewer_or_governor, require_operator_or_governor,
    require_any_authenticated, register_used_approval_token
)

logger = logging.getLogger("production_api")
router = APIRouter(prefix="/production", tags=["production"])

# Request/Response Models
class LoginRequest(BaseModel):
    username: str
    password: str

class NiyantranTaskRequest(BaseModel):
    task_id: str = Field(..., min_length=1, max_length=100)
    task_title: str = Field(..., min_length=5, max_length=200)
    task_description: str = Field(..., min_length=10, max_length=10000)
    submitted_by: str = Field(..., min_length=2, max_length=50)
    repository_url: Optional[str] = None
    module_id: str = Field(default="task-review-agent")
    schema_version: str = Field(default="v1.0")
    pdf_text: str = Field(default="")
    trace_id: str = Field(..., min_length=8, description="trace_id must come from upstream")
    priority: str = Field(default="normal")
    deadline: Optional[str] = None
    current_task_id: Optional[str] = Field(default=None, description="Current task_id from Niyantran graph — enables deterministic graph traversal")

class HumanOverrideRequest(BaseModel):
    case_id: str = Field(..., min_length=1)
    reviewer: str = Field(..., min_length=2, max_length=50)
    override_decision: Dict[str, Any] = Field(...)
    review_notes: str = Field(..., min_length=10, max_length=1000)
    signature: Optional[str] = None
    approval_reason: Optional[str] = None
    approval_version: Optional[int] = 1

class BucketQueryRequest(BaseModel):
    limit: int = Field(default=100, ge=1, le=1000)
    trace_id: Optional[str] = None

# Token Generation Endpoint
@router.post("/auth/token")
async def login_for_access_token(request: LoginRequest):
    CREDENTIALS = {
        "operator": {"password": "OperatorPass123!", "role": UserRole.OPERATOR.value},
        "reviewer": {"password": "ReviewerPass123!", "role": UserRole.REVIEWER.value},
        "governor": {"password": "GovernorPass123!", "role": UserRole.GOVERNOR.value},
        "readonly": {"password": "ReadOnlyPass123!", "role": UserRole.READONLY.value},
        "Akash": {"password": "AkashPass123!", "role": UserRole.GOVERNOR.value},
        "Ansh": {"password": "AnshPass123!", "role": UserRole.GOVERNOR.value},
    }
    user_info = CREDENTIALS.get(request.username)
    if not user_info or user_info["password"] != request.password:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    token = SecurityConfig.create_access_token({"sub": request.username, "role": user_info["role"]})
    return {"access_token": token, "token_type": "bearer"}

# Niyantran Integration Endpoints
@router.post("/niyantran/submit")
async def submit_task_from_niyantran(request: NiyantranTaskRequest, current_user: dict = Depends(require_operator_or_governor)):
    """
    Accept task from Niyantran and return complete evaluation + next task
    This is the main production endpoint for task processing
    """
    logger.info(f"[PRODUCTION API] Niyantran task received: trace_id={request.trace_id}")
    
    try:
        # Process through Niyantran connection service (now recommendation only)
        result = niyantran_connection.process_niyantran_task(request.model_dump())
        
        # Phase 5: Hard Rule Enforcement - Mandatory Approval Gate
        logger.info(f"[GOVERNANCE] Task queued for review: trace_id={request.trace_id}")
        return {
            "trace_id": result["trace_id"],
            "submission_id": result["submission_id"],
            "review_state": "PENDING_REVIEW",
            "status": "QUEUED",
            "message": "Evaluation complete. Pending human approval for final assignment."
        }
        
    except ValueError as ve:
        error_msg = str(ve)
        logger.error(f"[PRODUCTION API] HARD REJECT: {error_msg}")
        
        error_code = "HARD_REJECT"
        if "trace_id" in error_msg.lower():
            error_code = "TRACE_ID_MISSING"
        elif "mandala" in error_msg.lower():
            error_code = "MANDALA_HARD_REJECT"
        elif "graph" in error_msg.lower():
            error_code = "GRAPH_HARD_REJECT"
            
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "detail": f"HARD REJECT: {error_msg}",
                "error_code": error_code,
                "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            }
        )
        
    except Exception as e:
        logger.error(f"[PRODUCTION API] Niyantran task processing failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": f"Task processing failed: {str(e)}",
                "error_code": "SYSTEM_ERROR",
                "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            }
        )

@router.get("/niyantran/health")
async def niyantran_health_check(current_user: dict = Depends(require_any_authenticated)):
    """Health check for Niyantran connection"""
    try:
        health_result = niyantran_connection.health_check()
        
        if health_result["status"] == "healthy":
            return health_result
        else:
            raise HTTPException(status_code=503, detail=health_result)
            
    except Exception as e:
        logger.error(f"[PRODUCTION API] Health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Health check failed: {str(e)}")

# Human-in-Loop Endpoints
@router.get("/human-review/pending")
async def get_pending_escalations(current_user: dict = Depends(require_any_authenticated)):
    """Get all pending human review cases"""
    try:
        pending_cases = human_in_loop.get_pending_escalations()
        
        return {
            "pending_count": len(pending_cases),
            "cases": pending_cases,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"[PRODUCTION API] Failed to get pending escalations: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve escalations: {str(e)}")

@router.post("/human-review/override")
async def apply_human_override(request: HumanOverrideRequest, current_user: dict = Depends(require_reviewer_or_governor)):
    """Apply human override to escalated case with explicit transitions and propagation"""
    try:
        # 1. Check escalation case
        if request.case_id not in human_in_loop.escalation_cases:
            raise HTTPException(status_code=404, detail=f"Escalation case {request.case_id} not found")
        
        case = human_in_loop.escalation_cases[request.case_id]
        submission_id = case.original_evaluation.get("submission_id")
        
        # 2. Get and update ReviewRecord
        from db.persistent_storage import product_storage
        review = product_storage.get_review_by_submission(submission_id)
        if not review:
            raise HTTPException(status_code=404, detail="Review record not found")
            
        # Replay protection check
        sig_token = request.signature or f"token-override-{request.case_id}-{review.version + 1}"
        register_used_approval_token(sig_token)

        # 3. Apply human override to state machine
        result = human_in_loop.apply_human_override(
            request.case_id,
            request.reviewer,
            request.override_decision,
            request.review_notes
        )
        
        # 4. Explicit transitions of review record
        decision_val = request.override_decision.get("decision", "APPROVED")
        review.decision = decision_val
        review.review_state = decision_val
        review.status = "pass" if decision_val == "APPROVED" else "fail"
        review.evaluation_result = "PASS" if decision_val == "APPROVED" else "FAIL"
        review.reviewed_by = request.reviewer
        review.reviewed_at = datetime.now()
        review.version += 1
        product_storage.store_review(review)

        # 5. Build Gov-OS Governance Envelope and commit mutation
        from canonical_db.integration import EcosystemIntegrator
        from canonical_db.contracts import GovernanceEnvelope
        
        envelope = GovernanceEnvelope(
            trace_id=case.trace_id,
            schema_version="v1.0",
            actor=request.reviewer,
            actor_role="SENIOR_REVIEW_OPERATOR",
            timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            lineage_reference="genesis",
            event_type="review_history",
            payload={
                "review_id": review.review_id,
                "submission_id": submission_id,
                "trace_id": case.trace_id,
                "evaluation_result": review.evaluation_result,
                "failure_type": review.failure_type,
                "decision": review.decision,
                "reviewed_by": request.reviewer,
                "reviewed_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "score": review.score,
                "readiness_percent": review.readiness_percent,
                "status": review.status,
                "candidate_name": review.candidate_name,
                "task_title": review.task_title
            },
            authorized_by=request.reviewer,
            approval_token=sig_token
        )

        # 6. Propagate governed override downstream
        submission = product_storage.get_submission(submission_id)
        task_details = {
            "task_id": submission.task_id if submission else "T-GOV-001",
            "task_title": submission.task_title if submission else review.task_title,
            "submitted_by": submission.submitted_by if submission else "operator"
        }
        
        graph_res = {
            "selected_task_id": review.selected_task_id or "T-GOV-001",
            "task_type": "advancement" if decision_val == "APPROVED" else "correction",
            "title": f"Next Task {review.selected_task_id}",
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
            governor=request.reviewer,
            eval_output={
                "evaluation_result": review.evaluation_result,
                "failure_type": review.failure_type,
                "canonical_authority": True
            },
            supporting_signals=supporting_sigs,
            graph_result=graph_res,
            task_data=task_details
        )
        event_id = propagation_res["commit_details"]["event_id"]

        # 7. Write immutable governance proof files to trace directory
        trace_dir = os.path.join("storage", "traces", case.trace_id)
        os.makedirs(trace_dir, exist_ok=True)
        
        dec_data = {
            "trace_id": case.trace_id,
            "decision": decision_val,
            "signed_by": request.reviewer,
            "signature": sig_token,
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "approval_reason": request.review_notes,
            "approval_version": review.version
        }
        with open(os.path.join(trace_dir, "validation_decision.json"), "w", encoding="utf-8") as f:
            json.dump(dec_data, f, ensure_ascii=False, indent=2)
            
        gov_data = {
            "trace_id": case.trace_id,
            "governor": request.reviewer,
            "authority_level": "Level_3_Governor",
            "valid_authority": True
        }
        with open(os.path.join(trace_dir, "governance_record.json"), "w", encoding="utf-8") as f:
            json.dump(gov_data, f, ensure_ascii=False, indent=2)

        # 8. Emit audit logs
        from api.review_routes import log_audit, _emit_operator_visibility, write_replay_checkpoint
        checkpoint_id = write_replay_checkpoint(case.trace_id, {
            "event_id":      event_id,
            "action":        "override",
            "submission_id": submission_id,
            "final_task":    review.selected_task_id,
            "operator_id":   request.reviewer
        })

        log_audit({
            "event_type":     "governance_action",
            "parent_event_hash": getattr(review, "last_event_hash", None),
            "replay_checkpoint_id": checkpoint_id,
            "expected_version": review.version,
            "event_id":       event_id,
            "trace_id":       case.trace_id,
            "submission_id":  submission_id,
            "operator_id":    request.reviewer,
            "operator_role":  "SENIOR_REVIEW_OPERATOR",
            "action":         "override",
            "reason_taxonomy": "HUMAN_VALIDATION_FAILURE",
            "system_task":    review.selected_task_id,
            "final_task":     review.selected_task_id,
            "timestamp":      datetime.now().isoformat(),
            "finalized":      True
        })

        _emit_operator_visibility(request.reviewer, "override", submission_id, decision_val)
        
        logger.info(f"[PRODUCTION API] Human override applied and propagated: case_id={request.case_id}, reviewer={request.reviewer}")
        return {
            "status": "override_applied",
            "case_id": request.case_id,
            "reviewer": request.reviewer,
            "result": result,
            "event_id": event_id,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException as e:
        raise e
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"[PRODUCTION API] Human override failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Override failed: {str(e)}")

# Bucket Integration Endpoints
@router.get("/bucket/logs")
async def get_evaluation_logs(limit: int = 100, current_user: dict = Depends(require_any_authenticated)):
    """Get recent evaluation logs from bucket"""
    try:
        logs = bucket_integration.get_evaluation_logs(limit)
        
        return {
            "logs_count": len(logs),
            "logs": logs,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"[PRODUCTION API] Failed to get bucket logs: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve logs: {str(e)}")

@router.get("/bucket/evaluation/{trace_id}")
async def get_evaluation_by_trace_id(trace_id: str, current_user: dict = Depends(require_any_authenticated)):
    """Get specific evaluation by trace_id"""
    try:
        evaluation = bucket_integration.get_evaluation_by_trace_id(trace_id)
        
        if not evaluation:
            raise HTTPException(status_code=404, detail=f"Evaluation with trace_id {trace_id} not found")
        
        return evaluation
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[PRODUCTION API] Failed to get evaluation {trace_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve evaluation: {str(e)}")

@router.get("/bucket/stats")
async def get_bucket_stats(current_user: dict = Depends(require_any_authenticated)):
    """Get bucket statistics and metrics"""
    try:
        stats = bucket_integration.get_bucket_stats()
        
        return {
            "bucket_stats": stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"[PRODUCTION API] Failed to get bucket stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve stats: {str(e)}")

@router.get("/system/metrics")
async def get_system_metrics(current_user: dict = Depends(require_any_authenticated)):
    """Get real-time observability metrics for the Deterministic Core"""
    try:
        from observability.observability import observer
        return observer.get_stats()
    except Exception as e:
        logger.error(f"[PRODUCTION API] Failed to get system metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Metrics retrieval failed: {str(e)}")

# System Monitoring Endpoints
@router.get("/system/review-packet-status")
async def check_review_packet_status(current_user: dict = Depends(require_any_authenticated)):
    """Check Review Packet status and validation"""
    try:
        packet_result = review_packet_parser.enforce_packet_requirement(".")
        
        return {
            "review_packet_status": "valid" if packet_result["valid"] else "invalid",
            "packet_result": packet_result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"[PRODUCTION API] Review packet check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Packet check failed: {str(e)}")

@router.get("/system/production-status")
async def get_production_status(current_user: dict = Depends(require_any_authenticated)):
    """Get overall production system status"""
    try:
        niyantran_health = niyantran_connection.health_check()
        bucket_stats = bucket_integration.get_bucket_stats()
        pending_escalations = human_in_loop.get_pending_escalations()
        packet_status = review_packet_parser.enforce_packet_requirement(".")
        
        overall_status = "healthy"
        if niyantran_health["status"] != "healthy":
            overall_status = "degraded"
        if not packet_status["valid"]:
            overall_status = "critical"
        
        return {
            "overall_status": overall_status,
            "components": {
                "niyantran_connection": niyantran_health["status"],
                "bucket_integration": "healthy" if bucket_stats["total_evaluations"] >= 0 else "unhealthy",
                "human_in_loop": f"{len(pending_escalations)} pending escalations",
                "review_packet": "valid" if packet_status["valid"] else "invalid"
            },
            "metrics": {
                "total_evaluations": bucket_stats["total_evaluations"],
                "avg_score": bucket_stats["avg_score"],
                "avg_confidence": bucket_stats["avg_confidence"],
                "pending_human_reviews": len(pending_escalations)
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"[PRODUCTION API] Production status check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")

# Test Endpoints
@router.post("/test/determinism")
async def test_determinism(request: NiyantranTaskRequest, runs: int = 3, current_user: dict = Depends(require_any_authenticated)):
    """
    Test deterministic execution by running the same task multiple times
    """
    if runs > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 test runs allowed")
    
    logger.info(f"[PRODUCTION API] Running determinism test: {runs} runs")
    
    results = []
    task_data = request.model_dump()
    
    try:
        for run in range(runs):
            result = niyantran_connection.process_niyantran_task(task_data)
            run_result = {
                "run": run + 1,
                "evaluation_result": result["review"]["evaluation_result"],
                "failure_type": result["review"].get("failure_type"),
                "decision": result["review"]["decision"],
                "task_type": result["next_task"]["task_type"],
                "trace_id": result["trace_id"]
            }
            results.append(run_result)
        
        first_result = results[0]
        is_deterministic = all(
            r["evaluation_result"] == first_result["evaluation_result"] and
            r["failure_type"] == first_result["failure_type"] and
            r["decision"] == first_result["decision"] and
            r["task_type"] == first_result["task_type"]
            for r in results
        )
        
        return {
            "deterministic": is_deterministic,
            "runs": runs,
            "results": results,
            "summary": {
                "consistent_result":    len(set(r["evaluation_result"] for r in results)) == 1,
                "consistent_failure":   len(set(str(r["failure_type"]) for r in results)) == 1,
                "consistent_decision":  len(set(r["decision"] for r in results)) == 1,
                "consistent_task_type": len(set(r["task_type"] for r in results)) == 1
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"[PRODUCTION API] Determinism test failed: {e}")
        raise HTTPException(status_code=500, detail=f"Determinism test failed: {str(e)}")

@router.get("/test/sample-evaluation")
async def get_sample_evaluation(current_user: dict = Depends(require_any_authenticated)):
    """Get a sample evaluation for testing and validation"""
    sample_task = {
        "task_id": "sample-test-001",
        "task_title": "REST API with Authentication System",
        "task_description": "Build a comprehensive REST API with JWT authentication, user management, role-based access control, and proper error handling. Include unit tests and documentation.",
        "submitted_by": "test-user",
        "repository_url": "https://github.com/test/sample-api",
        "module_id": "task-review-agent",
        "schema_version": "v1.0",
        "pdf_text": "",
        "priority": "normal"
    }
    
    try:
        result = niyantran_connection.process_niyantran_task(sample_task)
        return {
            "sample_task": sample_task,
            "evaluation_result": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"[PRODUCTION API] Sample evaluation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Sample evaluation failed: {str(e)}")

@router.get("/constitutional-review/{trace_id}")
async def get_constitutional_readiness(trace_id: str, current_user: dict = Depends(require_any_authenticated)):
    try:
        from constitutional_readiness_engine import ConstitutionalReadinessEngine
        engine = ConstitutionalReadinessEngine()
        result = engine.evaluate_readiness(trace_id)
        return result
    except Exception as e:
        logger.error(f"[PRODUCTION API] Constitutional review query failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Constitutional review failed: {str(e)}"
        )

@router.get("/certification/{trace_id}")
async def get_production_certification(trace_id: str, current_user: dict = Depends(require_any_authenticated)):
    try:
        from production_certification_engine import ProductionCertificationEngine
        engine = ProductionCertificationEngine()
        result = engine.certify_system(trace_id)
        if "system_information" in result:
            result["system_information"]["certified_at"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        return result
    except Exception as e:
        logger.error(f"[PRODUCTION API] Production certification query failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Production readiness certification failed: {str(e)}"
        )

@router.get("/ecosystem-participation/{trace_id}")
async def get_ecosystem_participation(trace_id: str, current_user: dict = Depends(require_any_authenticated)):
    try:
        from ecosystem_participation_validator import EcosystemParticipationValidator
        val = EcosystemParticipationValidator()
        result = val.generate_participation_report(trace_id)
        return result
    except Exception as e:
        logger.error(f"[PRODUCTION API] Ecosystem participation query failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Ecosystem participation verification failed: {str(e)}"
        )

# Pydantic schema for dataset intake request
class IntakeRequestBody(BaseModel):
    assigned_task: str = Field(..., min_length=1)
    original_task_document: Optional[str] = Field(None)
    original_assignment_document: Optional[str] = Field(None)
    review_packet: str = Field(..., min_length=1)
    repository_or_commit: Optional[str] = Field(None)
    repository_path: Optional[str] = Field(None)
    repository_commit_or_branch: Optional[str] = Field(None)
    submission_date: Optional[str] = Field(None)
    submission_timestamp: Optional[str] = Field(None)
    due_date: str = Field(..., min_length=1)
    expected_deliverables: Optional[Any] = Field(default=None)
    candidate_name: Optional[str] = Field(None)
    candidate_identifier: Optional[str] = Field(None)
    supporting_evidence: Optional[Dict[str, Any]] = Field(default_factory=dict)
    architecture_notes: Optional[str] = Field(default="")
    integration_notes: Optional[str] = Field(default="")
    runtime_evidence: Optional[Dict[str, Any]] = Field(default_factory=dict)
    test_evidence: Optional[Dict[str, Any]] = Field(default_factory=dict)
    documentation_evidence: Optional[Dict[str, Any]] = Field(default_factory=dict)
    additional_instructions: Optional[str] = Field(default="")
    trace_id: str = Field(..., min_length=8)
    assigned_task_id: Optional[str] = Field(default="T-GOV-001")

@router.post("/intake")
async def dataset_intake_endpoint(request: IntakeRequestBody, current_user: dict = Depends(require_operator_or_governor)):
    """
    Accept dataset intake, run evaluation and recommendation, stage for human review.
    """
    logger.info(f"[PRODUCTION API] Intake request received: trace_id={request.trace_id}")
    try:
        intake_data = request.model_dump()
        intake_data = dataset_intake.validate_and_ingest(intake_data, request.trace_id)

        import hashlib
        content_hash = hashlib.md5(
            f"{request.assigned_task}{request.original_assignment_document or request.original_task_document}".encode(), 
            usedforsecurity=False
        ).hexdigest()[:12]
        submission_id = f"sub-{content_hash}-{request.trace_id[-8:]}"

        eval_result = bhiv_review_engine.run_evaluation(intake_data, request.trace_id)

        from db.persistent_storage import TaskSubmission, ReviewRecord, product_storage, TaskStatus
        
        submission = TaskSubmission(
            submission_id=submission_id,
            task_id=request.assigned_task_id or "T-GOV-001",
            task_title=request.assigned_task,
            task_description=request.original_assignment_document or request.original_task_document or "No description",
            submitted_by="operator",
            submitted_at=datetime.now(),
            status=TaskStatus.SUBMITTED,
            pdf_file_path=None,
            pdf_extracted_text=None,
            module_id="task-review-agent",
            schema_version="v1.0",
            registry_validation_status="VALID",
            review_state="PENDING_REVIEW"
        )
        product_storage.store_submission(submission)

        review_record = ReviewRecord(
            review_id=f"rev-{submission_id}",
            submission_id=submission_id,
            trace_id=request.trace_id,
            evaluation_result=eval_result["evaluation_result"],
            failure_type=eval_result["failure_type"],
            decision="PENDING",
            failure_reasons=eval_result["failure_reasons"],
            improvement_hints=eval_result["improvement_hints"],
            analysis=eval_result,
            reviewed_at=datetime.now(),
            evaluation_time_ms=0,
            missing_features=[],
            evaluation_summary=eval_result["evaluation_summary"],
            selected_task_id=eval_result["selected_task_id"],
            selection_reason=eval_result["selection_reason"],
            review_state="PENDING_REVIEW",
            score=eval_result["score"],
            readiness_percent=eval_result["readiness_percent"],
            status=eval_result["status"],
            candidate_name=request.candidate_name or "Ishan Shirode",
            task_title=request.assigned_task
        )
        product_storage.store_review(review_record)

        try:
            from task_selector.human_in_loop import human_in_loop, ConfidenceMetrics
            decision_dict = {"decision": "APPROVED" if eval_result["evaluation_result"] == "PASS" else "REJECTED"}
            signals_dict = {"repository_available": True, "domain": "engineering"}
            metrics = ConfidenceMetrics(
                base_confidence=0.5,
                quality_adjustment=0.0,
                pac_adjustment=0.0,
                evidence_adjustment=0.0,
                consistency_adjustment=0.0,
                final_confidence=0.5,
                proof_consistency=1.0,
                signal_alignment=1.0,
                decision_clarity=1.0,
                evidence_strength=0.5,
                requires_escalation=True,
                escalation_reasons=["low_confidence"]
            )
            eval_result_copy = dict(eval_result)
            eval_result_copy["submission_id"] = submission_id
            human_in_loop._create_escalation_case(
                evaluation_result=eval_result_copy,
                decision_result=decision_dict,
                supporting_signals=signals_dict,
                confidence_metrics=metrics,
                trace_id=request.trace_id
            )
        except Exception as hil_err:
            logger.warning(f"Could not stage human loop case (non-fatal): {hil_err}")

        return {
            "trace_id": request.trace_id,
            "submission_id": submission_id,
            "review_state": "PENDING_REVIEW",
            "status": "QUEUED",
            "message": "Intake valid. Candidate review completed and queued for human approval.",
            "review": eval_result
        }

    except ValueError as val_err:
        logger.error(f"[PRODUCTION API] Intake validation/execution failed: {val_err}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err)
        )
    except Exception as e:
        logger.error(f"[PRODUCTION API] Intake endpoint error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Intake processing encountered an error: {str(e)}"
        )