# Testing Documentation — Human Review Workflow

---

## Test Files

| File | Type | Requires Server |
|---|---|---|
| `tests/static_verification.py` | Static code analysis | No |
| `tests/test_review_workflow.py` | End-to-end HTTP tests | Yes (port 8000) |

---

## Static Verification

Verifies all integration points by inspecting source code and model definitions. No server required.

**Run:**
```bash
set PYTHONPATH=.
py -3 tests/static_verification.py
```

**Result:**
```
============================================================
STATIC VERIFICATION — HUMAN REVIEW WORKFLOW
============================================================
✓ CHECK 1:  ReviewRecord has all required fields
✓ CHECK 2:  ReviewState enum complete
✓ CHECK 3:  submit endpoint blocks at PENDING_REVIEW
✓ CHECK 4:  approve does NOT rerun evaluation/selection
✓ CHECK 5:  reject blocks assignment
✓ CHECK 6:  modify overrides without rerun
✓ CHECK 7:  audit log is append-only
✓ CHECK 8:  execution_pipeline stores trace_id correctly
✓ CHECK 9:  /review/all returns review.trace_id
✓ CHECK 10: audit log directory exists
✓ CHECK 11: AuditLogEntry schema complete
✓ CHECK 12: No auto-assignment bypass
✓ CHECK 13: ReviewRecord defaults to PENDING_REVIEW

ALL 13 CHECKS PASSED ✓
VERDICT: VERIFIED WORKING
```

---

## End-to-End Test Suite

Tests all 6 flows against a running server.

**Start server first:**
```bash
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

**Run:**
```bash
py -3 tests/test_review_workflow.py
```

### Test 1 — Submit Task
Submits a PASS-quality payload. Asserts response contains `review_state: PENDING_REVIEW` and `status: QUEUED`.

### Test 2 — View Pending
Calls `GET /api/v1/review/all`. Asserts response is a list. Prints each submission's candidate name and state.

### Test 3 — Approve
Gets first PENDING_REVIEW submission. Calls `POST /review/approve`. Asserts `status: APPROVED`.

### Test 4 — Reject
Submits a FAIL-quality payload. Calls `POST /review/reject`. Asserts `status: REJECTED`.

### Test 5 — Modify
Submits a new payload. Calls `POST /review/modify` with `override_task_id: T-GOV-999`. Asserts `status: MODIFIED` and `assigned_task: T-GOV-999`.

### Test 6 — Audit Log
Reads `storage/audit_logs/audit_YYYY-MM-DD.jsonl`. Prints last 3 entries. Asserts file exists and has entries.

---

## Manual Curl Tests

### Submit (PASS quality)
```bash
curl -X POST http://localhost:8000/api/v1/production/niyantran/submit \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "demo-001",
    "task_title": "E-Commerce REST API with Payment Integration",
    "task_description": "Built a complete e-commerce REST API with Stripe payment integration, user authentication using JWT, product catalog management, shopping cart functionality, order processing, and admin dashboard. Implemented comprehensive error handling, input validation, rate limiting, and security best practices. Repository includes 120+ unit tests with 92% code coverage, API documentation using Swagger/OpenAPI, Docker containerization, CI/CD pipeline configuration, and deployment guide.",
    "submitted_by": "Akash Kumar",
    "repository_url": "https://github.com/akash/ecommerce-api",
    "module_id": "task-review-agent",
    "schema_version": "v1.0",
    "pdf_text": "",
    "trace_id": "trace-demo-001-pass",
    "current_task_id": "T-GOV-001"
  }'
```

Expected: `"review_state": "PENDING_REVIEW"`

### Get All Reviews
```bash
curl http://localhost:8000/api/v1/review/all
```

### Get Pending Only
```bash
curl http://localhost:8000/api/v1/review/pending
```

### Approve
```bash
curl -X POST http://localhost:8000/api/v1/review/approve \
  -H "Content-Type: application/json" \
  -d '{
    "trace_id": "trace-demo-001-pass",
    "submission_id": "<submission_id from submit response>",
    "action": "approve"
  }'
```

Expected: `"status": "APPROVED"`

### Reject
```bash
curl -X POST http://localhost:8000/api/v1/review/reject \
  -H "Content-Type: application/json" \
  -d '{
    "trace_id": "trace-demo-002-fail",
    "submission_id": "<submission_id>",
    "action": "reject"
  }'
```

Expected: `"status": "REJECTED"`

### Modify
```bash
curl -X POST http://localhost:8000/api/v1/review/modify \
  -H "Content-Type: application/json" \
  -d '{
    "trace_id": "trace-demo-001-pass",
    "submission_id": "<submission_id>",
    "action": "modify",
    "override_task_id": "T-GOV-005"
  }'
```

Expected: `"status": "MODIFIED"`, `"assigned_task": "T-GOV-005"`

---

## Failure Tests

### Duplicate Approval (must return 409)
```bash
# Approve once (succeeds)
curl -X POST http://localhost:8000/api/v1/review/approve \
  -H "Content-Type: application/json" \
  -d '{"trace_id": "...", "submission_id": "...", "action": "approve"}'

# Approve again (must fail with 409)
curl -X POST http://localhost:8000/api/v1/review/approve \
  -H "Content-Type: application/json" \
  -d '{"trace_id": "...", "submission_id": "...", "action": "approve"}'
```

Expected second response: `{"detail": "Submission already actioned: APPROVED"}`

### Modify Without Override Task (must return 400)
```bash
curl -X POST http://localhost:8000/api/v1/review/modify \
  -H "Content-Type: application/json" \
  -d '{"trace_id": "...", "submission_id": "...", "action": "modify"}'
```

Expected: `{"detail": "override_task_id is required for modify action"}`

### Invalid submission_id (must return 404)
```bash
curl -X POST http://localhost:8000/api/v1/review/approve \
  -H "Content-Type: application/json" \
  -d '{"trace_id": "trace-xxx", "submission_id": "sub-nonexistent", "action": "approve"}'
```

Expected: `{"detail": "Review record not found"}`

### Missing trace_id (must return 422)
```bash
curl -X POST http://localhost:8000/api/v1/production/niyantran/submit \
  -H "Content-Type: application/json" \
  -d '{"task_id": "x", "task_title": "Test Title", "task_description": "Test description here", "submitted_by": "User"}'
```

Expected: `422 Unprocessable Entity`

---

## Frontend Manual Test

1. Start backend: `python -m uvicorn main:app --host 0.0.0.0 --port 8000`
2. Start frontend: `cd frontend && npm start`
3. Navigate to: `http://localhost:3000/review-queue`
4. Submit a task via `http://localhost:3000/submit`
5. Refresh the review queue — submission appears with `PENDING_REVIEW`
6. Click a row — detail view opens with selection_reason and full JSON
7. Click APPROVE — state updates to `APPROVED`, buttons disappear
8. Submit another task, click REJECT — state updates to `REJECTED`
9. Submit another task, enter override task ID, click MODIFY — state updates to `MODIFIED`

---

## Audit Log Verification

```bash
# Windows
type storage\audit_logs\audit_2026-05-07.jsonl

# Unix
cat storage/audit_logs/audit_$(date +%Y-%m-%d).jsonl
```

Each line is one JSON object. Verify:
- `action` matches what was performed
- `final_task` is `NONE` for reject, `override_task_id` for modify, `selected_task_id` for approve
- `system_task` always reflects the original deterministic recommendation
- `timestamp` is present and accurate
- No lines are missing between actions
