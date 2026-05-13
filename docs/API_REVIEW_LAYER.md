# API Documentation — Human Review & Approval Layer

All endpoints are served from `http://localhost:8000`.
Interactive docs: `http://localhost:8000/docs`

---

## Submission Endpoint

### POST `/api/v1/production/niyantran/submit`

Accepts a task submission, runs evaluation and task selection, and queues the result for human review. Nothing is sent to Niyantran at this stage.

**Request Body:**
```json
{
  "task_id":          "T-GOV-001",
  "task_title":       "Build REST API with Authentication",
  "task_description": "Implemented a complete REST API with JWT...",
  "submitted_by":     "Akash Kumar",
  "repository_url":   "https://github.com/user/repo",
  "module_id":        "task-review-agent",
  "schema_version":   "v1.0",
  "pdf_text":         "",
  "trace_id":         "trace-abc123def456",
  "current_task_id":  "T-GOV-001"
}
```

**Field constraints:**
- `trace_id`: required, minimum 8 characters
- `task_title`: 5–200 characters
- `task_description`: 10–10000 characters
- `submitted_by`: 2–50 characters

**Success Response `200`:**
```json
{
  "trace_id":      "trace-abc123def456",
  "submission_id": "sub-eb2e07e7c652-ef456",
  "review_state":  "PENDING_REVIEW",
  "status":        "QUEUED",
  "message":       "Evaluation complete. Pending human approval for final assignment."
}
```

**Hard Reject Response `200` (structured):**
```json
{
  "error":   "TRACE_ID_MISSING",
  "trace_id": null,
  "status":  "REJECTED",
  "details": "HARD REJECT: trace_id missing or too short"
}
```

---

## Review Queue Endpoints

### GET `/api/v1/review/all`

Returns all submissions with their current review state.

**Response `200`:**
```json
[
  {
    "submission_id":     "sub-eb2e07e7c652-ef456",
    "candidate_name":    "Akash Kumar",
    "task_title":        "Build REST API with Authentication",
    "evaluation_result": "PASS",
    "failure_type":      null,
    "selected_task_id":  "T-GOV-002",
    "trace_id":          "trace-abc123def456",
    "review_state":      "PENDING_REVIEW",
    "selection_reason":  "PASS -> next_tasks[0] = T-GOV-002",
    "full_response":     { ... }
  }
]
```

---

### GET `/api/v1/review/pending`

Returns only submissions in `PENDING_REVIEW` state.

**Response `200`:** Same shape as `/all`, filtered to `review_state == "PENDING_REVIEW"`.

---

## Approval Endpoints

### POST `/api/v1/review/approve`

Approves the system's deterministic recommendation. Sets state to `APPROVED`. Writes audit log.

**Request Body:**
```json
{
  "trace_id":      "trace-abc123def456",
  "submission_id": "sub-eb2e07e7c652-ef456",
  "action":        "approve"
}
```

**Success Response `200`:**
```json
{
  "status":        "APPROVED",
  "submission_id": "sub-eb2e07e7c652-ef456",
  "assigned_task": "T-GOV-002"
}
```

**Error Responses:**
- `404` — submission_id not found
- `409` — submission already actioned (not in PENDING_REVIEW)

---

### POST `/api/v1/review/reject`

Rejects the submission. No task is assigned. Sets state to `REJECTED`. Writes audit log.

**Request Body:**
```json
{
  "trace_id":      "trace-abc123def456",
  "submission_id": "sub-eb2e07e7c652-ef456",
  "action":        "reject"
}
```

**Success Response `200`:**
```json
{
  "status":        "REJECTED",
  "submission_id": "sub-eb2e07e7c652-ef456"
}
```

**Error Responses:**
- `404` — submission_id not found
- `409` — submission already actioned

---

### POST `/api/v1/review/modify`

Overrides the system's task recommendation with a human-specified task. Sets state to `MODIFIED`. Writes audit log with both original and override task.

**Request Body:**
```json
{
  "trace_id":         "trace-abc123def456",
  "submission_id":    "sub-eb2e07e7c652-ef456",
  "action":           "modify",
  "override_task_id": "T-GOV-005"
}
```

**Success Response `200`:**
```json
{
  "status":        "MODIFIED",
  "submission_id": "sub-eb2e07e7c652-ef456",
  "assigned_task": "T-GOV-005"
}
```

**Error Responses:**
- `400` — override_task_id missing
- `404` — submission_id not found
- `409` — submission already actioned

---

## Hard Rules Enforced by API Layer

| Rule | Enforcement |
|---|---|
| No action on already-actioned submission | 409 on approve/reject/modify if `review_state != PENDING_REVIEW` |
| No modify without override task | 400 on modify if `override_task_id` is null or empty |
| No submission without trace_id | 422 from Pydantic if `trace_id` missing or < 8 chars |
| No evaluation rerun | approve/reject/modify contain zero calls to evaluation engine |
| No selector rerun | approve/reject/modify contain zero calls to task graph engine |

---

## Audit Log

Every action (approve, reject, modify) writes one entry to:
`storage/audit_logs/audit_YYYY-MM-DD.jsonl`

**Schema:**
```json
{
  "trace_id":      "trace-abc123def456",
  "submission_id": "sub-eb2e07e7c652-ef456",
  "system_task":   "T-GOV-002",
  "final_task":    "T-GOV-005",
  "action":        "modify",
  "timestamp":     "2026-05-07 17:00:08.227760"
}
```

- `system_task` — what the deterministic engine selected
- `final_task` — what was actually assigned (`NONE` for reject, `override_task_id` for modify)
- File opened in append mode `"a"` — no entry is ever overwritten
