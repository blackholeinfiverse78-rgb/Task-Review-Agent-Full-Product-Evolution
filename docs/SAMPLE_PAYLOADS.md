# Sample Test Payloads for Human Review Workflow

## 1. PASS Submission (Complete Engineering Task)

```json
{
  "task_id": "demo-001",
  "task_title": "E-Commerce REST API with Payment Integration",
  "task_description": "Built a complete e-commerce REST API with Stripe payment integration, user authentication using JWT, product catalog management, shopping cart functionality, order processing, and admin dashboard. Implemented comprehensive error handling, input validation, rate limiting, and security best practices. Repository includes 120+ unit tests with 92% code coverage, API documentation using Swagger/OpenAPI, Docker containerization, CI/CD pipeline configuration, and deployment guide. All endpoints are RESTful, properly versioned, and follow industry standards.",
  "submitted_by": "Akash Kumar",
  "repository_url": "https://github.com/akash/ecommerce-api",
  "module_id": "task-review-agent",
  "schema_version": "v1.0",
  "pdf_text": "",
  "trace_id": "trace-demo-001-pass",
  "current_task_id": "T-GOV-001"
}
```

**Expected Result:**
- evaluation_result: PASS
- selected_task_id: T-GOV-002 (next advancement task)
- review_state: PENDING_REVIEW

---

## 2. FAIL Submission (Incomplete)

```json
{
  "task_id": "demo-002",
  "task_title": "Simple Todo App",
  "task_description": "Created a basic todo application with add and delete features.",
  "submitted_by": "Test User",
  "repository_url": null,
  "module_id": "task-review-agent",
  "schema_version": "v1.0",
  "pdf_text": "",
  "trace_id": "trace-demo-002-fail",
  "current_task_id": "T-GOV-001"
}
```

**Expected Result:**
- evaluation_result: FAIL
- failure_type: incomplete
- selected_task_id: T-GOV-F01 (correction task)
- review_state: PENDING_REVIEW

---

## 3. FAIL Submission (Schema Violation)

```json
{
  "task_id": "demo-003",
  "task_title": "App",
  "task_description": "Made app.",
  "submitted_by": "User",
  "repository_url": null,
  "module_id": "task-review-agent",
  "schema_version": "v1.0",
  "pdf_text": "",
  "trace_id": "trace-demo-003-schema",
  "current_task_id": "T-GOV-001"
}
```

**Expected Result:**
- evaluation_result: FAIL
- failure_type: schema_violation
- selected_task_id: T-GOV-F01
- review_state: PENDING_REVIEW

---

## API Test Commands

### Submit Task
```bash
curl -X POST http://localhost:8000/api/v1/production/niyantran/submit \
  -H "Content-Type: application/json" \
  -d @payload_pass.json
```

### Get All Reviews
```bash
curl http://localhost:8000/api/v1/review/all
```

### Get Pending Reviews Only
```bash
curl http://localhost:8000/api/v1/review/pending
```

### Approve Submission
```bash
curl -X POST http://localhost:8000/api/v1/review/approve \
  -H "Content-Type: application/json" \
  -d '{
    "trace_id": "trace-demo-001-pass",
    "submission_id": "sub-abc123-001-pass",
    "action": "approve"
  }'
```

### Reject Submission
```bash
curl -X POST http://localhost:8000/api/v1/review/reject \
  -H "Content-Type: application/json" \
  -d '{
    "trace_id": "trace-demo-002-fail",
    "submission_id": "sub-def456-002-fail",
    "action": "reject"
  }'
```

### Modify Assignment
```bash
curl -X POST http://localhost:8000/api/v1/review/modify \
  -H "Content-Type: application/json" \
  -d '{
    "trace_id": "trace-demo-001-pass",
    "submission_id": "sub-abc123-001-pass",
    "action": "modify",
    "override_task_id": "T-GOV-999"
  }'
```

---

## Frontend Testing

1. Start backend: `python -m uvicorn main:app --reload`
2. Start frontend: `cd frontend && npm start`
3. Navigate to: `http://localhost:3000/review-queue`
4. Test all three actions: APPROVE, REJECT, MODIFY

---

## Audit Log Verification

Check audit log after each action:
```bash
cat storage/audit_logs/audit_$(date +%Y-%m-%d).jsonl | jq
```

Expected format:
```json
{
  "trace_id": "trace-demo-001-pass",
  "submission_id": "sub-abc123-001-pass",
  "system_task": "T-GOV-002",
  "final_task": "T-GOV-002",
  "action": "approve",
  "timestamp": "2025-01-15T10:30:00"
}
```
