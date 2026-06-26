"""
Dataset Intake Module — Parikshak v6.0.0
Validates that all required evaluation inputs are available before reviews run.
Saves intake evidence to storage/traces/{trace_id}/intake_packet.json.
"""
import os
import json
import logging
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field, ValidationError

logger = logging.getLogger("dataset_intake")

class DatasetIntakeRequest(BaseModel):
    assigned_task: str = Field(..., min_length=1)
    original_task_document: str = Field(..., min_length=1)
    review_packet: str = Field(..., min_length=1)
    repository_or_commit: str = Field(..., min_length=1)
    submission_date: str = Field(..., min_length=1)
    due_date: str = Field(..., min_length=1)
    supporting_evidence: Dict[str, Any] = Field(default_factory=dict)
    additional_instructions: Optional[str] = Field(default="")
    trace_id: Optional[str] = Field(default="")

class DatasetIntakeService:
    def __init__(self, base_storage_dir: str = "storage/traces"):
        self.base_storage_dir = base_storage_dir
        os.makedirs(self.base_storage_dir, exist_ok=True)

    def validate_and_ingest(self, data: Dict[str, Any], trace_id: str) -> Dict[str, Any]:
        """
        Validates intake dataset. Returns validated dict.
        Raises ValueError if required inputs are missing or invalid.
        """
        # Ensure trace_id is present
        if not trace_id or len(trace_id) < 8:
            raise ValueError("HARD_REJECT: trace_id missing or too short from upstream.")

        # Force trace_id in body for consistency
        data_copy = dict(data)
        data_copy["trace_id"] = trace_id

        try:
            intake = DatasetIntakeRequest(**data_copy)
        except ValidationError as e:
            # Format errors for clarity
            errors = [f"{err['loc'][-1]}: {err['msg']}" for err in e.errors()]
            raise ValueError(f"HARD_REJECT: Missing or invalid required intake fields. Errors: {', '.join(errors)}")

        # Create trace directory
        trace_dir = os.path.join(self.base_storage_dir, trace_id)
        os.makedirs(trace_dir, exist_ok=True)

        # Write intake packet JSON
        intake_path = os.path.join(trace_dir, "intake_packet.json")
        try:
            with open(intake_path, "w", encoding="utf-8") as f:
                json.dump(intake.model_dump(), f, ensure_ascii=False, indent=2)
            logger.info(f"[INTAKE] Intake packet persisted for trace: {trace_id}")
        except Exception as file_err:
            logger.error(f"[INTAKE] Failed to write intake packet: {file_err}")
            raise RuntimeError(f"SYSTEM_ERROR: Failed to save intake dataset: {file_err}")

        return intake.model_dump()

# Global instance
dataset_intake = DatasetIntakeService()
