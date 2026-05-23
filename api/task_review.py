"""
Extended / Task Review API Route
Provides backwards compatibility for ad-hoc reviews (GitHub repo / PDF file / description evaluation).
"""
import re
import uuid
import requests
import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Form, File, UploadFile, HTTPException, Request

from contracts.schemas import Task
from task_selector.review_orchestrator import ReviewOrchestrator
from evaluation_engine.pdf_analyzer import PDFAnalyzer
from db.persistent_storage import product_storage

logger = logging.getLogger("task_review_api")
router = APIRouter(prefix="/api/v1/task", tags=["task"])

# CWE-918: URL validation regex
_GITHUB_URL_RE = re.compile(r"^https?://(www\.)?github\.com/[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+/?$")

orchestrator = ReviewOrchestrator()
pdf_analyzer = PDFAnalyzer()

@router.post("/submit")
async def submit_task(request: Request):
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        try:
            body = await request.json()
        except Exception:
            body = {}
    else:
        form_data = await request.form()
        body = dict(form_data)
        
    task_title = body.get("task_title") or body.get("title") or "Legacy Task"
    task_description = body.get("task_description") or body.get("description") or "Legacy Description"
    submitted_by = body.get("submitted_by") or "Anonymous"
    github_repo_link = body.get("github_repo_link") or body.get("github_url") or ""
    previous_task_id = body.get("previous_task_id")
    
    # Validation
    if len(task_title) < 5 or len(task_title) > 100:
        task_title = (task_title[:95] + "...") if len(task_title) > 100 else task_title
        if len(task_title) < 5:
            task_title = "Legacy Task Title"
            
    if len(task_description) < 10:
        task_description = "Legacy Task Description " + task_description
        
    task_id = f"task-legacy-{uuid.uuid4().hex[:12]}"
    task = Task(
        task_id=task_id,
        task_title=task_title,
        task_description=task_description,
        submitted_by=submitted_by,
        timestamp=datetime.now(),
        github_repo_link=github_repo_link,
        module_id="task-review-agent",
        schema_version="v1.0"
    )
    
    try:
        trace_id = f"trace-legacy-{uuid.uuid4().hex[:12]}"
        result = orchestrator.process_submission(
            task=task,
            previous_task_id=previous_task_id,
            trace_id=trace_id
        )
        return {
            "task_id": result["submission_id"],
            "status": "success",
            "submission_id": result["submission_id"]
        }
    except Exception as e:
        logger.error(f"Legacy submit failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/review")
async def review_task(
    request: Request,
    description: Optional[str] = Form(None),
    github_url: Optional[str] = Form(None),
    pdf_file: Optional[UploadFile] = File(None),
    submitted_by: Optional[str] = Form(None)
):
    # Check if request has JSON content-type
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        try:
            body = await request.json()
        except Exception:
            body = {}
        task_id = body.get("task_id")
        if task_id:
            # Look up task review in storage
            review = product_storage.get_review_by_submission(task_id)
            if not review:
                # Also check if it's the submission_id directly
                submission = product_storage.get_submission(task_id)
                if submission:
                    review = product_storage.get_review_by_submission(submission.submission_id)
            if not review:
                # Also check if task_id matches task_id attribute in submissions
                for sub in product_storage.submissions.values():
                    if sub.task_id == task_id:
                        review = product_storage.get_review_by_submission(sub.submission_id)
                        break
            if not review:
                raise HTTPException(status_code=404, detail="Task or review not found")
            return review
        
        description = body.get("description")
        github_url = body.get("github_url")
        submitted_by = body.get("submitted_by")

    # 1. Description validation
    if description is None:
        raise HTTPException(status_code=400, detail="Description is required")
    if not description.strip():
        raise HTTPException(status_code=400, detail="Description cannot be empty")
    if len(description.strip()) < 10:
        raise HTTPException(status_code=400, detail="Description must be at least 10 characters")

    # 2. GitHub URL validation and existence check
    if github_url:
        if not _GITHUB_URL_RE.match(github_url):
            raise HTTPException(status_code=400, detail="Invalid GitHub repository URL")
        
        match = re.search(r"github\.com/([^/]+)/([^/]+)", github_url)
        if not match:
            raise HTTPException(status_code=400, detail="Invalid GitHub repository URL")
        owner = match.group(1)
        repo = match.group(2).rstrip('/')
        if repo.endswith('.git'):
            repo = repo[:-4]
        api_url = f"https://api.github.com/repos/{owner}/{repo}"

        try:
            resp = requests.get(api_url, timeout=10)
            if resp.status_code == 404:
                raise HTTPException(status_code=404, detail="GitHub repository not found or is private")
        except requests.RequestException as e:
            logger.error(f"GitHub URL reachability check failed: {e}")
            raise HTTPException(status_code=404, detail="GitHub repository not found or is private")

    # 3. PDF File validation and parsing
    pdf_file_path = None
    pdf_text = ""
    if pdf_file:
        filename = pdf_file.filename or ""
        if not filename.lower().endswith(".pdf") or pdf_file.content_type != "application/pdf":
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")
        
        try:
            pdf_result = pdf_analyzer.process_upload(pdf_file)
            pdf_file_path = pdf_result.get("file_path")
            pdf_text = pdf_result.get("extracted_text", "")
        except Exception as e:
            logger.error(f"PDF processing failed: {e}")
            raise HTTPException(status_code=400, detail="Invalid or corrupt PDF file")

    # 4. Construct Task for the Orchestrator
    trace_id = f"trace-ext-{uuid.uuid4()}"
    task = Task(
        task_id=f"task-ext-{uuid.uuid4()}",
        task_title="Extended Evaluation Task",
        task_description=description,
        submitted_by=submitted_by or "Anonymous",
        timestamp=datetime.now(),
        github_repo_link=github_url or "",
        module_id="task-review-agent",
        schema_version="v1.0"
    )

    try:
        result = orchestrator.process_submission(
            task=task,
            pdf_file_path=pdf_file_path,
            pdf_extracted_text=pdf_text,
            trace_id=trace_id
        )
        return result["review"]
    except Exception as e:
        logger.error(f"Process submission failed: {e}")
        raise HTTPException(status_code=500, detail=f"Review process failed: {str(e)}")
