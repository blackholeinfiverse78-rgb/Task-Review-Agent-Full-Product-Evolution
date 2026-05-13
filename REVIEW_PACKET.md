# REVIEW PACKET — Parikshak v5.0.0

## ENTRY POINT

**Primary File**: `main.py`
**Routers registered**:
- `api/lifecycle.py` → `/api/v1`
- `api/tts.py` → `/api/v1`
- `api/production.py` → `/api/v1/production`
- `api/review_routes.py` → `/api/v1/review`

**Orchestrators**:
- `evaluation_engine/orchestrator.py` — Sri Satya, evaluation authority
- `engine/execution_pipeline.py` — unified pipeline entry point
- `api/review_routes.py` — human governance approval layer

**Critical Files**:
- `engine/task_graph_engine.py` — deterministic graph traversal
- `evaluation_engine/rule_engine.py` — single evaluation authority
- `models/persistent_storage.py` — `ReviewRecord`, `TaskSubmission`, `ProductStorage`
- `models/review_models.py` — `ReviewState`, `ReviewActionRequest`, `AuditLogEntry`

Every submission enters a single sequential pipeline. No parallel paths. **trace_id MUST come from upstream. Missing or short trace_id results in HARD REJECT.**

---

## CORE FLOW

```
POST /api/v1/production/niyantran/submit
    |
    v
[execution_pipeline.execute()]
    |
    ├── trace_id validation          HARD REJECT if missing or < 8 chars
    ├── evaluation_orchestrator      Sri Satya — 4 binary rule checks
    ├── task_graph_engine.traverse   Parikshak — deterministic graph lookup
    ├── _enforce_boundary()          7-field contract validation
    └── _persist()
            ├── TaskSubmission  review_state = "PENDING_REVIEW"
            └── ReviewRecord    review_state = "PENDING_REVIEW"
                                trace_id     = upstream trace_id
    |
    v
Response: { review_state: "PENDING_REVIEW", status: "QUEUED" }
    |
    ← NOTHING sent to Niyantran yet ←
    |
    v
[Step 7] Human Governance Layer       api/review_routes.py
    |
    ├── APPROVE  POST /api/v1/review/approve
    │       guard: state must be PENDING_REVIEW → 409 if not
    │       sets:  review_state = APPROVED
    │       logs:  audit entry (action=approve, final_task=selected_task_id)
    │
    ├── REJECT   POST /api/v1/review/reject
    │       guard: state must be PENDING_REVIEW → 409 if not
    │       sets:  review_state = REJECTED
    │       logs:  audit entry (action=reject, final_task=NONE)
    │
    └── MODIFY   POST /api/v1/review/modify
            guard: override_task_id required → 400 if missing
            guard: state must be PENDING_REVIEW → 409 if not
            sets:  selected_task_id = override_task_id
                   review_state = MODIFIED
            logs:  audit entry (action=modify, system_task=original, final_task=override)
    |
    v
[Step 8] Bucket Logging               bucket_integration.py
    |
    v
Final assignment reaches Niyantran ONLY after human approval
```

---

## WHAT WAS BUILT

### Added
- `api/review_routes.py` — approve, reject, modify endpoints + audit logger
- `models/review_models.py` — `ReviewState` enum, `ReviewActionRequest`, `AuditLogEntry`
- `frontend/src/pages/ReviewDashboard.jsx` — operational review dashboard
- `frontend/src/components/SubmissionTable.jsx` — review queue table
- `frontend/src/components/SubmissionDetail.jsx` — detail view + action buttons
- `tests/static_verification.py` — 13-check static verifier
- `tests/test_review_workflow.py` — end-to-end test suite
- `storage/audit_logs/` — append-only audit log directory

### Modified
- `models/persistent_storage.py` — added `trace_id` field to `ReviewRecord`
- `engine/execution_pipeline.py` — `_persist()` stores `trace_id` on `ReviewRecord`
- `api/review_routes.py` — added 409 duplicate-action guard to all three endpoints
- `api/review_routes.py` — fixed `/all` and `/pending` to use `review.trace_id`

### Not Changed
- `evaluation_engine/rule_engine.py`
- `engine/task_graph_engine.py`
- `task_selector/final_convergence.py`
- `db/niyantran_tasks.json`
- 7-field output contract

---

## FAILURE CASES

| Case | Trigger | failure_type | Selected Task |
|---|---|---|---|
| FC-01 | REVIEW_PACKET.md missing | schema_violation | T-GOV-F01 |
| FC-02 | No repo AND word_count < 50 | schema_violation | T-GOV-F01 |
| FC-03 | Invalid module_id | schema_violation | T-GOV-F01 |
| FC-04 | No code / no proof / file_count < 3 | incomplete | T-GOV-F01 |
| FC-05 | delivery_ratio < 0.6 OR word_count < 80 | incorrect_logic | T-GOV-F02 |
| FC-06 | Repo fetch error | integration_fail | T-SYS-F00 |
| FC-07 | failure_type not in failure_tasks map | GRAPH_HARD_REJECT | raises ValueError |
| FC-08 | Output contract violation | CONTRACT_VIOLATION | raises ValueError |
| FC-09 | Missing trace_id | NIYANTRAN_HARD_REJECT | raises ValueError |
| FC-10 | Task ID not in DB | GRAPH_HARD_REJECT | raises ValueError |
| FC-11 | Approve already-actioned submission | — | 409 Conflict |
| FC-12 | Modify without override_task_id | — | 400 Bad Request |

---

## OUTPUT CONTRACT (7 Fields — Unchanged)

```json
{
  "trace_id":          "trace-a3f2c1d48b9e4f2a",
  "submission_id":     "sub-eb2e07e7c652-d42768ed",
  "evaluation_result": "PASS",
  "failure_type":      null,
  "selected_task_id":  "T-GOV-002",
  "selection_reason":  "PASS -> next_tasks[0] = T-GOV-002",
  "source":            "task_graph"
}
```

Submit endpoint response (after governance gate):
```json
{
  "trace_id":      "trace-a3f2c1d48b9e4f2a",
  "submission_id": "sub-eb2e07e7c652-d42768ed",
  "review_state":  "PENDING_REVIEW",
  "status":        "QUEUED",
  "message":       "Evaluation complete. Pending human approval for final assignment."
}
```

---

## PROOF

**Static Verification — 13/13 PASSED:**

| Check | Description | Result |
|---|---|---|
| 1 | ReviewRecord has trace_id, review_state, selected_task_id | PASS |
| 2 | ReviewState enum has all 4 states | PASS |
| 3 | Submit endpoint returns PENDING_REVIEW | PASS |
| 4 | Approve does NOT rerun evaluation or selection | PASS |
| 5 | Reject does NOT assign task | PASS |
| 6 | Modify overrides task without rerun | PASS |
| 7 | Audit log opened in append mode only | PASS |
| 8 | Pipeline stores trace_id on ReviewRecord | PASS |
| 9 | /review/all uses review.trace_id | PASS |
| 10 | storage/audit_logs/ directory exists | PASS |
| 11 | AuditLogEntry has all 6 required fields | PASS |
| 12 | No auto-assignment bypass in submit | PASS |
| 13 | ReviewRecord defaults to PENDING_REVIEW | PASS |

**System Compliance:**
- No numeric scoring: YES
- No fallback routing: YES
- No evaluation rerun on approval: YES
- No selector rerun on approval: YES
- No duplicate actions permitted: YES
- trace_id from upstream only: YES
- Audit log append-only: YES
- Assignment only after explicit approval: YES

**-> FINAL STATUS: VERIFIED WORKING — GOVERNANCE LAYER OPERATIONAL**
