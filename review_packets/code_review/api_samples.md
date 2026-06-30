# API Request and Response Samples

This document contains request and response payloads for core Parikshak production endpoints. All endpoints require standard JWT Bearer authentication header.

---

## 1. Candidate Submission Intake
* **Endpoint**: `POST /api/v1/production/intake`
* **Headers**: 
  * `Authorization: Bearer <JWT_Token>`
  * `Content-Type: application/json`

### Request Payload
```json
{
  "assigned_task": "Implement Secure REST API Authentication",
  "original_task_document": "Objective: Build JWT auth. Deliverables: login, register endpoints.",
  "review_packet": "Check endpoints and JWT RS256 validation.",
  "repository_or_commit": "G:/Live Task Review Agent - 2",
  "submission_date": "2026-06-30T12:00:00Z",
  "due_date": "2026-06-30T18:00:00Z",
  "supporting_evidence": {
    "evidence_files": ["api/production.py"]
  },
  "additional_instructions": "Check for docstrings.",
  "trace_id": "trace-test-c8311a2f",
  "assigned_task_id": "T-GOV-001"
}
```

### Response Payload
```json
{
  "status": "QUEUED",
  "submission_id": "sub-ec513bc1-c8311a2f",
  "trace_id": "trace-test-c8311a2f",
  "review_state": "PENDING_REVIEW",
  "review": {
    "review_id": "rev-sub-ec513bc1-c8311a2f",
    "submission_id": "sub-ec513bc1-c8311a2f",
    "evaluation_result": "FAIL",
    "failure_type": "schema_violation",
    "score": 40,
    "readiness_percent": 40,
    "evaluation_summary": "### WHAT'S DONE WELL\n- Code styling is clean...\n### MISSING / INCOMPLETE\n- Missing proper docstrings...\n### REQUIRED FIXES\n- Add schema validation checks...",
    "selected_task_id": "T-GOV-F01",
    "selection_reason": "FAIL(schema_violation) -> failure_tasks['schema_violation'][0] = T-GOV-F01",
    "evidence_used": ["api/production.py"]
  }
}
```

---

## 2. Retrieve Pending Reviews
* **Endpoint**: `GET /api/v1/review/pending`
* **Headers**:
  * `Authorization: Bearer <JWT_Token>`

### Response Payload
```json
[
  {
    "submission_id": "sub-ec513bc1-c8311a2f",
    "candidate_name": "operator",
    "task_title": "Implement Secure REST API Authentication",
    "evaluation_result": "FAIL",
    "failure_type": "schema_violation",
    "selected_task_id": "T-GOV-F01",
    "trace_id": "trace-test-c8311a2f",
    "review_state": "PENDING_REVIEW",
    "expected_version": 1
  }
]
```

---

## 3. Human-in-Loop Governance Approval
* **Endpoint**: `POST /api/v1/review/approve`
* **Headers**:
  * `Authorization: Bearer <JWT_Token>`
  * `Content-Type: application/json`

### Request Payload
```json
{
  "trace_id": "trace-test-c8311a2f",
  "submission_id": "sub-ec513bc1-c8311a2f",
  "operator_id": "Akash",
  "operator_role": "REVIEW_OPERATOR",
  "action": "approve",
  "expected_version": 1,
  "reason_taxonomy": "HUMAN_VALIDATION_FAILURE"
}
```

### Response Payload
```json
{
  "status": "APPROVED",
  "submission_id": "sub-ec513bc1-c8311a2f",
  "assigned_task": "T-GOV-F01",
  "event_id": "evt-77da09f1b95c"
}
```

---

## 4. Production Certification Report
* **Endpoint**: `GET /api/v1/production/certification/trace-prod-ready`

### Response Payload
```json
{
  "system_information": {
    "trace_id": "trace-prod-ready",
    "certified_at": "2026-06-30T12:00:00Z",
    "verifier": "Parikshak Production Certification Engine v1.0"
  },
  "dimensions": {
    "Runtime": "PASS",
    "Observability": "PASS",
    "Replayability": "PASS",
    "Governance": "PASS",
    "Provenance": "PASS",
    "Security": "PASS",
    "Versioning": "PASS",
    "Recovery": "PASS",
    "Human Approval": "PASS",
    "Layer Placement": "PASS",
    "Dependency Integrity": "PASS",
    "Ecosystem Participation": "PASS"
  },
  "production_score": 100,
  "certification_decision": "READY",
  "critical_failures": [],
  "warnings": [],
  "risk_summary": "System demonstrates compliant architectural boundaries, verified replay safety, and full ecosystem integration. Approved for governed TANTRA production.",
  "evidence_summary": {
    "evidence_bundle.json": "PRESENT",
    "handover_bundle.json": "PRESENT"
  },
  "replay_status": "PASS",
  "governance_status": "PASS",
  "observability_status": "PASS",
  "security_status": "PASS",
  "recovery_status": "PASS",
  "dependencies": {
    "status": "PASS"
  },
  "evaluation_result": "PASS",
  "failure_type": null,
  "trace_id": "trace-prod-ready"
}
```
