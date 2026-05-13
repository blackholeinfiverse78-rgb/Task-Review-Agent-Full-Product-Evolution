from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class ReviewState(str, Enum):
    PENDING_REVIEW = "PENDING_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    MODIFIED = "MODIFIED"

class ReviewActionRequest(BaseModel):
    trace_id: str
    submission_id: str
    action: str  # approve | reject | modify
    override_task_id: Optional[str] = None

class AuditLogEntry(BaseModel):
    trace_id: str
    submission_id: str
    system_task: str
    final_task: str
    action: str
    timestamp: datetime = Field(default_factory=datetime.now)
