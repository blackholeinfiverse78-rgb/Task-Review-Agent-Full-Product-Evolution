# Parikshak — Deterministic Task Review System

**Version:** v5.0.0
**Status:** CORE LOCKED + GOVERNANCE LAYER OPERATIONAL

> Parikshak is a deterministic, rule-based engineering task evaluation engine. It evaluates submissions against 4 binary rules, routes them to the exact next task via a graph database, and holds every recommendation in a mandatory human review queue before any assignment reaches Niyantran.

---

## System Certification

| Property | Value |
|---|---|
| Type | Deterministic Finite Automaton (DB-driven) |
| Compliance | Tantra Fully Compliant |
| Evaluation | DFA Verified |
| Governance | Human Approval Gate — OPERATIONAL |
| Core Status | LOCKED — no logic mutations permitted |

---

## How It Works

```
Submission (trace_id required)
    → Evaluation (4 binary rules)
    → Graph Traversal (deterministic task selection)
    → PENDING_REVIEW (blocked — no auto-assignment)
    → Human reviews in dashboard
    → APPROVE / REJECT / MODIFY
    → Assignment reaches Niyantran only after approval
```

---

## Architecture

### Execution Pipeline

```
POST /api/v1/production/niyantran/submit
    |
    v
[Step 0] REVIEW_PACKET Hard Gate        evaluation_engine/review_packet_parser.py
[Step 1] Registry Validation            evaluation_engine/validator.py
[Step 2] Signal Collection              evaluation_engine/signal_engine.py (supporting only)
[Step 3] Rule Engine — 4 binary checks  evaluation_engine/rule_engine.py
    |  Check 1: schema_validation    repo OR word_count >= 50
    |  Check 2: completeness         code + proof + architecture + file_count >= 3
    |  Check 3: logic_validation     delivery_ratio >= 0.6 AND word_count >= 80
    |  Check 4: integration          repo accessible, metadata present
    |  → evaluation_result: PASS | FAIL
    |  → failure_type: schema_violation | incomplete | incorrect_logic | integration_fail
    v
[Step 4] Graph Traversal                engine/task_graph_engine.py
    |  PASS → task.next_tasks[0]
    |  FAIL → task.failure_tasks[failure_type][0]
    |  No fallback. Missing mapping → HARD REJECT
    v
[Step 5] Output Contract Enforcement    engine/execution_pipeline.py
    |  Exactly 8 fields. Extra or missing → CONTRACT_VIOLATION
    v
[Step 6] Persist to storage             models/persistent_storage.py
    |  review_state = PENDING_REVIEW
    |  trace_id stored on ReviewRecord
    v
[Step 7] Human Governance Gate          api/review_routes.py
    |  APPROVE → state=APPROVED, task assigned
    |  REJECT  → state=REJECTED, no assignment
    |  MODIFY  → state=MODIFIED, override task assigned
    v
[Step 8] Bucket Logging                 task_selector/bucket_integration.py
```

### Architecture Ownership

**Sri Satya (Evaluation Engine):**
- `evaluation_engine/rule_engine.py` — single PASS/FAIL authority
- `evaluation_engine/signal_engine.py` — supporting signals only
- `evaluation_engine/validator.py` — registry validation
- `evaluation_engine/review_packet_parser.py` — documentation gate

**Parikshak (Task Selector):**
- `engine/task_graph_engine.py` — deterministic graph traversal
- `task_selector/final_convergence.py` — output contract enforcement
- `task_selector/niyantran_connection.py` — API gateway

**Human Governance Layer:**
- `api/review_routes.py` — approve / reject / modify endpoints
- `models/review_models.py` — review state models

**Nupur Replay Persistence:**
- `replay_audit/atomic_persistence.py` — append-only atomic storage
- `storage/audit_logs/` — append-only audit trail
- `storage/checkpoints/` — deterministic replay reconstruction

**Observability:**
- `observability/observability.py` — structured operational visibility
---

## Review States

| State | Meaning |
|---|---|
| `PENDING_REVIEW` | Default. Awaiting human action. No assignment sent. |
| `APPROVED` | Human approved. System recommendation assigned. |
| `REJECTED` | Human rejected. No assignment. |
| `MODIFIED` | Human overrode task. Override task assigned. |

---

## API Endpoints

### Submission

| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/production/niyantran/submit` | Submit task. Returns PENDING_REVIEW. |
| GET | `/api/v1/production/niyantran/health` | Health check |

### Human Review

| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/review/all` | All submissions with review state |
| GET | `/api/v1/review/pending` | Submissions in PENDING_REVIEW only |
| POST | `/api/v1/review/approve` | Approve recommendation |
| POST | `/api/v1/review/reject` | Reject — no assignment |
| POST | `/api/v1/review/modify` | Override task assignment |

### Monitoring

| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/production/bucket/logs` | Evaluation logs |
| GET | `/api/v1/production/bucket/stats` | Bucket statistics |
| GET | `/api/v1/production/system/production-status` | System health |

---

## Output Contract (8 Fields — Internal)

```json
{
  "trace_id":          "trace-a3f2c1d48b9e4f2a",
  "submission_id":     "sub-eb2e07e7c652-d42768ed",
  "evaluation_result": "PASS",
  "failure_type":      null,
  "selected_task_id":  "T-GOV-002",
  "selection_reason":  "PASS -> next_tasks[0] = T-GOV-002",
  "source":            "task_graph",
  "schema_version":    "v1.0"
}
```

Submit endpoint response (external):
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

## Rule Engine — 4 Binary Checks

| Check | Failure Type | Criteria |
|---|---|---|
| Schema | `schema_violation` | FAIL if no repository AND word_count < 50 |
| Completeness | `incomplete` | FAIL if no code, no proof, or file_count < 3 |
| Logic | `incorrect_logic` | FAIL if delivery_ratio < 0.6 OR word_count < 80 |
| Integration | `integration_fail` | FAIL if repo fetch error or metadata missing |

---

## Task DB Schema

Every task in `db/niyantran_tasks.json` — 65 tasks, 11 fields each:

```json
{
  "task_id":            "T-GOV-001",
  "product":            "Niyantran",
  "layer":              "Governance",
  "subsystem":          "Task Review Engine",
  "capability":         "Submission Evaluation",
  "dharma":             "Ensure accurate evaluation.",
  "completion_signals": ["evaluation_api_returns_200"],
  "prerequisites":      [],
  "next_tasks":         ["T-GOV-002"],
  "failure_tasks": {
    "schema_violation": ["T-GOV-F01"],
    "incomplete":       ["T-GOV-F01"],
    "incorrect_logic":  ["T-GOV-F02"],
    "integration_fail": ["T-SYS-F00"]
  },
  "constraints": ["no_numeric_scoring", "no_fallback_routing"]
}
```

---

## Frontend Dashboard

**URL:** `http://localhost:3000/review-queue`

**Table columns:** Candidate Name, Task Title, evaluation_result, failure_type, review_state, trace_id

**Detail view:** selection_reason, full response JSON, APPROVE / REJECT / MODIFY buttons

**Buttons only visible when:** `review_state === "PENDING_REVIEW"`

---

## Running Locally

```bash
# Backend
pip install -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8000

# Frontend
cd frontend
npm install
npm start
```

---

## Testing

```bash
# Static verification (no server required)
set PYTHONPATH=.
py -3 tests/static_verification.py

# End-to-end tests (requires running server)
py -3 tests/test_review_workflow.py
```

Static verification result: **13/13 PASSED**

---

## Tech Stack

- **Backend:** Python 3.11+, FastAPI, Pydantic v2
- **Storage:** JSON file persistence (`storage/product_state.json`)
- **Audit:** JSONL append-only (`storage/audit_logs/`)
- **Frontend:** React 18, Tailwind CSS, React Router v6
- **Task DB:** JSON-based, 65 tasks
