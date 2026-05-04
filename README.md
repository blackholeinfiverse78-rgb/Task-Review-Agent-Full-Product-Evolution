# Parikshak — Deterministic Task Evaluation Engine

**Version**: 3.0.0 | **Status**: TANTRA-COMPLIANT | **Protocol**: Rule-Based Deterministic

Parikshak is a fully deterministic, rule-based engineering task evaluation engine. It uses a 4-check binary rule engine, deterministic graph traversal, and a strict 7-field output contract. No numeric scoring. No weights. No fallback routing.

---

## Architecture

### Architecture Ownership & Separation

**Evaluation Engine owns:**
- rule_engine
- assignment_engine
- signal_engine
- validator

**Task Selector owns:**
- final_convergence
- mandala_mapper

**Post-Processing Layers:**
- Decision Engine
- Human-in-Loop
- Bucket Logging
*(Note: These are strictly downstream and DO NOT affect task selection or the evaluation result. They are only post-processing layers.)*


```
Submission Input (multipart/form-data or JSON)
    |
    v
[Step 0] REVIEW_PACKET Hard Gate        <- review_packet_parser.py
    |  Missing / malformed -> FAIL, schema_violation
    v
[Step 1] Registry Validation            <- validator.py
    |  Invalid module_id / schema_version -> FAIL, schema_violation
    v
[Step 2] Signal Collection              <- signal_engine.py (SUPPORTING ONLY)
    |  Repo signals, feature match, title/desc signals — no evaluation authority
    v
[Step 2.5] Domain Routing               <- domain_router.py
    |  Detects: backend / frontend / infrastructure / fullstack / ml
    |  No match -> FAIL, schema_violation
    v
[Step 3] Rule Engine                    <- rule_engine.py (SINGLE AUTHORITY)
    |  4 binary checks in strict order, first failure stops:
    |    Check 1: schema_validation    (repo OR word_count >= 50)
    |    Check 2: completeness         (code + proof + architecture + file_count >= 3)
    |    Check 3: logic_validation     (delivery_ratio >= 0.6 AND word_count >= 80)
    |    Check 4: integration          (repo accessible, metadata present)
    |  Output: evaluation_result = PASS | FAIL
    |          failure_type = schema_violation | incomplete | incorrect_logic | integration_fail
    v
[Step 4] Graph Traversal                <- engine/task_graph_engine.py
    |  PASS  -> task.next_tasks[0]
    |  FAIL  -> task.failure_tasks[failure_type][0]
    |  No fallback. Missing mapping -> HARD REJECT
    v
[Step 5] Decision Engine                <- production_decision_engine.py
    |  PASS -> APPROVED, advancement
    |  FAIL -> REJECTED, correction | reinforcement
    |  Generates: strengths, failures, root_cause, learning_feedback, next_direction
    v
[Step 6] Human-in-Loop                  <- human_in_loop.py
    |  confidence = (proof + architecture + code + rubric_completeness) / 4
    |  confidence < 0.98 -> escalation persisted to storage/escalations/
    v
[Step 7] Output Contract Enforcement    <- final_convergence.py
    |  Exactly 7 fields enforced. Extra or missing -> CONTRACT_VIOLATION
    v
[Step 8] Bucket Logging                 <- bucket_integration.py
    |  Writes: evaluation_result, failure_type, decision, trace_id, next_task
    v
Final Response — exact 7-field contract
```

---

## Output Contract (Exact)

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

No extra fields. No missing fields. Exact naming only.

---

## Rule Engine — 4 Binary Checks

```
Check 1 — schema_validation
  FAIL if: no repository AND word_count < 50

Check 2 — completeness_validation
  FAIL if: no code (no repo or 0 files)
  FAIL if: no proof (no README, no tests, no docs)
  FAIL if: no architecture (layer_count < 2 AND not modular AND no arch keywords)
  FAIL if: file_count < 3

Check 3 — logic_validation
  FAIL if: delivery_ratio < 0.6 OR missing_features > 3
  FAIL if: word_count < 80 AND readme_score < 1

Check 4 — integration_validation
  FAIL if: repo error present (not network_failure)
  FAIL if: repo_available=True but metadata.name missing
```

---

## failure_type Values

| failure_type | Trigger | Graph Route |
|---|---|---|
| `schema_violation` | No repo + short desc, invalid module, no domain match | `failure_tasks["schema_violation"][0]` |
| `incomplete` | No code, no proof, no architecture, < 3 files | `failure_tasks["incomplete"][0]` |
| `incorrect_logic` | Low delivery ratio, short description | `failure_tasks["incorrect_logic"][0]` |
| `integration_fail` | Repo fetch error, metadata missing | `failure_tasks["integration_fail"][0]` |

---

## Task DB — FINAL Schema

Every task must have all 14 fields:

```json
{
  "task_id":            "T-GOV-001",
  "product":            "Niyantran",
  "layer":              "Governance",
  "subsystem":          "Task Review Engine",
  "capability":         "Submission Evaluation",
  "dharma":             "Ensure accurate evaluation.",
      "completion_signals": ["evaluation_api_returns_200", "trace_id_written"],
  "failure_type":       null,
  "prerequisites":      [],
  "next_tasks":         ["T-GOV-002"],
  "failure_tasks": {
    "schema_violation": ["T-GOV-F01"],
    "incomplete":       ["T-GOV-F01"],
    "incorrect_logic":  ["T-GOV-F02"],
    "integration_fail": ["T-SYS-F00"]
  },
  "constraints":        ["no_numeric_scoring", "no_fallback_routing"]
}
```

---

## Domain Detection

Task title + description must contain keywords from one of:

| Domain | Sample Keywords |
|--------|----------------|
| `backend` | api, fastapi, flask, service, database, auth, endpoint |
| `frontend` | react, vue, component, ui, dashboard, tailwind |
| `infrastructure` | docker, kubernetes, terraform, deployment, pipeline |
| `fullstack` | fullstack, full-stack, react, fastapi, node |
| `ml` | machine learning, model, training, pytorch, sklearn |

No match -> `schema_violation` HARD REJECT.

---

## API Endpoints

### Lifecycle
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/lifecycle/submit` | Submit task (multipart/form-data) |
| GET | `/api/v1/lifecycle/history` | All submission history |
| GET | `/api/v1/lifecycle/review/{id}` | Review by submission ID |
| GET | `/api/v1/lifecycle/next/{id}` | Next task by submission ID |

### Production (Niyantran)
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/production/niyantran/submit` | Accept task from Niyantran (JSON) |
| GET | `/api/v1/production/niyantran/health` | Health check |
| GET | `/api/v1/production/bucket/logs` | Recent evaluation logs |
| GET | `/api/v1/production/bucket/stats` | Bucket statistics |
| GET | `/api/v1/production/human-review/pending` | Pending escalations |
| POST | `/api/v1/production/human-review/override` | Apply human override |
| GET | `/api/v1/production/system/production-status` | Full system status |

### TTS (Vaani)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/tts/speak` | Generate speech audio |
| GET | `/api/v1/tts/languages` | Supported languages |

---

## Running Locally

**Backend**
```bash
cd "g:\Live Task Review Agent - 2"
pip install -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
API docs: `http://localhost:8000/docs`

**Frontend**
```bash
cd frontend
npm install
npm start
```
UI: `http://localhost:3000`

**Environment** — copy `.env.example` to `.env`:
```
GITHUB_TOKEN=your_token_here
GROQ_API_KEY=your_key_here
ALLOWED_ORIGINS=["http://localhost:3000"]
```

---

## BHIV Determinism Proof

```bash
set PYTHONIOENCODING=utf-8
python tests/test_determinism_proof.py
```

| TC | Scenario | Result |
|----|----------|--------|
| TC-1 | Same input x2 | PASS, T-GOV-002 x2 identical |
| TC-2 | No repo + short desc | FAIL, schema_violation |
| TC-3 | No proof/arch/1 file | FAIL, incomplete |
| TC-4 | Low delivery_ratio | FAIL, incorrect_logic |
| TC-5 | Repo error | FAIL, integration_fail |
| TC-6 | All tasks in DB | all task_ids valid |

**6/6 PASSED — SYSTEM TANTRA-COMPLIANT**

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.11, FastAPI, Pydantic v2 |
| Frontend | React 18, TailwindCSS, Axios, React Query |
| TTS | VaaniTTS (gTTS primary, pyttsx3 fallback) |
| Storage | Local JSONL (bucket_logs, escalations) |
| Deployment | Render (backend + static frontend) |

---

## Engine File Map

| Engine | File |
|--------|------|
| Rule Engine (evaluation authority) | `evaluation_engine/rule_engine.py` |
| Assignment Engine (delegates to rule_engine) | `evaluation_engine/assignment_engine.py` |
| Signal Engine (supporting only) | `evaluation_engine/signal_engine.py` |
| Domain Router | `evaluation_engine/domain_router.py` |
| Decision Engine (narrative only) | `task_selector/production_decision_engine.py` |
| Graph Engine (deterministic traversal) | `engine/task_graph_engine.py` |
| Final Convergence (orchestrator) | `task_selector/final_convergence.py` |
| Review Orchestrator (lifecycle handler) | `task_selector/review_orchestrator.py` |
| Review Packet Parser (hard gate) | `evaluation_engine/review_packet_parser.py` |
| Human-in-Loop | `task_selector/human_in_loop.py` |
| Bucket Integration | `task_selector/bucket_integration.py` |
| Validation Gate | `evaluation_engine/shraddha_validation.py` |
| Registry Validator | `evaluation_engine/validator.py` |
| Mandala Mapper | `task_selector/mandala_mapper.py` |
