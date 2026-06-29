"""
Dataset Intake Module — Parikshak v8.0.0
Validates that all required evaluation inputs are available before reviews run.
Saves intake evidence to storage/traces/{trace_id}/intake_packet.json.
"""
import os
import json
import logging
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field, ValidationError, model_validator

logger = logging.getLogger("dataset_intake")

class DatasetIntakeRequest(BaseModel):
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
    supporting_evidence: Dict[str, Any] = Field(default_factory=dict)
    architecture_notes: Optional[str] = Field(default="")
    integration_notes: Optional[str] = Field(default="")
    runtime_evidence: Optional[Dict[str, Any]] = Field(default_factory=dict)
    test_evidence: Optional[Dict[str, Any]] = Field(default_factory=dict)
    documentation_evidence: Optional[Dict[str, Any]] = Field(default_factory=dict)
    additional_instructions: Optional[str] = Field(default="")
    trace_id: Optional[str] = Field(default="")

    @model_validator(mode='before')
    @classmethod
    def normalize_fields(cls, values: Any) -> Any:
        if isinstance(values, dict):
            # Normalize task documents
            if values.get("original_task_document") and not values.get("original_assignment_document"):
                values["original_assignment_document"] = values["original_task_document"]
            elif values.get("original_assignment_document") and not values.get("original_task_document"):
                values["original_task_document"] = values["original_assignment_document"]

            # Normalize repository settings
            if values.get("repository_or_commit"):
                if not values.get("repository_path"):
                    values["repository_path"] = values["repository_or_commit"]
                if not values.get("repository_commit_or_branch"):
                    values["repository_commit_or_branch"] = values["repository_or_commit"]
            else:
                if values.get("repository_path") and values.get("repository_commit_or_branch"):
                    values["repository_or_commit"] = f"{values['repository_path']}@{values['repository_commit_or_branch']}"
                elif values.get("repository_path"):
                    values["repository_or_commit"] = values["repository_path"]

            # Normalize submission timestamps
            if values.get("submission_date") and not values.get("submission_timestamp"):
                values["submission_timestamp"] = values["submission_date"]
            elif values.get("submission_timestamp") and not values.get("submission_date"):
                values["submission_date"] = values["submission_timestamp"]

        return values

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

        data_copy = dict(data)
        data_copy["trace_id"] = trace_id

        try:
            intake = DatasetIntakeRequest(**data_copy)
        except ValidationError as e:
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
