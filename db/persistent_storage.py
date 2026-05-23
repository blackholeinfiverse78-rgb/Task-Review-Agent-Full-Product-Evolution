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
import time
import errno
import threading


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
                    # Try to delete directly. If no process has the file descriptor open, this will succeed.
                    # On Windows, this is a very reliable way to check if the lock is actually held.
                    try:
                        if os.path.exists(self.lock_path):
                            os.remove(self.lock_path)
                    except OSError:
                        # If deletion fails, check if it's a stale lock using PID
                        try:
                            if os.path.exists(self.lock_path):
                                with open(self.lock_path, "r") as lf:
                                    content = lf.read().strip()
                                if content.isdigit():
                                    pid = int(content)
                                    if not self._is_pid_running(pid):
                                        # Stale lock file! Let's delete it.
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
    # Compatibility fields used by tests and history APIs
    score: int = Field(default=0, ge=0, le=100, description="Evaluation score 0-100")
    readiness_percent: int = Field(default=0, ge=0, le=100)
    status: str = Field(default="fail", pattern="^(pass|borderline|fail)$", description="pass | fail | borderline")
    candidate_name: str = Field(default="")
    task_title: str = Field(default="")

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


# In-memory storage with explicit structure and process-safe locking
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
        self.lock_file = persistence_file + ".lock"
        self._file_lock = FileLock(self.lock_file)
        os.makedirs(os.path.dirname(self.persistence_file), exist_ok=True)
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
        with self._file_lock:
            self._load_nolock()
            self.submissions[submission.submission_id] = submission
            
            # Enforce 1000 submissions limit
            if len(self.submissions) > 1000:
                keys = sorted(self.submissions.keys(), key=lambda k: self.submissions[k].submitted_at)
                to_evict = keys[:len(self.submissions) - 1000]
                for k in to_evict:
                    self.submissions.pop(k, None)
                    # Also evict corresponding reviews and next tasks
                    rev_keys_to_remove = [rk for rk, rv in self.reviews.items() if rv.submission_id == k]
                    for rk in rev_keys_to_remove:
                        self.reviews.pop(rk, None)
                    
                    nt_keys_to_remove = [nk for nk, nv in self.next_tasks.items() if nv.previous_submission_id == k]
                    for nk in nt_keys_to_remove:
                        self.next_tasks.pop(nk, None)
            
            self._save_nolock()
    
    def store_review(self, review: ReviewRecord) -> None:
        """Store review record"""
        with self._file_lock:
            self._load_nolock()
            self.reviews[review.review_id] = review
            self._save_nolock()
    
    def store_next_task(self, next_task: NextTaskRecord) -> None:
        """Store next task record"""
        with self._file_lock:
            self._load_nolock()
            self.next_tasks[next_task.next_task_id] = next_task
            self._save_nolock()
    
    def get_submission(self, submission_id: str) -> Optional[TaskSubmission]:
        """Retrieve submission by ID"""
        with self._file_lock:
            self._load_nolock()
            return self.submissions.get(submission_id)
    
    def get_review(self, review_id: str) -> Optional[ReviewRecord]:
        """Retrieve review by ID"""
        with self._file_lock:
            self._load_nolock()
            return self.reviews.get(review_id)
    
    def get_next_task(self, next_task_id: str) -> Optional[NextTaskRecord]:
        """Retrieve next task by ID"""
        with self._file_lock:
            self._load_nolock()
            return self.next_tasks.get(next_task_id)
    
    def get_review_by_submission(self, submission_id: str) -> Optional[ReviewRecord]:
        """Find review linked to submission"""
        with self._file_lock:
            self._load_nolock()
            for review in self.reviews.values():
                if review.submission_id == submission_id:
                    return review
            return None
    
    def get_next_task_by_submission(self, submission_id: str) -> Optional[NextTaskRecord]:
        """Find next task assigned after submission"""
        with self._file_lock:
            self._load_nolock()
            for next_task in self.next_tasks.values():
                if next_task.previous_submission_id == submission_id:
                    return next_task
            return None
    
    def get_lifecycle(self, submission_id: str) -> Optional[Dict[str, Any]]:
        """Get complete lifecycle for a submission"""
        with self._file_lock:
            self._load_nolock()
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


# Global storage instance
product_storage = ProductStorage()
