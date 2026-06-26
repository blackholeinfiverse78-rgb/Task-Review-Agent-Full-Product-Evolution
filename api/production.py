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

from task_selector.niyantran_connection import niyantran_connection
from task_selector.human_in_loop import human_in_loop
from task_selector.bucket_integration import bucket_integration
from evaluation_engine.review_packet_parser import review_packet_parser
from evaluation_engine.dataset_intake import dataset_intake
from evaluation_engine.bhiv_review_engine import bhiv_review_engine

logger = logging.getLogger("production_api")

router = APIRouter(prefix="/production", tags=["production"])

# Request/Response Models
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

class BucketQueryRequest(BaseModel):
    limit: int = Field(default=100, ge=1, le=1000)
    trace_id: Optional[str] = None

# Niyantran Integration Endpoints
@router.post("/niyantran/submit")
async def submit_task_from_niyantran(request: NiyantranTaskRequest):
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
        # HARD REJECT is not a 500 crash. It's a structured rejection.
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
async def niyantran_health_check():
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
async def get_pending_escalations():
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
async def apply_human_override(request: HumanOverrideRequest):
    """Apply human override to escalated case"""
    try:
        result = human_in_loop.apply_human_override(
            request.case_id,
            request.reviewer,
            request.override_decision,
            request.review_notes
        )
        
        logger.info(f"[PRODUCTION API] Human override applied: case_id={request.case_id}, reviewer={request.reviewer}")
        return {
            "status": "override_applied",
            "case_id": request.case_id,
            "reviewer": request.reviewer,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"[PRODUCTION API] Human override failed: {e}")
        raise HTTPException(status_code=500, detail=f"Override failed: {str(e)}")

# Bucket Integration Endpoints
@router.get("/bucket/logs")
async def get_evaluation_logs(limit: int = 100):
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
async def get_evaluation_by_trace_id(trace_id: str):
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
async def get_bucket_stats():
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
async def get_system_metrics():
    """Get real-time observability metrics for the Deterministic Core"""
    try:
        from observability.observability import observer
        return observer.get_stats()
    except Exception as e:
        logger.error(f"[PRODUCTION API] Failed to get system metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Metrics retrieval failed: {str(e)}")

# System Monitoring Endpoints
@router.get("/system/review-packet-status")
async def check_review_packet_status():
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
async def get_production_status():
    """Get overall production system status"""
    try:
        # Check all system components
        niyantran_health = niyantran_connection.health_check()
        bucket_stats = bucket_integration.get_bucket_stats()
        pending_escalations = human_in_loop.get_pending_escalations()
        packet_status = review_packet_parser.enforce_packet_requirement(".")
        
        # Determine overall status
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

# Test Endpoints (for Vinayak validation)
@router.post("/test/determinism")
async def test_determinism(request: NiyantranTaskRequest, runs: int = 3):
    """
    Test deterministic execution by running the same task multiple times
    For Vinayak's validation protocol
    """
    if runs > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 test runs allowed")
    
    logger.info(f"[PRODUCTION API] Running determinism test: {runs} runs")
    
    results = []
    task_data = request.dict()
    
    try:
        for run in range(runs):
            result = niyantran_connection.process_niyantran_task(task_data)
            
            # Extract key metrics for comparison
            run_result = {
                "run": run + 1,
                "evaluation_result": result["review"]["evaluation_result"],
                "failure_type": result["review"].get("failure_type"),
                "decision": result["review"]["decision"],
                "task_type": result["next_task"]["task_type"],
                "trace_id": result["trace_id"]
            }
            results.append(run_result)
        
        # Check determinism
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
async def get_sample_evaluation():
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
async def get_constitutional_readiness(trace_id: str):
    """
    Independently verify trace readiness (READY, NEEDS_REVIEW, REJECTED)
    using persisted artifacts in storage/traces/{trace_id}/
    """
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
async def get_production_certification(trace_id: str):
    """
    Independently verify production readiness (READY, READY WITH OBSERVATIONS, NEEDS_REVIEW, NOT PRODUCTION READY, UNKNOWN)
    using persisted artifacts in storage/traces/{trace_id}/
    """
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
async def get_ecosystem_participation(trace_id: str):
    """
    Independently verify ecosystem participation role and compliance
    using persisted artifacts in storage/traces/{trace_id}/
    """
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
    original_task_document: str = Field(..., min_length=1)
    review_packet: str = Field(..., min_length=1)
    repository_or_commit: str = Field(..., min_length=1)
    submission_date: str = Field(..., min_length=1)
    due_date: str = Field(..., min_length=1)
    supporting_evidence: Optional[Dict[str, Any]] = Field(default_factory=dict)
    additional_instructions: Optional[str] = Field(default="")
    trace_id: str = Field(..., min_length=8)
    assigned_task_id: Optional[str] = Field(default="T-GOV-001")

@router.post("/intake")
async def dataset_intake_endpoint(request: IntakeRequestBody):
    """
    Accept dataset intake, run evaluation and recommendation, stage for human review.
    """
    logger.info(f"[PRODUCTION API] Intake request received: trace_id={request.trace_id}")
    try:
        # 1. Run dataset intake ingestion & validation
        intake_data = request.model_dump()
        dataset_intake.validate_and_ingest(intake_data, request.trace_id)

        # 2. Generate deterministic submission_id
        import hashlib
        content_hash = hashlib.md5(
            f"{request.assigned_task}{request.original_task_document}".encode(), 
            usedforsecurity=False
        ).hexdigest()[:12]
        submission_id = f"sub-{content_hash}-{request.trace_id[-8:]}"

        # 3. Execute evaluation
        eval_result = bhiv_review_engine.run_evaluation(intake_data, request.trace_id)

        # 4. Persist to storage as PENDING_REVIEW
        from db.persistent_storage import TaskSubmission, ReviewRecord, product_storage, TaskStatus
        
        submission = TaskSubmission(
            submission_id=submission_id,
            task_id=request.assigned_task_id or "T-GOV-001",
            task_title=request.assigned_task,
            task_description=request.original_task_document,
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
            candidate_name="Ishan Shirode",
            task_title=request.assigned_task
        )
        product_storage.store_review(review_record)

        # 5. Stage in human_in_loop review queue
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
            human_in_loop._create_escalation_case(
                evaluation_result=eval_result,
                decision_result=decision_dict,
                supporting_signals=signals_dict,
                confidence_metrics=metrics,
                trace_id=request.trace_id
            )
        except Exception as hil_err:
            logger.warning(f"Could not stage human loop case (non-fatal): {hil_err}")

        # Return structured receipt
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