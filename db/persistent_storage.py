"""
Product Core v1 - Persistent Storage Models
Branch: product-core-v1
Base: demo-freeze-v1.0

Deterministic storage layer with explicit lifecycle tracking.
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
import os
import json
import time
import errno
import threading
import logging

from db.db_config import SessionLocal, init_db
from db.models import TaskSubmissionModel, ReviewModel, AssignmentModel, Builder, Product

logger = logging.getLogger("persistent_storage")


class FileLock:
    """Cross-process reentrant lock using exclusive file creation."""
    def __init__(self, lock_path: str, timeout: float = 15.0, delay: float = 0.02):
        self.lock_path = lock_path
        self.timeout = timeout
        self.delay = delay
        self._local = threading.local()

    def _is_pid_running(self, pid: int) -> bool:
        if os.name == 'nt':
            import ctypes
            PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
            kernel32 = ctypes.windll.kernel32
            handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
            if not handle:
                err = kernel32.GetLastError()
                if err == 5:  # Access denied: process exists but we can't query it
                    return True
                return False
            exit_code = ctypes.c_ulong()
            STILL_ACTIVE = 259
            if kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
                kernel32.CloseHandle(handle)
                return exit_code.value == STILL_ACTIVE
            kernel32.CloseHandle(handle)
            return False
        else:
            try:
                os.kill(pid, 0)
                return True
            except OSError:
                return False

    def __enter__(self):
        if getattr(self._local, "depth", 0) > 0:
            self._local.depth += 1
            return self

        start_time = time.time()
        while True:
            try:
                fd = os.open(self.lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(fd, str(os.getpid()).encode())
                self._local.fd = fd
                break
            except OSError as e:
                if e.errno in (errno.EEXIST, errno.EACCES):
                    try:
                        if os.path.exists(self.lock_path):
                            os.remove(self.lock_path)
                    except OSError:
                        try:
                            if os.path.exists(self.lock_path):
                                with open(self.lock_path, "r") as lf:
                                    content = lf.read().strip()
                                if content.isdigit():
                                    pid = int(content)
                                    if not self._is_pid_running(pid):
                                        try:
                                            os.remove(self.lock_path)
                                        except OSError:
                                            pass
                        except Exception:
                            pass

                    if time.time() - start_time >= self.timeout:
                        raise TimeoutError(f"Lock acquire timeout on {self.lock_path}")
                    time.sleep(self.delay)
                else:
                    raise
        self._local.depth = 1
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._local.depth -= 1
        if self._local.depth == 0:
            fd = getattr(self._local, "fd", None)
            if fd is not None:
                try:
                    os.close(fd)
                except OSError:
                    pass
                self._local.fd = None
            try:
                if os.path.exists(self.lock_path):
                    os.remove(self.lock_path)
            except OSError:
                pass


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
    evaluation_result: str = Field(default="FAIL", pattern="^(PASS|FAIL)$")
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
    version: int = Field(default=1)
    score: int = Field(default=0, ge=0, le=100, description="Evaluation score 0-100")
    readiness_percent: int = Field(default=0, ge=0, le=100)
    status: str = Field(default="fail", pattern="^(pass|borderline|fail)$", description="pass | fail | borderline")
    candidate_name: str = Field(default="")
    task_title: str = Field(default="")
    reviewed_by: Optional[str] = Field(None)
    whats_done_well: list[str] = Field(default_factory=list)

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


# Hybrid DB + File fallback storage implementation
class ProductStorage:
    """
    Unified database repository mapping standard operations.
    Falls back to in-memory JSON file store for backward compatibility.
    """
    def __init__(self, persistence_file: str = "storage/product_state.json"):
        self.submissions: Dict[str, TaskSubmission] = {}
        self.reviews: Dict[str, ReviewRecord] = {}
        self.next_tasks: Dict[str, NextTaskRecord] = {}
        self.persistence_file = persistence_file
        self.lock_file = persistence_file + ".lock"
        self._file_lock = FileLock(self.lock_file)
        os.makedirs(os.path.dirname(self.persistence_file), exist_ok=True)
        
        self.use_db = (persistence_file == "storage/product_state.json")
        
        # Initalize schema on boot
        if self.use_db:
            try:
                init_db()
            except Exception as e:
                logger.warning(f"Database initialization failed: {e}")
            
        self._load()

    def lock(self) -> FileLock:
        """Expose lock context manager."""
        return self._file_lock
    
    def _save_nolock(self) -> None:
        """Persist storage to disk atomically without acquiring lock."""
        try:
            data = {
                "submissions": {k: v.model_dump(mode='json') for k, v in self.submissions.items()},
                "reviews": {k: v.model_dump(mode='json') for k, v in self.reviews.items()},
                "next_tasks": {k: v.model_dump(mode='json') for k, v in self.next_tasks.items()}
            }
            tmp_file = self.persistence_file + ".tmp"
            with open(tmp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_file, self.persistence_file)
        except Exception as e:
            print(f"Failed to save storage: {e}")

    def _load_nolock(self) -> None:
        """Load storage from disk without acquiring lock."""
        if not os.path.exists(self.persistence_file):
            return
        try:
            with open(self.persistence_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.submissions.clear()
                self.reviews.clear()
                self.next_tasks.clear()
                for k, v in data.get("submissions", {}).items():
                    self.submissions[k] = TaskSubmission(**v)
                for k, v in data.get("reviews", {}).items():
                    self.reviews[k] = ReviewRecord(**v)
                for k, v in data.get("next_tasks", {}).items():
                    self.next_tasks[k] = NextTaskRecord(**v)
        except Exception as e:
            print(f"Failed to load storage: {e}")

    def _save(self) -> None:
        """Persist storage to disk with locking."""
        with self._file_lock:
            self._save_nolock()

    def _load(self) -> None:
        """Load storage from disk with locking."""
        with self._file_lock:
            self._load_nolock()

    def store_submission(self, submission: TaskSubmission) -> None:
        """Store task submission"""
        # Save to file (backward compatibility fallback)
        with self._file_lock:
            self._load_nolock()
            self.submissions[submission.submission_id] = submission
            
            # Enforce 1000 submissions limit
            if len(self.submissions) > 1000:
                keys = sorted(self.submissions.keys(), key=lambda k: self.submissions[k].submitted_at)
                to_evict = keys[:len(self.submissions) - 1000]
                for k in to_evict:
                    self.submissions.pop(k, None)
                    rev_keys_to_remove = [rk for rk, rv in self.reviews.items() if rv.submission_id == k]
                    for rk in rev_keys_to_remove:
                        self.reviews.pop(rk, None)
                    nt_keys_to_remove = [nk for nk, nv in self.next_tasks.items() if nv.previous_submission_id == k]
                    for nk in nt_keys_to_remove:
                        self.next_tasks.pop(nk, None)
            
            self._save_nolock()

        # Save to DB
        if self.use_db:
            try:
                db = SessionLocal()
                db_obj = db.query(TaskSubmissionModel).filter(TaskSubmissionModel.submission_id == submission.submission_id).first()
                if not db_obj:
                    db_obj = TaskSubmissionModel(submission_id=submission.submission_id)
                
                db_obj.task_id = submission.task_id
                db_obj.task_title = submission.task_title
                db_obj.task_description = submission.task_description
                db_obj.submitted_by = submission.submitted_by
                db_obj.submitted_at = submission.submitted_at
                db_obj.status = submission.status
                db_obj.previous_task_id = submission.previous_task_id
                db_obj.pdf_file_path = submission.pdf_file_path
                db_obj.pdf_extracted_text = submission.pdf_extracted_text
                db_obj.module_id = submission.module_id
                db_obj.schema_version = submission.schema_version
                db_obj.registry_validation_status = submission.registry_validation_status
                db_obj.registry_validation_reason = submission.registry_validation_reason
                db_obj.review_state = submission.review_state

                db.add(db_obj)
                
                # Auto-register builder in database
                builder_obj = db.query(Builder).filter(Builder.id == submission.submitted_by).first()
                if not builder_obj:
                    builder_obj = Builder(id=submission.submitted_by, name=submission.submitted_by)
                    db.add(builder_obj)

                db.commit()
                db.close()
            except Exception as e:
                logger.error(f"Failed to store submission in DB: {e}")
    
    def store_review(self, review: ReviewRecord) -> None:
        """Store review record"""
        with self._file_lock:
            self._load_nolock()
            self.reviews[review.review_id] = review
            self._save_nolock()

        if self.use_db:
            try:
                db = SessionLocal()
                db_obj = db.query(ReviewModel).filter(ReviewModel.review_id == review.review_id).first()
                if not db_obj:
                    db_obj = ReviewModel(review_id=review.review_id)
                
                db_obj.submission_id = review.submission_id
                db_obj.trace_id = review.trace_id
                db_obj.evaluation_result = review.evaluation_result
                db_obj.score = review.score
                db_obj.readiness_percent = review.readiness_percent
                db_obj.status = review.status
                db_obj.decision = review.decision
                db_obj.reviewed_by = getattr(review, "reviewed_by", None) or "system"
                db_obj.reviewed_at = review.reviewed_at
                db_obj.evaluation_time_ms = review.evaluation_time_ms
                db_obj.evaluation_summary = review.evaluation_summary
                db_obj.review_state = review.review_state
                db_obj.version = review.version
                db_obj.candidate_name = review.candidate_name
                db_obj.task_title = review.task_title

                # Serialize lists and dicts
                db_obj.failure_reasons = json.dumps(review.failure_reasons)
                db_obj.improvement_hints = json.dumps(review.improvement_hints)
                db_obj.analysis = json.dumps(review.analysis)
                db_obj.missing_features = json.dumps(review.missing_features)

                db.add(db_obj)
                db.commit()
                db.close()
            except Exception as e:
                logger.error(f"Failed to store review in DB: {e}")
    
    def store_next_task(self, next_task: NextTaskRecord) -> None:
        """Store next task record"""
        with self._file_lock:
            self._load_nolock()
            self.next_tasks[next_task.next_task_id] = next_task
            self._save_nolock()

        if self.use_db:
            try:
                db = SessionLocal()
                db_obj = db.query(AssignmentModel).filter(AssignmentModel.id == next_task.next_task_id).first()
                if not db_obj:
                    db_obj = AssignmentModel(id=next_task.next_task_id)
                
                db_obj.next_task_id = next_task.next_task_id
                db_obj.review_id = next_task.review_id
                db_obj.previous_submission_id = next_task.previous_submission_id
                db_obj.task_type = next_task.task_type
                db_obj.title = next_task.title
                db_obj.objective = next_task.objective
                db_obj.focus_area = next_task.focus_area
                db_obj.difficulty = next_task.difficulty
                db_obj.reason = next_task.reason
                db_obj.assigned_at = next_task.assigned_at
                db_obj.status = "assigned"

                db.add(db_obj)
                db.commit()
                db.close()
            except Exception as e:
                logger.error(f"Failed to store next task in DB: {e}")
    
    def get_submission(self, submission_id: str) -> Optional[TaskSubmission]:
        """Retrieve submission by ID"""
        if self.use_db:
            try:
                db = SessionLocal()
                row = db.query(TaskSubmissionModel).filter(TaskSubmissionModel.submission_id == submission_id).first()
                if row:
                    if row.deleted_at is not None:
                        db.close()
                        return None
                    res = TaskSubmission(
                        submission_id=row.submission_id,
                        task_id=row.task_id,
                        task_title=row.task_title,
                        task_description=row.task_description,
                        submitted_by=row.submitted_by,
                        submitted_at=row.submitted_at,
                        status=row.status,
                        previous_task_id=row.previous_task_id,
                        pdf_file_path=row.pdf_file_path,
                        pdf_extracted_text=row.pdf_extracted_text,
                        module_id=row.module_id,
                        schema_version=row.schema_version,
                        registry_validation_status=row.registry_validation_status,
                        registry_validation_reason=row.registry_validation_reason,
                        review_state=row.review_state
                    )
                    db.close()
                    return res
                db.close()
            except Exception as e:
                logger.error(f"Failed to read submission from DB: {e}")

        with self._file_lock:
            self._load_nolock()
            return self.submissions.get(submission_id)
    
    def get_review(self, review_id: str) -> Optional[ReviewRecord]:
        """Retrieve review by ID"""
        mem_review = None
        with self._file_lock:
            self._load_nolock()
            mem_review = self.reviews.get(review_id)

        if self.use_db:
            try:
                db = SessionLocal()
                row = db.query(ReviewModel).filter(ReviewModel.review_id == review_id).first()
                if row:
                    if row.deleted_at is not None:
                        db.close()
                        return None
                    def _dejson(val, default):
                        if val is None:
                            return default
                        if isinstance(val, (list, dict)):
                            return val
                        try:
                            return json.loads(val)
                        except Exception:
                            return default
                    res = ReviewRecord(
                        review_id=row.review_id,
                        submission_id=row.submission_id,
                        trace_id=row.trace_id or (mem_review.trace_id if mem_review else ""),
                        evaluation_result=row.evaluation_result,
                        failure_type=getattr(mem_review, "failure_type", None) if mem_review else None,
                        decision=row.decision,
                        failure_reasons=_dejson(row.failure_reasons, getattr(mem_review, "failure_reasons", []) if mem_review else []),
                        improvement_hints=_dejson(row.improvement_hints, getattr(mem_review, "improvement_hints", []) if mem_review else []),
                        analysis=_dejson(row.analysis, getattr(mem_review, "analysis", {}) if mem_review else {}),
                        reviewed_at=row.reviewed_at,
                        evaluation_time_ms=row.evaluation_time_ms or 0,
                        missing_features=_dejson(row.missing_features, getattr(mem_review, "missing_features", []) if mem_review else []),
                        evaluation_summary=row.evaluation_summary or (mem_review.evaluation_summary if mem_review else ""),
                        selected_task_id=getattr(mem_review, "selected_task_id", "") if mem_review else "",
                        selection_reason=getattr(mem_review, "selection_reason", "") if mem_review else "",
                        review_state=row.review_state or "PENDING_REVIEW",
                        version=row.version or 1,
                        score=row.score or 0,
                        readiness_percent=row.readiness_percent or 0,
                        status=row.status or "fail",
                        candidate_name=row.candidate_name or "",
                        task_title=row.task_title or "",
                        reviewed_by=row.reviewed_by or "system",
                        whats_done_well=getattr(mem_review, "whats_done_well", []) if mem_review else []
                    )
                    db.close()
                    return res
                db.close()
            except Exception as e:
                logger.error(f"Failed to read review from DB: {e}")

        with self._file_lock:
            self._load_nolock()
            return self.reviews.get(review_id)
    
    def get_next_task(self, next_task_id: str) -> Optional[NextTaskRecord]:
        """Retrieve next task by ID"""
        if self.use_db:
            try:
                db = SessionLocal()
                row = db.query(AssignmentModel).filter(AssignmentModel.id == next_task_id).first()
                if row:
                    if row.deleted_at is not None:
                        db.close()
                        return None
                    res = NextTaskRecord(
                        next_task_id=row.next_task_id,
                        review_id=row.review_id or "",
                        previous_submission_id=row.previous_submission_id or "",
                        task_type=row.task_type,
                        title=row.title,
                        objective=row.objective,
                        focus_area=row.focus_area,
                        difficulty=row.difficulty,
                        reason=row.reason or "",
                        assigned_at=row.assigned_at
                    )
                    db.close()
                    return res
                db.close()
            except Exception as e:
                logger.error(f"Failed to read next task from DB: {e}")

        with self._file_lock:
            self._load_nolock()
            return self.next_tasks.get(next_task_id)
    
    def get_review_by_submission(self, submission_id: str) -> Optional[ReviewRecord]:
        """Retrieve review by submission ID"""
        mem_review = None
        with self._file_lock:
            self._load_nolock()
            for r in self.reviews.values():
                if r.submission_id == submission_id:
                    mem_review = r
                    break

        if self.use_db:
            try:
                db = SessionLocal()
                row = db.query(ReviewModel).filter(ReviewModel.submission_id == submission_id).first()
                if row:
                    if row.deleted_at is not None:
                        db.close()
                        return None
                    def _dejson(val, default):
                        if val is None:
                            return default
                        if isinstance(val, (list, dict)):
                            return val
                        try:
                            return json.loads(val)
                        except Exception:
                            return default
                    res = ReviewRecord(
                        review_id=row.review_id,
                        submission_id=row.submission_id,
                        trace_id=row.trace_id or (mem_review.trace_id if mem_review else ""),
                        evaluation_result=row.evaluation_result,
                        failure_type=getattr(mem_review, "failure_type", None) if mem_review else None,
                        decision=row.decision,
                        failure_reasons=_dejson(row.failure_reasons, getattr(mem_review, "failure_reasons", []) if mem_review else []),
                        improvement_hints=_dejson(row.improvement_hints, getattr(mem_review, "improvement_hints", []) if mem_review else []),
                        analysis=_dejson(row.analysis, getattr(mem_review, "analysis", {}) if mem_review else {}),
                        reviewed_at=row.reviewed_at,
                        evaluation_time_ms=row.evaluation_time_ms or 0,
                        missing_features=_dejson(row.missing_features, getattr(mem_review, "missing_features", []) if mem_review else []),
                        evaluation_summary=row.evaluation_summary or (mem_review.evaluation_summary if mem_review else ""),
                        selected_task_id=getattr(mem_review, "selected_task_id", "") if mem_review else "",
                        selection_reason=getattr(mem_review, "selection_reason", "") if mem_review else "",
                        review_state=row.review_state or "PENDING_REVIEW",
                        version=row.version or 1,
                        score=row.score or 0,
                        readiness_percent=row.readiness_percent or 0,
                        status=row.status or "fail",
                        candidate_name=row.candidate_name or "",
                        task_title=row.task_title or "",
                        reviewed_by=row.reviewed_by or "system",
                        whats_done_well=getattr(mem_review, "whats_done_well", []) if mem_review else []
                    )
                    db.close()
                    return res
                db.close()
            except Exception as e:
                logger.error(f"Failed to find review by submission in DB: {e}")

        with self._file_lock:
            self._load_nolock()
            for review in self.reviews.values():
                if review.submission_id == submission_id:
                    return review
            return None
    
    def get_next_task_by_submission(self, submission_id: str) -> Optional[NextTaskRecord]:
        """Find next task assigned after submission"""
        if self.use_db:
            try:
                db = SessionLocal()
                row = db.query(AssignmentModel).filter(AssignmentModel.previous_submission_id == submission_id).first()
                if row:
                    if row.deleted_at is not None:
                        db.close()
                        return None
                    res = NextTaskRecord(
                        next_task_id=row.next_task_id,
                        review_id=row.review_id or "",
                        previous_submission_id=row.previous_submission_id or "",
                        task_type=row.task_type,
                        title=row.title,
                        objective=row.objective,
                        focus_area=row.focus_area,
                        difficulty=row.difficulty,
                        reason=row.reason or "",
                        assigned_at=row.assigned_at
                    )
                    db.close()
                    return res
                db.close()
            except Exception as e:
                logger.error(f"Failed to find next task by submission in DB: {e}")

        with self._file_lock:
            self._load_nolock()
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
        with self._file_lock:
            self.submissions.clear()
            self.reviews.clear()
            self.next_tasks.clear()
            try:
                if os.path.exists(self.persistence_file):
                    os.remove(self.persistence_file)
            except Exception:
                pass

        if self.use_db:
            try:
                db = SessionLocal()
                from db.models import (
                    EvidenceModel, ArtifactModel, DimensionResultModel, RiskRegisterModel,
                    AssignmentModel, Repository, CertificationModel, HistoricalMetricModel,
                    ProductParticipationModel, TraceSessionModel, ReplayRecordModel,
                    AuditLogModel, GovernanceRecordModel, DecisionLedgerModel,
                    ReviewModel, TaskSubmissionModel, Builder, Product
                )
                
                # Delete child/referencing tables first
                db.query(EvidenceModel).delete()
                db.query(ArtifactModel).delete()
                db.query(DimensionResultModel).delete()
                db.query(RiskRegisterModel).delete()
                db.query(AssignmentModel).delete()
                db.query(Repository).delete()
                db.query(CertificationModel).delete()
                db.query(HistoricalMetricModel).delete()
                db.query(ProductParticipationModel).delete()
                db.query(TraceSessionModel).delete()
                db.query(ReplayRecordModel).delete()
                db.query(AuditLogModel).delete()
                db.query(GovernanceRecordModel).delete()
                db.query(DecisionLedgerModel).delete()
                
                # Delete parent tables
                db.query(ReviewModel).delete()
                db.query(TaskSubmissionModel).delete()
                db.query(Builder).delete()
                db.query(Product).delete()
                
                db.commit()
                db.close()
            except Exception as e:
                logger.error(f"Failed to clear all tables in DB: {e}")


# Global storage instance
product_storage = ProductStorage()
