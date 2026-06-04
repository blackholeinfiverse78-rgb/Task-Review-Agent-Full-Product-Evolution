# Parikshak Integration Surface Document

This document lists all active APIs, routes, schemas, input/output structures, storage schemas, and integration adapter contracts in Parikshak today.

---

## 1. REST API Endpoints

### 1.1 Niyantran Production Route
- **Endpoint**: `POST /api/v1/production/niyantran/submit`
- **Purpose**: Evaluates submissions received from Niyantran and returns the transaction trace and a `PENDING_REVIEW` queue status.
- **Request Format** (JSON):
```json
{
  "task_id": "T-GOV-001",
  "task_title": "Implement API Authorization System",
  "task_description": "Requirement: Add role-based check routes. Objective: Enforce security.",
  "submitted_by": "Akash Dev",
  "repository_url": "https://github.com/developer/sec-auth",
  "module_id": "task-review-agent",
  "schema_version": "v1.0",
  "pdf_text": "",
  "trace_id": "trace-niyantran-12345678",
  "priority": "normal",
  "deadline": "2026-06-15T00:00:00Z",
  "current_task_id": "T-GOV-001"
}
```
- **Response Format** (JSON):
```json
{
  "trace_id": "trace-niyantran-12345678",
  "submission_id": "sub-a3c9e2b109d7-12345678",
  "review_state": "PENDING_REVIEW",
  "status": "QUEUED",
  "message": "Evaluation complete. Pending human approval for final assignment."
}
```

- **Endpoint**: `GET /api/v1/production/niyantran/health`
- **Response**:
```json
{
  "status": "healthy",
  "service": "niyantran_connection",
  "version": "2.0",
  "timestamp": "2026-06-04T12:58:22Z",
  "bucket_stats": {
    "total_evaluations": 1,
    "avg_score": 80.0,
    "avg_confidence": 0.95
  }
}
```

---

### 1.2 Human Review Operations Routes
- **Endpoint**: `GET /api/v1/production/human-review/pending`
- **Response**:
```json
{
  "pending_count": 1,
  "cases": [
    {
      "case_id": "esc-20260604120000-trace123",
      "trace_id": "trace-niyantran-12345678",
      "timestamp": "2026-06-04T12:00:00Z",
      "confidence": 0.725,
      "reasons": ["low_confidence", "no_proof"],
      "evaluation_result": "FAIL",
      "failure_type": "incomplete",
      "decision": "REJECTED"
    }
  ],
  "timestamp": "2026-06-04T12:58:22Z"
}
```

- **Endpoint**: `POST /api/v1/production/human-review/override`
- **Request Format** (JSON):
```json
{
  "case_id": "esc-20260604120000-trace123",
  "reviewer": "Vinayak",
  "override_decision": {
    "evaluation_result": "PASS",
    "failure_type": null,
    "decision": "APPROVED"
  },
  "review_notes": "Manually verified repository files; tests exist in test/ directory and cover constraints."
}
```
- **Response**:
```json
{
  "status": "override_applied",
  "case_id": "esc-20260604120000-trace123",
  "reviewer": "Vinayak",
  "result": {
    "evaluation_result": "PASS",
    "failure_type": null,
    "decision": "APPROVED",
    "human_override_applied": true,
    "human_reviewer": "Vinayak",
    "human_review_notes": "Manually verified repository files...",
    "original_confidence": 0.725,
    "override_confidence": 1.0,
    "escalation_resolved": true
  },
  "timestamp": "2026-06-04T12:58:22Z"
}
```

---

### 1.3 Gov-OS System Operations
- **Endpoint**: `POST /api/v1/gov-os/mutate`
- **Request Format** (JSON):
```json
{
  "envelope": {
    "trace_id": "trace-niyantran-12345678",
    "schema_version": "v1.0",
    "actor": "operator-1",
    "actor_role": "operator",
    "event_type": "assignment_history",
    "payload": {
      "assignment_id": "asg-001",
      "task_id": "T-GOV-002",
      "candidate_id": "cand-001",
      "assigned_by": "Akash",
      "assigned_at": "2026-06-04T12:58:22Z"
    },
    "authorized_by": "Akash",
    "approval_token": "token-sig-xyz",
    "payload_checksum": "a7b3c2d1...",
    "parent_event_hash": "e3b0c442..."
  },
  "executor_actor": "Parikshak"
}
```

---

### 1.4 Standalone Text-to-Speech (TTS)
- **Endpoint**: `GET /api/v1/tts/speak`
- **Parameters**: `text` (string, required), `lang` (string, default "en"), `tone` (string, default "neutral"), `translate` (bool, default false)
- **Response**: Binary audio file content (`audio/mpeg` or `audio/wav`).

---

### 1.5 HackaVerse Backwards-Compatible review Route
- **Endpoint**: `POST /parikshak/review`
- **Request** (JSON or Form):
```json
{
  "title": "API Authentication",
  "description": "Requirement: Add role-based authentication check routes. Objective: Enforce security.",
  "submitted_by": "Ishan",
  "repo_url": "https://github.com/developer/auth-api",
  "trace_id": "trace-hv-demo-001"
}
```
- **Response**:
```json
{
  "status": "PASS",
  "review": "Task evaluation passed successfully. Requirements are fully satisfied...",
  "score": 85,
  "next_task": "T-GOV-002",
  "trace_id": "trace-hv-demo-001"
}
```

---

## 2. Frozen Database Event Schemas

The following entities are registered in the `FrozenRegistry` in `canonical_db/contracts.py` and appended to the SQL event journal payload:

```python
class CandidateProfile(BaseModel):
    candidate_id: str
    name: str
    github_handle: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    performance_score: float = 0.0

class TaskLineage(BaseModel):
    task_id: str
    parent_task_id: Optional[str] = None
    child_task_ids: List[str] = Field(default_factory=list)
    evolution_stage: str

class ReviewHistory(BaseModel):
    review_id: str
    submission_id: str
    status: str
    score: float
    reviewed_by: str
    reviewed_at: str

class AssignmentHistory(BaseModel):
    assignment_id: str
    task_id: str
    candidate_id: str
    assigned_by: str
    assigned_at: str
```

---

## 3. Storage Interfaces

### 3.1 SQLite Event Journal (`canonical_db.sqlite`)
- **Table**: `events`
- **Schema**:
```sql
CREATE TABLE events (
    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT UNIQUE NOT NULL,
    trace_id TEXT NOT NULL,
    schema_version TEXT NOT NULL,
    actor TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    event_type TEXT NOT NULL,
    lineage_reference TEXT,
    payload TEXT NOT NULL,
    parent_event_hash TEXT NOT NULL,
    event_hash TEXT NOT NULL,
    checksum TEXT NOT NULL
);
```

### 3.2 Product Storage JSON (`product_state.json`)
- Flat JSON structure maintaining in-memory dictionaries:
  - `submissions`: Keyed by `submission_id` -> Pydantic `TaskSubmission`.
  - `reviews`: Keyed by `review_id` -> Pydantic `ReviewRecord`.
  - `next_tasks`: Keyed by `next_task_id` -> Pydantic `NextTaskRecord`.
