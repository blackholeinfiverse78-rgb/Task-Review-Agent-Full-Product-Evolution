# REVIEW PACKET — Parikshak Production Validation

**Version:** v6.0.0
**Status:** PROVEN OPERATIONAL SYSTEM

---

## 1. Entry Points

| Module / Path | Role |
| :--- | :--- |
| `main.py` | FastAPI app startup |
| `api/parikshak_routes.py` | API endpoint `/parikshak/review` (consumed by HackaVerse) |
| `canonical_db/db.py` | SQLite event journal and mutex single-writer queue |
| `canonical_db/integration.py` | EcosystemIntegrator (Saarthi, Niyantran, Bucket adapters) |

---

## 2. Core Execution Flow

```
Submission Intake (/parikshak/review)
    |
    v
Signal Collection (signal_engine)
    |
    v
Rule Engine Check (schema -> completeness -> logic -> integration)
    |
    v
Graph Traversal (final_convergence)
    |
    v
Human Review Queue (PENDING_REVIEW)
    |
    v
Human Decides (APPROVE / REJECT / MODIFY)
    |
    v
Ecosystem Ingest (propagate_governed_approval)
    |
    ├── Commit to Gov-OS Event Journal (Append-only Trigger locked)
    ├── Dispatch Task to Niyantran Assignments Ledger
    ├── Log Downstream Visibility to Saarthi
    └── Log Evaluation Metrics to Bucket
```

---

## 3. Live Flow & Verification

The integration verification test successfully executed a live end-to-end traversal:
- Simulates intake for `trace-ecosystem-proof-999`.
- Evaluates signals using the Rule Engine.
- Generates a human-signed `review_history` envelope.
- Propagates event downstream, writing to `saarthi_visibility.jsonl` and `niyantran_assignments.jsonl`.
- Proves database write serialization, ensuring absolute transaction order integrity.

---

## 4. What Changed

We added the following core features and validation suites:
- **Dataset Intake validation** (`evaluation_engine/dataset_intake.py`): Validates required intake fields and serializes to `storage/traces/{trace_id}/intake_packet.json`.
- **BHIV Candidate Review Engine** (`evaluation_engine/bhiv_review_engine.py`): Run local repository analyses and passes code context to llama-3.3-70b-versatile via Groq to produce structured reports with the 8 mandatory review fields, with a deterministic rule-based fallback.
- **Ecosystem Integration** (`canonical_db/integration.py`): Appends trace replay evidence to Pravah ledger (`storage/pravah_replay.jsonl`) and propagates approval events on human sign-off via `/api/v1/review/approve`.
- **Executive Comparison** (`scripts/compare_reviews.py`): Compares Parikshak automated reviews against executive reviews in `review_packets/final_gc_review.md` and outputs comparison report.
- **Backup & Validation Isolation** (`canonical_db/integrity.py` and `canonical_db/backup.py`): Dynamically resolves isolated backup subfolders `storage/backups/{db_name}` by DB file name to prevent validation checkpoint mismatch safety blocks.

We also added comprehensive validation suite `tests/test_candidate_review_pipeline.py`.

---

## 5. Failure Cases

The system enforces hard errors under the following failure modes:
1. **Empty/Malformed Payload**: Triggers HTTP 400 Bad Request.
2. **Missing required fields**: Triggers validation exceptions (such as missing `reviewed_by` or empty `trace_id`).
3. **Database Corruption**: If journal hashes are altered, `scan_and_verify()` fails on boot, locking all database writes.
4. **Autonomous Release Attempt**: Any event signed without human authorization triggers `AutonomousReleaseBlocked` exceptions.

---

## 6. Handover Notes & Recommended Steps

### Known Limits & Risks
- **SQLite Single-Writer Limit**: Highly parallel writes are serialized by a threading mutex. High-volume transactional scaling is limited by SQLite lock serialization.
- **Static Schema Registry**: Models are frozen at runtime. Schema additions require migration manifest changes.

### Fresh Developer Onboarding
- Run all checks: `python -m pytest tests/`
- Run candidate reviewer checks: `python -m pytest tests/test_candidate_review_pipeline.py`
- Run comparison script: `python scripts/compare_reviews.py`
- DB journal logic is located in `canonical_db/db.py`, integrations in `canonical_db/integration.py`, and rule sets in `evaluation_engine/rule_engine.py`.

---

## 7. BHIV Candidate Submission Validation (First-Stage Reviewer)

Parikshak has been evolved into the default first-stage reviewer for BHIV candidate submissions.

### Core Modules
1. **Dataset Intake Module** (`evaluation_engine/dataset_intake.py`): Validates and ensures all evaluation inputs are available before starting evaluation.
2. **Production Review Engine** (`evaluation_engine/bhiv_review_engine.py`): Executes the evaluation pipeline. Generates the structured executive review format (What's Done Well, Missing/Incomplete, Required Fixes, Score/10, Readiness %, Timeline, Evidence, Verdict). Every finding references supporting codebase evidence.
3. **Next-Task Dispatch** (`task_selector/task_graph_engine.py`): Traverse graph to determine the next task and includes a short justification.
4. **Ecosystem Propagation** (`canonical_db/integration.py` & `/api/v1/review/approve`): Commits approved reviews to Gov-OS DB, dispatches to Niyantran assignments ledger, exposes visibility to Saarthi visibility ledger, and writes trace replay evidence to Pravah ledger (`storage/pravah_replay.jsonl`) verifying complete trace continuity.
5. **Executive Comparison Report** (`scripts/compare_reviews.py`): Compares automated review against human executive review. Measures agreements, differences, missed findings, false positives, and calculates alignment confidence score. Output saved in `review_packets/executive_comparison_report.md`.
6. **Isolated Safety Gates**: Dynamically computes backup path by database basename (e.g. `storage/backups/canonical_db`) to resolve test vs. prod snapshot mismatch errors.

---

## 8. Hardened Production Certification (Phase IV)

In Phase IV, Parikshak has been hardened for production certification. The following mechanisms have been introduced:

### 1. Close Security Gate (Role-Based Access Control)
- **Role Enforcement**: Enforces strictly defined roles (`Governor`, `Reviewer`, `Operator`, `Read Only`) across all endpoints.
- **JWT Middleware**: Validates signatures, expiration (`Expired credentials` error), and role permissions.
- **Replay Attack Protection**: An in-memory token registry rejects duplicate approval token hashes with `409 Conflict` (`REPLAY_REJECT`).
- **Startup Secrets Validation**: Executes `validate_startup_secrets()` at boot time to block execution if insecure or default secret keys are configured.
- **Signed Governance Proofs**: Every override action persists `validation_decision.json` (signature, timestamp, version, signer details) and `governance_record.json` to the trace directory.

### 2. Executable Dependency Verification
- **Dynamic Scanner**: Resolves packages dynamically from the active runtime environment rather than static files.
- **Pinning & Normalization**: Verifies strict `==` pinning, checks version compatibility, detects circular dependencies, and filters out forbidden packages (`unverified_lib`, `unsafe_bridge_plugin`, `backdoor`). Normalizes package name hyphens and underscores (e.g., `pydantic-core` / `pydantic_core`).
- **SBOM Export**: Dynamically generates and writes a CycloneDX v1.5 compliant `sbom.json` containing version metadata and package checksums to the trace folder.
- **Verdict Enforcement**: Fails production certification if dependency validation fails.

### 3. Dataset Intake & Self-Certification
- **17 production fields**: Expanded dataset intake pipeline to support: *Assigned Task, Original Assignment Document, Repository Path, Repository Commit / Branch, Review Packet, Expected Deliverables, Candidate Name, Candidate Identifier, Submission Timestamp, Due Date, Supporting Evidence, Architecture Notes, Integration Notes, Runtime Evidence, Test Evidence, Documentation Evidence, and Additional Instructions*.
- **Backward Compatibility**: A custom Pydantic `@model_validator` maps older payloads cleanly without data loss.
- **Self-Certification Loop**: Full pipeline runs deterministically: Intake -> Evaluation -> Human Review Escalate -> human Override -> Gov-OS Commit -> Saarthi -> Bucket -> Pravah Replay -> Production Certification -> Evidence Export.


