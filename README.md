# Parikshak — Deterministic Task Review & Gov-OS System

**Version:** v6.0.0
**Status:** CORE LOCKED + GOVERNED OPERATIONAL SYSTEM (Gov-OS) OPERATIONAL

> Parikshak is a deterministic, rule-based engineering task evaluation engine. It evaluates submissions against strict binary rules, routes them to the exact next task via a graph database, and enforces a mandatory human review queue. It is hardened into a Governed Operational System (Gov-OS) featuring an immutable append-only event journal, cryptographic governance envelopes, single-writer concurrency containment, static schema registries, and a startup safety gate.

---

## Gov-OS Architecture Principles

### 1. Immutable Append-Only Event Journal
- **No Mutations**: All database updates and deletes are blocked at the database layer using SQLite triggers.
- **Monotonicity**: Events are sequenced using a strictly monotonic sequence number (`event_sequence`).
- **WAL Mode**: Write-Ahead Logging is enabled on startup to ensure concurrent read safety and durability.
- **Boot Verification**: On startup, a safety gate scans the journal and validates the hash chain from sequence 1.

### 2. Cryptographic Governance Envelopes
Every mutation submitted to Gov-OS must carry a validated envelope containing:
- `trace_id`: The upstream execution trace link.
- `schema_version`: Version of the event definition.
- `actor`: System/Operator identity executing the mutation.
- `actor_role`: Role of the actor (e.g., `operator`, `auditor`).
- `timestamp`: RFC3339/ISO UTC timestamp.
- `lineage_reference`: Pointer to parent trace or execution lineage.
- `approval_token`: Signed token proving authority.
- `payload_checksum`: SHA-256 hash of the canonical serialized payload.
- `parent_event_hash`: SHA-256 hash of the immediately preceding event in the journal.

*Any missing or invalid fields cause immediate rejection of the transaction.*

### 3. Human Approval & Release Lock
- **Explicit Human Gates**: Autonomous task assignment releases by AI agents are strictly blocked.
- **Enforcement Exception**: If a release event is submitted without a `HUMAN_APPROVED` state signature, an `AutonomousReleaseBlocked` exception is raised.
- **GPT Bridge Isolation**: The GPT bridge is quarantined. It is allowed to export state but cannot directly mutate the database or exercise approval/assignment authority.

### 4. Concurrency Containment (Single Writer Queue)
- **Mutex Protection**: A thread-safe mutex and queue serialize all database mutations.
- **Deterministic Ordering**: Ensures events are committed in strict monotonic sequence order, eliminating race conditions.

### 5. Schema Governance
- **Frozen Registry**: Pydantic schemas for the 9 core database entities (`candidate_profiles`, `task_lineage`, etc.) are frozen at runtime to prevent dynamic schema mutations.
- **Migration Manifests**: All changes must be registered in the schema migration manifest (`schema_manifest.json`).

### 6. Isolated Ecosystem Adapters
Adapters under `/integrations/` consume immutable events from the journal only and cannot mutate the DB:
- `niyantran_adapter`: Propagates tasks to Niyantran.
- `bucket_adapter`: Propagates metrics and logs.
- `insightflow_adapter`: Feeds insights to analytical logs.
- `saarthi_adapter`: Dispatches tasks to Saarthi developer visibility ledgers.

---

## API Endpoints (v6.0.0)

### Niyantran Production Pipeline
- `POST /api/v1/production/niyantran/submit`: Evaluates and enqueues tasks.
- `GET /api/v1/production/niyantran/health`: Health status.

### Human Review Operations
- `GET /api/v1/review/all`: Lists all reviews.
- `GET /api/v1/review/pending`: Lists PENDING_REVIEW items.
- `POST /api/v1/review/approve`: Approves assignment.
- `POST /api/v1/review/reject`: Rejects assignment.
- `POST /api/v1/review/modify`: Modifies and overrides assignment.

### Gov-OS System Operations
- `POST /api/v1/gov-os/mutate`: Appends a validated governance envelope to the event journal.
- `GET /api/v1/gov-os/export`: Exports signed system state to GPT.
- `POST /api/v1/gov-os/scaffold`: Formulates a quarantined import scaffold awaiting human approval.
- `POST /api/v1/gov-os/rollback`: Performs deterministic rollback to a checkpoint anchor.
- `POST /api/v1/gov-os/reconstruct`: Replays audit logs to recreate the SQLite database.
- `POST /api/v1/gov-os/integrate`: Integrates and propagates events to external adapters.

---

## Verification & Testing

To run the Gov-OS diagnostic self-test suite (TEST-01 to TEST-12) proving all safety guarantees:
```bash
python -X utf8 scratch/test_operating_system.py
```

To run the proof generation engine generating files under `/proofs`, `/snapshots`, and `/test_vectors`:
```bash
python -X utf8 scripts/generate_proofs.py
```

---

## Evaluation Flow (Task Submission → PASS/FAIL)

Every submission through `POST /api/v1/production/niyantran/submit` runs this deterministic pipeline:

1. **REVIEW_PACKET Gate** — `REVIEW_PACKET.md` must be present and valid or the submission is hard-rejected.
2. **Registry Validation** — `module_id` and `schema_version` must match the static registry.
3. **Signal Collection** — Repository, title, description, and PDF signals are collected (no scoring authority).
4. **Rule Engine** — 4 binary checks in strict order. First failure stops execution:
   - `schema_violation`: no repo and description < 50 words
   - `incomplete`: no code, no proof (README/tests/docs), no architecture keywords, or < 3 files
   - `incorrect_logic`: delivery ratio < 0.6, missing features > 3, or description < 80 words
   - `integration_fail`: repo accessible but metadata missing
5. **Graph Traversal** — PASS routes to `next_tasks[0]`, FAIL routes to `failure_tasks[failure_type][0]`. No fallback.
6. **Output Contract** — Exactly 8 fields enforced: `trace_id`, `submission_id`, `evaluation_result`, `failure_type`, `selected_task_id`, `selection_reason`, `source`, `schema_version`.
7. **Human Review Queue** — All results enter `PENDING_REVIEW`. No assignment is released without human approval.

---

## Tech Stack
- **Backend**: Python 3.11+, FastAPI, SQLite (WAL mode, Trigger locked)
- **Serialization**: Canonical JSON (NFC UTF-8, sorted keys)
- **Frontend**: React 18, Tailwind CSS, React Router v6
