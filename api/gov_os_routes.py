from fastapi import APIRouter, HTTPException, status, Depends
from typing import Dict, Any, Optional
from canonical_db.contracts import GovernanceEnvelope
from canonical_db.pipeline import GovernedPipeline
from canonical_db.gpt_bridge import GPTBridge
from canonical_db.strategic_approval import StrategicApprovalEngine
from canonical_db.integration import EcosystemIntegrator
from canonical_db.recovery import RecoveryTool

from security.middleware import (
    require_governor, require_any_authenticated
)

router = APIRouter(prefix="/api/v1/gov-os", tags=["gov-os"])

db_path = "storage/canonical_db.sqlite"

@router.get("/export")
async def export_state(current_user: dict = Depends(require_any_authenticated)):
    bridge = GPTBridge(db_path)
    try:
        return bridge.export_state_for_gpt()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@router.post("/scaffold")
async def prepare_scaffold(request: Dict[str, Any], current_user: dict = Depends(require_governor)):
    bridge = GPTBridge(db_path)
    try:
        gpt_scaffold = request.get("payload", {})
        event_type = request.get("event_type", "")
        trace_id = request.get("trace_id", "")
        actor = request.get("actor", "gpt")
        return bridge.prepare_import_envelope(gpt_scaffold, event_type, trace_id, actor)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/mutate")
async def commit_mutation(request: Dict[str, Any], current_user: dict = Depends(require_governor)):
    pipeline = GovernedPipeline(db_path)
    try:
        envelope = GovernanceEnvelope(**request.get("envelope", {}))
        executor_actor = request.get("executor_actor", "Parikshak")
        result = pipeline.submit_mutation(envelope, executor_actor)
        return result
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/recommend")
async def get_recommendation(request: Dict[str, Any], current_user: dict = Depends(require_any_authenticated)):
    try:
        name = request.get("candidate_name", "Unknown")
        score = request.get("score", 0.0)
        evidence = request.get("evidence", {})
        dep = request.get("dependency_context", "None")
        rec = StrategicApprovalEngine.prepare_recommendation(name, score, evidence, dep)
        return rec.dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/rollback")
async def rollback(request: Dict[str, Any], current_user: dict = Depends(require_governor)):
    tool = RecoveryTool(db_path)
    try:
        target_seq = request.get("target_seq", 1)
        state = tool.rollback_to_sequence(target_seq)
        return {"status": "SUCCESS", "reconstructed_state": state}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reconstruct")
async def reconstruct(request: Dict[str, Any], current_user: dict = Depends(require_governor)):
    tool = RecoveryTool(db_path)
    try:
        jsonl_path = request.get("jsonl_path", "")
        new_db_path = request.get("new_db_path", "storage/reconstructed_db.sqlite")
        success = tool.reconstruct_db_from_jsonl(jsonl_path, new_db_path)
        return {"status": "SUCCESS", "new_db_path": new_db_path}
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/integrate")
async def integrate_flow(request: Dict[str, Any], current_user: dict = Depends(require_governor)):
    integrator = EcosystemIntegrator(db_path)
    try:
        task_payload = request.get("task_payload", {})
        trace_id = request.get("trace_id", "trace-integrated-123")
        return integrator.process_niyantran_submission(task_payload, trace_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
