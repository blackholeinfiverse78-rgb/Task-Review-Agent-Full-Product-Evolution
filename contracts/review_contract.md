# Review Contract (Intake Contract)

- **Version**: 1.0.0
- **Status**: FROZEN / CORE-LOCKED
- **Ownership Boundary**: Owned by `api/production.py` and `task_selector/niyantran_connection.py`.

---

## 1. Purpose
Defines the boundary and interface specifications for task ingestion. Any consumer (e.g., Niyantran, HackaVerse, or external products) must submit tasks following this schema. Ingestion is non-blocking and does not execute mutations to the persistent ledger until human governor verification is complete.

---

## 2. Inputs
Consumers must submit a `POST` request to `/api/v1/production/niyantran/submit` with a JSON payload matching the following specification:

| Field | Type | Required | Constraints | Description |
| :--- | :--- | :--- | :--- | :--- |
| `task_id` | String | Yes | Min 1, Max 100 chars | Unique task identifier |
| `task_title` | String | Yes | Min 5, Max 200 chars | Describing the engineering task |
| `task_description` | String | Yes | Min 10, Max 10000 chars | The instructions and constraints |
| `submitted_by` | String | Yes | Min 2, Max 50 chars | Candidate handle or name |
| `repository_url` | String | No | Valid URL pattern | GitHub repository link (optional) |
| `module_id` | String | No | Default: `"task-review-agent"` | Identifier for registry validation |
| `schema_version` | String | No | Default: `"v1.0"` | Schema compatibility version |
| `pdf_text` | String | No | Default: `""` | Extracted text from PDF context |
| `trace_id` | String | Yes | Min 8 chars | Upstream trace identifier (preserved) |
| `priority` | String | No | Default: `"normal"` | Priority tier |
| `current_task_id` | String | No | Default: `None` | Precursor task in the Niyantran graph |

### Sample Input Payload
```json
{
  "task_id": "T-GOV-001",
  "task_title": "REST API with Layered Architecture",
  "task_description": "Objective: Build a production-ready REST API service.",
  "submitted_by": "Ishan Shirode",
  "repository_url": "https://github.com/blackholeinfiverse78-rgb/task-repo",
  "module_id": "task-review-agent",
  "schema_version": "v1.0",
  "trace_id": "trace-a3f2c1d48b9e4f2a"
}
```

---

## 3. Outputs
On successful validation and execution, the system issues a queued receipt:

| Field | Type | Description |
| :--- | :--- | :--- |
| `trace_id` | String | Inherited from request, unmodified |
| `submission_id` | String | Unique evaluation runtime sequence identifier |
| `review_state` | String | Static value: `"PENDING_REVIEW"` |
| `status` | String | Static value: `"QUEUED"` |
| `message` | String | Acknowledgment message |

### Sample Output Payload
```json
{
  "trace_id": "trace-a3f2c1d48b9e4f2a",
  "submission_id": "sub-eb2e07e7c652-d42768ed",
  "review_state": "PENDING_REVIEW",
  "status": "QUEUED",
  "message": "Evaluation complete. Pending human approval for final assignment."
}
```

---

## 4. Failure States
All intake violations are caught at entry. No system crashes (500s) are permitted; failures must map to structured JSON responses.

### 4.1 Validation Failure (HTTP 422)
Triggered when fields violate length constraints or are whitespace-only.
- **Payload**:
  ```json
  {
    "score": 0,
    "readiness_percent": 0,
    "status": "fail",
    "failure_reasons": ["Validation Failure", "task_title: Field cannot be empty or just whitespace"],
    "improvement_hints": ["Ensure all fields meet length requirements."],
    "analysis": { "technical_quality": 0, "clarity": 0, "discipline_signals": 0 },
    "meta": { "evaluation_time_ms": 0, "mode": "rule" }
  }
  ```

### 4.2 Missing Trace ID / Internal Rule Violations (HTTP 400)
Triggered when `trace_id` is missing, too short, or if hard gates fail.
- **Payload**:
  ```json
  {
    "detail": "HARD REJECT: trace_id missing or too short from upstream.",
    "error_code": "TRACE_ID_MISSING",
    "timestamp": "2026-06-12T08:24:00Z"
  }
  ```

---

## 5. Versioning Rules
- **Schema Key**: `schema_version` in ingestion payload.
- **Incremental Path**: Major version bumps represent breaking schema changes. Minor version updates must be backward-compatible (e.g., adding optional metadata fields).

---

## 6. Compatibility Rules
- **Backward Compatibility**: Older client versions sending `"v1.0"` are accepted. Field additions must always contain default values.
- **Forward Compatibility**: Reject unknown properties if the schema version is bumped to a higher major version.

---

## 7. Ownership Boundary
- **Parikshak Boundary**: Validates structures, extracts keywords, crawls GitHub repositories, parses `REVIEW_PACKET.md`, runs evaluations, calculates confidence, and stages the review in the escalation directory.
- **Consumer Boundary**: Responsible for supplying a monotonic `trace_id`, valid repository link, and correct inputs.
