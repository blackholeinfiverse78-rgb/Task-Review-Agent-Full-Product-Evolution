# REVIEW PACKET — Parikshak v6.0.0

## ENTRY POINT

**Primary File**: `main.py`
**Secondary Files**: `api/production.py`, `api/review_routes.py`, `api/gov_os_routes.py`

**Routes**:
- `POST /api/v1/production/niyantran/submit` → `api/production.py` — JSON with trace_id
- `GET /api/v1/production/niyantran/health` → `api/production.py`
- `GET /api/v1/review/pending` → `api/review_routes.py`
- `GET /api/v1/review/all` → `api/review_routes.py`
- `POST /api/v1/review/approve` → `api/review_routes.py`
- `POST /api/v1/review/reject` → `api/review_routes.py`
- `POST /api/v1/review/modify` → `api/review_routes.py`
- `POST /api/v1/gov-os/mutate` → `api/gov_os_routes.py`
- `GET /api/v1/gov-os/export` → `api/gov_os_routes.py`
- `POST /api/v1/gov-os/scaffold` → `api/gov_os_routes.py`
- `POST /api/v1/gov-os/rollback` → `api/gov_os_routes.py`
- `POST /api/v1/gov-os/reconstruct` → `api/gov_os_routes.py`
- `POST /api/v1/gov-os/integrate` → `api/gov_os_routes.py`

Entry accepts JSON from Niyantran with trace_id. Every submission enters a single sequential pipeline. No parallel paths. trace_id must come from upstream — never generated inside Parikshak.

---

## CORE FLOW

```
Submission Input (trace_id required from Niyantran)
    |
    v
[Step 0] REVIEW_PACKET Hard Gate
    |  File: evaluation_engine/review_packet_parser.py
    |  Rule: REVIEW_PACKET.md missing or malformed -> FAIL, schema_violation
    v
[Step 1] Registry Validation
    |  File: evaluation_engine/validator.py
    |  Rule: Invalid module_id or schema_version -> FAIL, schema_violation
    v
[Step 2] Signal Collection — SUPPORTING ONLY
    |  File: evaluation_engine/signal_engine.py
    |  Collects: repo signals, feature match, title/desc signals, pdf signals
    v
[Step 3] Rule Engine — SINGLE EVALUATION AUTHORITY
    |  File: evaluation_engine/rule_engine.py
    |  4 binary checks in strict order, first failure stops:
    |    Check 1: schema_violation   (repo OR word_count >= 50)
    |    Check 2: incomplete         (code + proof + architecture + file_count >= 3)
    |    Check 3: incorrect_logic    (delivery_ratio >= 0.6 AND word_count >= 80)
    |    Check 4: integration_fail   (repo accessible, metadata present)
    |  Output: evaluation_result = PASS | FAIL
    |          failure_type = schema_violation | incomplete | incorrect_logic | integration_fail
    v
[Step 4] Graph Traversal — DETERMINISTIC
    |  File: task_selector/task_graph_engine.py
    |  PASS  -> task.next_tasks[0]
    |  FAIL  -> task.failure_tasks[failure_type][0]
    |  No fallback. Missing mapping -> HARD REJECT
    v
[Step 5] Output Contract Enforcement
    |  File: evaluation_engine/execution_pipeline.py
    |  Exactly 8 fields enforced. Extra or missing -> HARD_REJECT
    |  Fields: trace_id, submission_id, evaluation_result, failure_type,
    |          selected_task_id, selection_reason, source, schema_version
    v
[Step 6] Persist to storage
    |  File: db/persistent_storage.py + task_selector/bucket_integration.py
    |  review_state = PENDING_REVIEW
    |  trace_id stored on ReviewRecord
    v
[Step 7] Human Governance Gate
    |  File: api/review_routes.py + governance_layer/governance.py
    |  APPROVE -> state=APPROVED, task assigned (requires operator role)
    |  REJECT  -> state=REJECTED, no assignment
    |  MODIFY  -> state=MODIFIED, override task (requires dual approval)
    |  All actions validated by ConstitutionalValidator
    v
[Step 8] Gov-OS Event Journal (on governed mutations)
    |  File: canonical_db/pipeline.py + canonical_db/db.py
    |  GovernanceEnvelope validated -> SHA-256 chain appended -> snapshot created
    |  Autonomous release -> AutonomousReleaseBlocked raised
    v
[Step 9] Bucket + Observability Logging
       File: task_selector/bucket_integration.py + observability/observability.py
       Writes: evaluation_result, failure_type, decision, trace_id
```

---

## LIVE FLOW

**Endpoint**: `POST /api/v1/production/niyantran/submit`

**Request**:
```json
{
  "task_id": "T-GOV-001",
  "task_title": "REST API Service with Layered Architecture, Authentication Module, and Pipeline Design",
  "task_description": "Objective: Build a production-ready REST API service with a modular, layered architecture including authentication, authorization, and role-based access control. Requirements: Implement JWT-based authentication and token validation middleware. Design a service layer, data access layer, and API controller layer. Build user management module with CRUD operations and schema validation. Implement async request pipeline with error handling and structured logging. Add integration tests and unit tests. Include a README with architecture overview and API contract documentation.",
  "submitted_by": "Akash",
  "repository_url": "https://github.com/blackholeinfiverse78-rgb/Parikshak-system",
  "module_id": "task-review-agent",
  "schema_version": "v1.0",
  "trace_id": "trace-a3f2c1d48b9e4f2a"
}
```

**Sequential pipeline execution**:
1. `review_packet_parser.enforce_packet_requirement(".")` → valid=True
2. `registry_validator.validate_complete("task-review-agent", "v1.0")` → VALID
3. `signal_engine.collect_supporting_signals(...)` → repo analyzed, features matched
4. `rule_engine.evaluate(signals)` → Check1=pass, Check2=pass, Check3=pass, Check4=pass → PASS
5. `task_graph_engine.traverse("T-GOV-001", "PASS", null)` → selected_task_id=T-GOV-002
6. `_enforce_boundary(output)` → 8 fields verified
7. `product_storage.store_submission(...)` + `store_review(...)` → review_state=PENDING_REVIEW
8. `bucket_integration.log_evaluation(...)` → trace_id written to JSONL

**trace_id propagation**:
- Received from Niyantran at intake
- Passed unchanged through all steps
- Written to bucket log and Gov-OS journal as final field
- NO override at any step

---

## OUTPUT SAMPLE

```json
{
  "trace_id": "trace-a3f2c1d48b9e4f2a",
  "submission_id": "sub-eb2e07e7c652-d42768ed",
  "evaluation_result": "PASS",
  "failure_type": null,
  "selected_task_id": "T-GOV-002",
  "selection_reason": "PASS -> next_tasks[0] = T-GOV-002",
  "source": "task_graph",
  "schema_version": "v1.0"
}
```

---

## PASS CONDITIONS (exact thresholds)

| Check | Rule | Threshold |
|---|---|---|
| Schema | No repo → description word count | ≥ 50 words |
| Completeness: code | Repository available with files | file_count > 0 |
| Completeness: proof | README, tests, or docs present | readme_val ≥ 1 OR test_files > 0 |
| Completeness: architecture | Arch keyword in title/desc OR layers ≥ 2 | keywords: architecture, layer, service, module, component, design, flow, pipeline, orchestrat |
| Completeness: file count | Minimum files in repo | ≥ 3 files |
| Logic: alignment | delivery_ratio AND missing features | ratio ≥ 0.6 AND missing ≤ 3 |
| Logic: effort | Description word count OR README | word_count ≥ 80 OR readme_val ≥ 1 |
| Integration | Repo accessible with metadata | metadata.name present, no error |

---

## GOV-OS ENFORCEMENT

All governed mutations (assignment approvals, review commits) pass through:
- `canonical_db/pipeline.py` → `GovernedPipeline.submit_mutation()`
- Requires `authorized_by` in `AUTHORIZED_GOVERNORS` set
- `AI_Orchestrator_Agent` → raises `AutonomousReleaseBlocked`
- Missing `authorized_by` → raises `PermissionError`
- Every event appended with SHA-256 hash chain to `canonical_db.sqlite`
- Boot integrity scan on every `CanonicalDB` init — blocks startup on corruption

---

## PROOF

**Gov-OS Diagnostic Suite — 12/12 PASSED**

Same input always produces same output — verified across repeated runs.

| Guarantee | Status | Evidence / Reference |
|---|---|---|
| No UPDATE/DELETE on event journal | VERIFIED | SQLite triggers block in `db.py` |
| Autonomous release blocked | VERIFIED | `AutonomousReleaseBlocked` raised on `AI_Orchestrator_Agent` in `pipeline.py` |
| Schema drift rejected | VERIFIED | `FrozenRegistry` + Pydantic in `contracts.py` |
| Corruption detected at boot | VERIFIED | SHA-256 chain scan in `IntegrityValidator` |
| Snapshot restore verified | VERIFIED | `file_hash` + `state_hash` parity in `backup.py` |
| Concurrent writes ordered | VERIFIED | `SingleWriterQueue` locks in `db.py` |
| GPT bridge read-only | VERIFIED | Draft scaffolds under human review only in `gpt_bridge.py` |
| Deterministic replay | VERIFIED | Reconstructed `state_hash` matches perfectly |
| Output contract 8 fields | VERIFIED | `_enforce_boundary()` |
| trace_id preserved unchanged | VERIFIED | Preserved from Niyantran ingestion to bucket adapter |
| Human approval enforced | VERIFIED | Dual enforcement in `GovernedPipeline` + `human_in_loop.py` |
| 12/12 TEST SUITE | PASS | `scratch/test_operating_system.py` |

### TANTRA Verification Evidence Logs (v6.0.0 Stable Deployment)
- **Vinayak Validation Protocol (`tests/production_readiness_test.py`)**: **100% PASS (7/7 Phases)**
  - *Phase 1 (Review Packet Enforcement)*: **PASSED**
  - *Phase 2 (Evaluation Engine Wiring)*: **PASSED** (Canonical score: 40, status: fail)
  - *Phase 3 (Decision & Output Standardization)*: **PASSED** (Decision: REJECTED)
  - *Phase 4 (Bucket Integration)*: **PASSED** (Trace ID: `test-bucket-trace-123` verified)
  - *Phase 5 (Niyantran Connection)*: **PASSED** (Niyantran Health: `healthy`)
  - *Phase 6 (Human-in-Loop Escalation)*: **PASSED** (Escalated successfully, pending escalations: 324)
  - *Phase 7 (Deployment Stability & Determinism)*: **PASSED** (3 identical runs produced identical scores/failures/tasks)
- **Deterministic Replay state_hash**: `8d4eeea32de1ed3e12d0364a3935456349f5746424d205977ba06b7968adf68e` (Verified match: `True` in `proofs/deterministic_replay_proof.json`)
- **Snapshot Restore Parity**: **PASSED** (`restore_successful = True` in `proofs/snapshot_restore_proof.json`)
  - *Manifest*: `storage/backups/snapshot_seq_1_20260526_084133.json`
  - *File signature hash*: `84a1dacf2649edf464aaa5297b63822f4c54da662edf567377c684fb4d1a8baa`
  - *State signature hash*: `9d0b1fad105fb242de9bdf23d4b7133814b827f3248f5d149b17da9ff07b298d`
- **Concurrency Containment**: **PASSED**
  - *Fail-Closed Case (Empty DB)*: Spawning `threads_spawned=5` on a non-existent DB triggers `DATABASE_CORRUPT` via `IntegrityValidator.run_full_scan()` before locking, failing closed (`events_written=0`, `strictly_ordered=False`).
  - *Serialized Case (Initialized DB)*: Spawning `threads_spawned=5` on a pre-initialized DB serializes concurrent writes cleanly, resulting in `events_written=5` with sequence `[1, 2, 3, 4, 5]`.

**→ SYSTEM GOV-OS COMPLIANT — v6.0.0**
