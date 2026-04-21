# Parikshak — Deterministic Task Evaluation Engine

**Version**: 2.0.0 | **Status**: Production-Ready | **Stack**: FastAPI · React 18 · TailwindCSS · Python 3.11

Parikshak is a fully deterministic, governance-safe engineering task evaluation system. It enforces strict architectural boundaries across layered service, api, model, and core directories, eliminates all parallel scoring paths, and guarantees that identical inputs always produce identical outputs across repeated runs.

---

## Project Structure

```
parikshak-system/
├── api/                        ← Route handlers and endpoint definitions
│   ├── lifecycle.py            ← Submission, history, review, next-task routes
│   ├── production.py           ← Niyantran, bucket, human-review routes
│   └── tts.py                  ← VaaniTTS speech generation routes
├── service/                    ← Business logic and evaluation pipeline
│   ├── assignment_engine.py    ← SINGLE scoring authority (Phase 2–4)
│   ├── signal_engine.py        ← Supporting signals collector (no scoring)
│   ├── production_decision_engine.py ← Phase 5 APPROVED/REJECTED decision
│   ├── task_selection_engine.py      ← Niyantran graph task selector
│   ├── review_packet_parser.py       ← Phase 0 hard gate
│   ├── domain_router.py        ← backend/frontend/infra/fullstack/ml routing
│   ├── human_in_loop.py        ← Escalation at confidence < 0.98
│   └── bucket_integration.py   ← Mandatory JSONL evaluation logging
├── model/                      ← Pydantic schemas and data models
│   ├── schemas.py
│   └── next_task_model.py
├── core/                       ← Configuration, registry, interfaces
│   └── interfaces/
├── frontend/                   ← React 18 + TailwindCSS UI
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   └── services/
│   └── package.json
├── tests/                      ← Determinism and integration test suite
│   └── test_determinism_proof.py
├── docs/                       ← Architecture and API documentation
│   ├── ARCHITECTURE.md
│   └── API_CONTRACTS.md
├── storage/
│   ├── bucket_logs/            ← JSONL evaluation logs
│   └── escalations/            ← Human-in-loop escalation cases
├── requirements.txt
└── README.md
```

---

## Architecture — 8-Step Locked Pipeline

```
Submission Input
    │
    ▼
[Step 0] REVIEW_PACKET Hard Gate       ← review_packet_parser.py
    │  Missing / malformed → HARD REJECT (score = 0)
    ▼
[Step 1] Registry Validation           ← validator.py
    │  Invalid module_id / schema_version → REJECT
    ▼
[Step 2] Signal Collection             ← signal_engine.py  (SUPPORTING ONLY)
    │  Repo signals, feature match, title/desc signals
    ▼
[Step 2.5] Domain Routing              ← domain_router.py
    │  Detects: backend / frontend / infra / fullstack / ml
    ▼
[Step 3] Assignment Engine             ← assignment_engine.py  (SINGLE AUTHORITY)
    │  Phase 2: Binary P/A/C  {proof:0/1, architecture:0/1, code:0/1}
    │  Phase 3: Binary rubric (Q_proof, Q_arch, Q_code, alignment, auth, effort)
    │  Phase 4: Exact formula → score 0–10
    │           0.35×completeness + 0.25×quality + 0.20×alignment
    │           + 0.10×authenticity + 0.10×effort
    ▼
[Step 4] Decision Engine               ← production_decision_engine.py
    │  score ≥ 6 → APPROVED  |  score < 6 → REJECTED
    │  Generates: strengths, failures, root_cause, learning_feedback, next_direction
    ▼
[Step 5] Human-in-Loop                 ← human_in_loop.py
    │  confidence = (proof + architecture + code + rubric_completeness) / 4
    │  confidence < 0.98 → escalation case created + persisted to disk
    ▼
[Step 6] Validation Gate               ← shraddha_validation.py
    │  Contract enforcement, type checking, field correction
    ▼
[Step 7] Bucket Logging                ← bucket_integration.py  (MANDATORY)
    │  Writes: type, candidate_id, task_id, score, decision,
    │          review_summary, next_task, trace_id
    ▼
[Step 8] Task Selection                ← task_selection_engine.py
         Deterministic selection from Niyantran task graph
         NO task generation — selection only
```

---

## Scoring Formula

```
final_score (0–10) =
  0.35 × completeness   (delivery_ratio from repo signals)
  0.25 × quality        (Q_proof + Q_arch + Q_code) / 3
  0.20 × alignment      (binary: delivery ≥ 0.6 and missing ≤ 3)
  0.10 × authenticity   (binary: repo present and description ≥ 50 words)
  0.10 × effort         (binary: description ≥ 80 words and README present)

Score Caps:
  Q_proof = 0    → cap at 4.0
  Q_code  = 0    → cap at 5.0
  alignment = 0  → cap at 6.0

Decision Thresholds:
  score ≥ 6.0 → APPROVED  (advancement)
  score 4–5.9 → REJECTED  (reinforcement)
  score < 4.0 → REJECTED  (correction)
```

---

## Confidence Formula

```
confidence = (proof + architecture + code + rubric_completeness) / 4

  proof               = pac.proof          (0 or 1)
  architecture        = pac.architecture   (0 or 1)
  code                = pac.code           (0 or 1)
  rubric_completeness = rubric_sum / 6     (0.0–1.0)

confidence < 0.98 → human escalation triggered
```

---

## Setup & Running Locally

### Prerequisites
- Python 3.11+
- Node.js 20.x
- GitHub Token (for repo analysis)
- Groq API Key (for LLM signals)

### Backend

```bash
git clone https://github.com/blackholeinfiverse78-rgb/Parikshak-system.git
cd Parikshak-system

pip install -r requirements.txt

cp .env.example .env
# Set GITHUB_TOKEN and GROQ_API_KEY in .env

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

API docs available at: `http://localhost:8000/docs`

### Frontend

```bash
cd frontend
npm install
npm start
```

UI available at: `http://localhost:3000`

### Environment Variables

```env
GITHUB_TOKEN=your_github_token
GROQ_API_KEY=your_groq_key
ALLOWED_ORIGINS=["http://localhost:3000"]
JWT_SECRET_KEY=your_secret_key
```

---

## API Endpoints

### Lifecycle
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/lifecycle/submit` | Submit task for evaluation |
| GET | `/api/v1/lifecycle/history` | All submission history |
| GET | `/api/v1/lifecycle/review/{id}` | Review result by submission ID |
| GET | `/api/v1/lifecycle/next/{id}` | Next task by submission ID |

### Production (Niyantran)
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/production/niyantran/submit` | Accept task from Niyantran |
| GET | `/api/v1/production/niyantran/health` | Niyantran connection health |
| GET | `/api/v1/production/bucket/logs` | Recent evaluation logs |
| GET | `/api/v1/production/bucket/stats` | Bucket statistics |
| GET | `/api/v1/production/bucket/evaluation/{trace_id}` | Evaluation by trace_id |
| GET | `/api/v1/production/human-review/pending` | Pending escalations |
| POST | `/api/v1/production/human-review/override` | Apply human override |
| GET | `/api/v1/production/system/production-status` | Full system status |
| POST | `/api/v1/production/test/determinism` | Run determinism test |

### TTS (Vaani)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/tts/speak` | Generate speech audio |
| GET | `/api/v1/tts/prosody` | Get prosody hint |
| GET | `/api/v1/tts/languages` | List supported languages and tones |

---

## Determinism Test Results

```bash
python tests/test_determinism_proof.py
```

| Test | Scenario | Result |
|------|----------|--------|
| TC-1 | Identical input × 3 runs | score=10.0 × 3 identical |
| TC-2 | Missing REVIEW_PACKET | HARD_GATE_FAILURE |
| TC-3 | Partial submission (no repo) | score=0.0, 3 caps applied |
| TC-4 | Full valid submission | score=10.0, APPROVED, confidence=1.0 |
| TC-5 | Failure case (empty repo) | proof_cap applied, escalation=True |
| TC-6 | Parser parse-only check | no score/status/decision in output |
| TC-7 | Task selection × 3 runs | NT-ADV-B-001 × 3 identical |

**7/7 PASSED — SYSTEM IS DETERMINISTIC**

---

## Boundary Rules

| Rule | Enforcement |
|------|-------------|
| Assignment Engine = ONLY scoring authority | No parallel scoring paths exist |
| No task generation | `task_selection_engine` selects from Niyantran graph only |
| No adaptive / RL logic | All scoring is purely mathematical |
| trace_id must come from Niyantran | Missing trace_id → REJECT at intake |
| Bucket write is mandatory | Every evaluation logged, no exceptions |
| Bucket reads restricted | Only `same_task_history` and `escalation_cases` |
| REVIEW_PACKET is a hard gate | Missing or malformed → score 0, no evaluation |

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.11, FastAPI, Pydantic v2 |
| Frontend | React 18, TailwindCSS, Axios, React Query |
| TTS | VaaniTTS (gTTS primary, pyttsx3 fallback) |
| Storage | Local JSONL (bucket_logs, escalations) |
| Deployment | Render (backend web service + static frontend) |

---

## Engine File Map

| Engine | File |
|--------|------|
| Assignment Engine (scoring authority) | `service/assignment_engine.py` |
| Signal Engine (supporting only) | `service/signal_engine.py` |
| Decision Engine (Phase 5) | `service/production_decision_engine.py` |
| Task Selection (Niyantran graph) | `service/task_selection_engine.py` |
| Review Packet Parser (hard gate) | `service/review_packet_parser.py` |
| Domain Router | `service/domain_router.py` |
| Human-in-Loop | `service/human_in_loop.py` |
| Bucket Integration | `service/bucket_integration.py` |
| Niyantran Connection | `service/niyantran_connection.py` |
| Validation Gate | `service/shraddha_validation.py` |
| Registry Validator | `service/validator.py` |
| Final Convergence Orchestrator | `service/final_convergence.py` |
