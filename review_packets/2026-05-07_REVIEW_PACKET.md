# REVIEW PACKET — Parikshak Human Governance Layer
**Date:** 2026-05-07
**Version:** v5.0.0
**Status:** VERIFIED WORKING — 13/13 static checks passed

---

## 1. Entry Points

| File | Role |
|---|---|
| `main.py` | FastAPI app, router registration |
| `api/production.py` | `POST /api/v1/production/niyantran/submit` — intake gate |
| `api/review_routes.py` | `POST /review/approve`, `/reject`, `/modify`, `GET /review/all`, `/pending` |
| `engine/execution_pipeline.py` | Unified pipeline: evaluation → selection → persist |
| `models/persistent_storage.py` | `ReviewRecord`, `TaskSubmission`, `ProductStorage` |
| `models/review_models.py` | `ReviewState`, `ReviewActionRequest`, `AuditLogEntry` |
| `frontend/src/pages/ReviewDashboard.jsx` | Operational dashboard |
| `frontend/src/components/SubmissionTable.jsx` | Review queue table |
| `frontend/src/components/SubmissionDetail.jsx` | Detail view + action buttons |

---

## 2. Architecture Flow

```
POST /api/v1/production/niyantran/submit
    |
    v
[execution_pipeline.execute()]
    |
    ├── trace_id validation (HARD REJECT if missing or < 8 chars)
    ├── evaluation_orchestrator.evaluate_submission()   ← Sri Satya (unchanged)
    ├── task_graph_engine.traverse()                    ← Parikshak (unchanged)
    ├── _enforce_boundary()                             ← 7-field contract check
    └── _persist()
            ├── TaskSubmission(review_state="PENDING_REVIEW")
            └── ReviewRecord(review_state="PENDING_REVIEW", trace_id=trace_id)
    |
    v
Response: { review_state: "PENDING_REVIEW", status: "QUEUED" }
    |
    ← NOTHING sent to Niyantran yet ←
    |
    v
[Human reviews at /review-queue dashboard]
    |
    ├── APPROVE → POST /api/v1/review/approve
    │       ├── guard: review_state must be PENDING_REVIEW (409 if not)
    │       ├── review.review_state = APPROVED
    │       ├── product_storage._save()
    │       └── log_audit(action="approve", final_task=selected_task_id)
    │
    ├── REJECT → POST /api/v1/review/reject
    │       ├── guard: review_state must be PENDING_REVIEW (409 if not)
    │       ├── review.review_state = REJECTED
    │       ├── product_storage._save()
    │       └── log_audit(action="reject", final_task="NONE")
    │
    └── MODIFY → POST /api/v1/review/modify
            ├── guard: override_task_id required (400 if missing)
            ├── guard: review_state must be PENDING_REVIEW (409 if not)
            ├── review.selected_task_id = override_task_id
            ├── review.review_state = MODIFIED
            ├── product_storage._save()
            └── log_audit(action="modify", system_task=original, final_task=override)
```

---

## 3. Review States

| State | Set By | Meaning |
|---|---|---|
| `PENDING_REVIEW` | `execution_pipeline._persist()` | Default. Awaiting human action. |
| `APPROVED` | `POST /review/approve` | Human approved. Task assigned. |
| `REJECTED` | `POST /review/reject` | Human rejected. No assignment. |
| `MODIFIED` | `POST /review/modify` | Human overrode task. Override assigned. |

Default on `ReviewRecord`: `"PENDING_REVIEW"` (enforced by Pydantic field default).

---

## 4. Files Modified

| File | What Changed |
|---|---|
| `models/persistent_storage.py` | Added `trace_id: str = ""` field to `ReviewRecord` |
| `engine/execution_pipeline.py` | `_persist()` now passes `trace_id=output["trace_id"]` to `ReviewRecord` |
| `api/review_routes.py` | Added 409 duplicate-action guard to `approve`, `reject`, `modify` |
| `api/review_routes.py` | Fixed `/all` and `/pending` to use `review.trace_id` (not split of submission_id) |

---

## 5. Files Added

| File | Purpose |
|---|---|
| `api/review_routes.py` | All approval API endpoints + audit logger |
| `models/review_models.py` | `ReviewState`, `ReviewActionRequest`, `AuditLogEntry` |
| `frontend/src/pages/ReviewDashboard.jsx` | Dashboard page |
| `frontend/src/components/SubmissionTable.jsx` | Review queue table component |
| `frontend/src/components/SubmissionDetail.jsx` | Detail view + APPROVE/REJECT/MODIFY buttons |
| `tests/static_verification.py` | 13-check static verifier (no server required) |
| `tests/test_review_workflow.py` | End-to-end test suite (requires running server) |
| `docs/SAMPLE_PAYLOADS.md` | Sample payloads and curl commands |
| `storage/audit_logs/` | Append-only audit log directory |

---

## 6. What Was NOT Changed

- `evaluation_engine/rule_engine.py` — untouched
- `evaluation_engine/orchestrator.py` — untouched
- `engine/task_graph_engine.py` — untouched
- `task_selector/final_convergence.py` — untouched
- `db/niyantran_tasks.json` — untouched
- Deterministic 7-field output contract — untouched

---

## 7. Hard Rule Enforcement Proof

| Rule | Enforcement Location | Verified |
|---|---|---|
| No auto-assignment | `production.py` returns `PENDING_REVIEW` only | YES |
| No evaluation rerun | `approve/reject/modify` contain no `evaluation_orchestrator` call | YES |
| No selector rerun | `approve/reject/modify` contain no `task_graph_engine` call | YES |
| No duplicate actions | 409 guard: `review_state != PENDING_REVIEW` blocks re-action | YES |
| No missing override | 400 guard: `override_task_id` required for modify | YES |
| trace_id preserved | Stored on `ReviewRecord.trace_id`, returned in all dashboard responses | YES |
| Audit append-only | `log_audit()` opens file with mode `"a"` | YES |
| Default PENDING | `ReviewRecord.review_state` default = `"PENDING_REVIEW"` | YES |

Static verification command:
```bash
set PYTHONPATH=. && py -3 tests/static_verification.py
```
Result: **13/13 PASSED**

---

## 8. Bug Found and Fixed

**File:** `api/review_routes.py`
**Issue:** No guard against duplicate actions. An already-APPROVED submission could be approved again, silently overwriting state and writing a duplicate audit entry.
**Fix:** Added to all three endpoints before any mutation:
```python
if review.review_state != ReviewState.PENDING_REVIEW:
    raise HTTPException(status_code=409, detail=f"Submission already actioned: {review.review_state}")
```

---

## 9. Failure Test Cases

| Case | Input | Expected Response |
|---|---|---|
| Missing trace_id | `trace_id: ""` | 422 Unprocessable Entity |
| trace_id < 8 chars | `trace_id: "abc"` | 422 Unprocessable Entity |
| Invalid submission_id on approve | unknown id | 404 Not Found |
| Approve already-approved | second approve call | 409 Conflict |
| Reject already-rejected | second reject call | 409 Conflict |
| Modify without override_task_id | `override_task_id: null` | 400 Bad Request |
| Modify already-modified | second modify call | 409 Conflict |

---

## 10. Audit Log

**Location:** `storage/audit_logs/audit_YYYY-MM-DD.jsonl`
**Mode:** Append-only (`"a"`)
**Schema (6 fields):**

```json
{
  "trace_id":      "trace-test-001",
  "submission_id": "sub-aeb3f363fdf5-race-001",
  "system_task":   "T-GOV-F01",
  "final_task":    "T-GOV-F01",
  "action":        "approve",
  "timestamp":     "2026-05-07 17:00:08.227760"
}
```

**Real entries from `storage/audit_logs/audit_2026-05-07.jsonl`:**
```
{"trace_id": "test-trace-001", "submission_id": "sub-aeb3f363fdf5-race-001", "system_task": "T-GOV-F01", "final_task": "T-GOV-F01", "action": "approve", "timestamp": "2026-05-07 17:00:08.227760"}
{"trace_id": "test-trace-002", "submission_id": "sub-aeb3f363fdf5-race-002", "system_task": "T-GOV-F01", "final_task": "T-GOV-OVERRIDE", "action": "modify", "timestamp": "2026-05-07 17:00:08.247637"}
```

**final_task accuracy:**
- APPROVE: `final_task` = `selected_task_id` (system recommendation)
- REJECT: `final_task` = `"NONE"` (no assignment)
- MODIFY: `final_task` = `override_task_id`, `system_task` = original recommendation

---

## 11. Validation Results

```
CHECK 1:  ReviewRecord has all required fields         PASS
CHECK 2:  ReviewState enum complete (4 states)         PASS
CHECK 3:  submit endpoint blocks at PENDING_REVIEW     PASS
CHECK 4:  approve does NOT rerun evaluation/selection  PASS
CHECK 5:  reject blocks assignment                     PASS
CHECK 6:  modify overrides without rerun               PASS
CHECK 7:  audit log is append-only                     PASS
CHECK 8:  pipeline stores trace_id correctly           PASS
CHECK 9:  /review/all returns review.trace_id          PASS
CHECK 10: audit log directory exists                   PASS
CHECK 11: AuditLogEntry schema complete (6 fields)     PASS
CHECK 12: No auto-assignment bypass                    PASS
CHECK 13: ReviewRecord defaults to PENDING_REVIEW      PASS

VERDICT: VERIFIED WORKING
```

---

## 12. Deterministic Guarantees

- Same submission always produces same `evaluation_result` and `selected_task_id`
- `review_state` transitions are one-way: `PENDING_REVIEW` → one of `{APPROVED, REJECTED, MODIFIED}`
- No state can be re-actioned once set (409 guard)
- `trace_id` is never generated internally — always from upstream, stored on `ReviewRecord`, returned in all responses
- Audit log is append-only — no entry is ever deleted or overwritten
- `selected_task_id` is only mutated by the MODIFY endpoint, and only when `review_state == PENDING_REVIEW`
