"""
FEATURE FREEZE COMPLETE - DEMO-ONLY MODE
Locked on: 2026-02-02
Version: 1.1.0 (PROD-LOCKED)
"""
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import List, Optional
import re

class TaskBase(BaseModel):
    task_title: str = Field(..., min_length=5, max_length=100)
    task_description: str = Field(..., min_length=10, max_length=100000)
    submitted_by: str = Field(..., min_length=2, max_length=50)
    module_id: str = Field(default="task-review-agent", description="Module identifier for registry validation")
    schema_version: str = Field(default="v1.0", description="Schema version for compatibility validation")

    @field_validator('task_title', 'task_description', 'submitted_by')
    @classmethod
    def prevent_empty_whitespace(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Field cannot be empty or just whitespace")
        return v.strip()

class TaskCreate(TaskBase):
    is_demo: bool = Field(default=False)
    demo_type: Optional[str] = Field(default=None)

class Task(TaskBase):
    task_id: str
    timestamp: datetime
    pdf_extracted_text: Optional[str] = None
    github_repo_link: Optional[str] = None  # Maintain backward compatibility

class Analysis(BaseModel):
    technical_quality: int = Field(..., ge=0, le=100)
    clarity: int = Field(..., ge=0, le=100)
    discipline_signals: int = Field(..., ge=0, le=100)

class Meta(BaseModel):
    evaluation_time_ms: int
    mode: str = Field(..., pattern="^(rule|ml|hybrid)$")

class V2NextTask(BaseModel):
    title: str
    objective: str
    focus_area: str
    difficulty: str

class ReviewOutput(BaseModel):
    score: int = Field(..., ge=0, le=100)
    readiness_percent: int = Field(..., ge=0, le=100)
    status: str = Field(..., pattern="^(pass|borderline|fail)$")
    failure_reasons: List[str] = Field(default_factory=list)
    improvement_hints: List[str] = Field(default_factory=list)
    analysis: Analysis
    meta: Meta
    next_task: Optional[V2NextTask] = Field(None, description="Recommended next task block")
    feature_coverage: float = Field(default=0.0)
    architecture_score: float = Field(default=0.0)
    code_quality_score: float = Field(default=0.0)
    completeness_score: float = Field(default=0.0)
    missing_features: List[str] = Field(default_factory=list)
    requirement_match: float = Field(default=0.0)
    evaluation_summary: str = Field(default="")
    documentation_score: float = Field(default=0.0)
    documentation_alignment: str = Field(default="unknown")
    analysis_pdf: Optional[dict] = Field(default=None)
    title_score: float = Field(default=0.0)
    description_score: float = Field(default=0.0)
    repository_score: float = Field(default=0.0)

class NextTask(BaseModel):
    next_task_title: str
    next_task_description: str
    difficulty_level: str
    rationale: str

class ExtendedReviewRequest(BaseModel):
    github_url: str = Field(..., description="GitHub repository URL")
    description: str = Field(..., min_length=10, description="Short project description")

    @field_validator('github_url')
    @classmethod
    def validate_github_url(cls, v: str) -> str:
        # Strict GitHub URL validation
        pattern = r'^https?://github\.com/[\w-]+/[\w.-]+/?$'
        if not re.match(pattern, v):
            raise ValueError("Must be a valid GitHub repository URL (e.g., https://github.com/user/repo)")
        return v
