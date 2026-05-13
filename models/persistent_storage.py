"""
Product Core v1 - Persistent Storage Models
Branch: product-core-v1
Base: demo-freeze-v1.0

Deterministic storage layer with explicit lifecycle tracking.
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum
import os
import json


class TaskStatus(str, Enum):
    """Explicit task lifecycle states"""
    ASSIGNED = "assigned"
    SUBMITTED = "submitted"
    REVIEWED = "reviewed"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    MODIFIED = "modified"


class TaskType(str, Enum):
    """Task assignment type"""
    CORRECTION = "correction"
    REINFORCEMENT = "reinforcement"
    ADVANCEMENT = "advancement"


class TaskSubmission(BaseModel):
    """
    Immutable record of task submission.
    All fields explicit, no auto-generation.
    """
    submission_id: str = Field(..., description="Explicit submission identifier")
    task_id: str = Field(..., description="Reference to original task")
    task_title: str = Field(..., min_length=5, max_length=100)
    task_description: str = Field(..., min_length=10, max_length=100000)
    submitted_by: str = Field(..., min_length=2, max_length=50)
    submitted_at: datetime = Field(..., description="Explicit submission timestamp")
    status: TaskStatus = Field(default=TaskStatus.SUBMITTED)
    previous_task_id: Optional[str] = Field(None, description="Reference to previous task in lifecycle")
    pdf_file_path: Optional[str] = Field(None, description="Path to uploaded PDF file")
    pdf_extracted_text: Optional[str] = Field(None, description="Extracted text from PDF")
    module_id: Optional[str] = Field(None)
    schema_version: Optional[str] = Field(None)
    registry_validation_status: Optional[str] = Field(None)
    registry_validation_reason: Optional[str] = Field(None)
    review_state: str = Field(default="PENDING_REVIEW")
    
    class Config:
        use_enum_values = True


class ReviewRecord(BaseModel):
    review_id: str
    submission_id: str
    trace_id: str = Field(default="")
    evaluation_result: str = Field(..., pattern="^(PASS|FAIL)$")
    failure_type: Optional[str] = Field(None)
    decision: str = Field(default="REJECTED")
    failure_reasons: list[str] = Field(default_factory=list)
    improvement_hints: list[str] = Field(default_factory=list)
    analysis: Dict[str, Any] = Field(default_factory=dict)
    reviewed_at: datetime
    evaluation_time_ms: int = Field(default=0)
    missing_features: list[str] = Field(default_factory=list)
    evaluation_summary: str = Field(default="")
    selected_task_id: str = Field(default="")
    selection_reason: str = Field(default="")
    review_state: str = Field(default="PENDING_REVIEW")

    class Config:
        use_enum_values = True


class NextTaskRecord(BaseModel):
    """
    Immutable record of next task assignment.
    Links to review via review_id.
    """
    next_task_id: str = Field(..., description="Explicit next task identifier")
    review_id: str = Field(..., description="Links to ReviewRecord")
    previous_submission_id: str = Field(..., description="Links to previous submission")
    task_type: str = Field(..., pattern="^(correction|reinforcement|advancement)$")
    title: str = Field(..., min_length=5)
    objective: str = Field(..., min_length=10)
    focus_area: str = Field(..., min_length=3)
    difficulty: str = Field(..., pattern="^(beginner|intermediate|advanced)$")
    reason: str = Field(..., description="Assignment reason")
    assigned_at: datetime = Field(..., description="Explicit assignment timestamp")
    
    class Config:
        use_enum_values = True


# In-memory storage with explicit structure
class ProductStorage:
    """
    Deterministic in-memory storage for product core.
    Explicit collections for each entity type.
    """
    def __init__(self, persistence_file: str = "storage/product_state.json"):
        self.submissions: Dict[str, TaskSubmission] = {}
        self.reviews: Dict[str, ReviewRecord] = {}
        self.next_tasks: Dict[str, NextTaskRecord] = {}
        self.persistence_file = persistence_file
        os.makedirs(os.path.dirname(self.persistence_file), exist_ok=True)
        self._load()
    
    def _save(self) -> None:
        """Persist storage to disk."""
        try:
            data = {
                "submissions": {k: v.model_dump(mode='json') for k, v in self.submissions.items()},
                "reviews": {k: v.model_dump(mode='json') for k, v in self.reviews.items()},
                "next_tasks": {k: v.model_dump(mode='json') for k, v in self.next_tasks.items()}
            }
            with open(self.persistence_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Failed to save storage: {e}")

    def _load(self) -> None:
        """Load storage from disk."""
        if not os.path.exists(self.persistence_file):
            return
        try:
            with open(self.persistence_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                for k, v in data.get("submissions", {}).items():
                    self.submissions[k] = TaskSubmission(**v)
                for k, v in data.get("reviews", {}).items():
                    self.reviews[k] = ReviewRecord(**v)
                for k, v in data.get("next_tasks", {}).items():
                    self.next_tasks[k] = NextTaskRecord(**v)
        except Exception as e:
            print(f"Failed to load storage: {e}")

    def store_submission(self, submission: TaskSubmission) -> None:
        """Store task submission"""
        self.submissions[submission.submission_id] = submission
        self._save()
    
    def store_review(self, review: ReviewRecord) -> None:
        """Store review record"""
        self.reviews[review.review_id] = review
        self._save()
    
    def store_next_task(self, next_task: NextTaskRecord) -> None:
        """Store next task record"""
        self.next_tasks[next_task.next_task_id] = next_task
        self._save()
    
    def get_submission(self, submission_id: str) -> Optional[TaskSubmission]:
        """Retrieve submission by ID"""
        return self.submissions.get(submission_id)
    
    def get_review(self, review_id: str) -> Optional[ReviewRecord]:
        """Retrieve review by ID"""
        return self.reviews.get(review_id)
    
    def get_next_task(self, next_task_id: str) -> Optional[NextTaskRecord]:
        """Retrieve next task by ID"""
        return self.next_tasks.get(next_task_id)
    
    def get_review_by_submission(self, submission_id: str) -> Optional[ReviewRecord]:
        """Find review linked to submission"""
        for review in self.reviews.values():
            if review.submission_id == submission_id:
                return review
        return None
    
    def get_next_task_by_submission(self, submission_id: str) -> Optional[NextTaskRecord]:
        """Find next task assigned after submission"""
        for next_task in self.next_tasks.values():
            if next_task.previous_submission_id == submission_id:
                return next_task
        return None
    
    def get_lifecycle(self, submission_id: str) -> Optional[Dict[str, Any]]:
        """Get complete lifecycle for a submission"""
        submission = self.get_submission(submission_id)
        if not submission:
            return None
        
        review = self.get_review_by_submission(submission_id)
        next_task = self.get_next_task_by_submission(submission_id)
        
        return {
            "submission": submission,
            "review": review,
            "next_task": next_task,
            "status": submission.status,
            "previous_task_id": submission.previous_task_id
        }
    
    def clear_all(self) -> None:
        """Clear all storage (for testing)"""
        self.submissions.clear()
        self.reviews.clear()
        self.next_tasks.clear()


# Global storage instance
product_storage = ProductStorage()
