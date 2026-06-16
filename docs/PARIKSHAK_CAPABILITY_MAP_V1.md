# Parikshak Capability Map (v1)

This document maps all operational capabilities present in the Parikshak codebase today, detailing their inputs, outputs, human involvement constraints, codebase evidence, and operational status.

---

## 1. Task Review (Ad-hoc / Legacy API)
- **Purpose**: Evaluates legacy task submissions containing descriptions and repository links deterministically, mapping them to next-step task assignments.
- **Input**:
  - `description` / `task_description` (string)
  - `github_url` / `github_repo_link` (string)
  - `submitted_by` (string)
  - `pdf_file` (optional, uploaded file)
- **Output**:
  - A structured JSON response containing `status` (PASS/PARTIAL/FAIL), `review` text, `score` (integer), `next_task` ID, and `trace_id`.
- **Human Involvement Required**: 
  - Results are placed in `PENDING_REVIEW` state. In order to release task assignments, review operators or judges must manually approve or override the decision via the review API endpoints.
- **Evidence**:
  - API endpoint: [api/task_review.py:review_task](file:///c:/Users/black/Downloads/Live%20Task%20Review%20Agent%20-%202/Live%20Task%20Review%20Agent%20-%202/api/task_review.py#L82-L189)
  - Processing logic: [task_selector/review_orchestrator.py:process_submission](file:///c:/Users/black/Downloads/Live%20Task%20Review%20Agent%20-%202/Live%20Task%20Review%20Agent%20-%202/task_selector/review_orchestrator.py#L41-L381)
- **Current Status**: **LIVE** (backwards-compatible console interface and HTTP REST endpoint for the HackaVerse demo).

---

## 2. Repository Review & Analysis
- **Purpose**: Clones or queries the GitHub tree metadata recursively to collect file metrics, structure depth, layer directories, and file contents for checking.
- **Input**:
  - `repository_url` (string, e.g., `https://github.com/owner/repo`)
- **Output**:
  - `structure`: Total files, directories, depth, and file extension distribution.
  - `components`: Groups of files matching routing, service, database model, test, and documentation patterns.
  - `architecture`: Boolean indicating layered separation, layer count, list of found layers, modularity status.
  - `quality`: Scores for README size, documentation density, and presence of a license.
- **Human Involvement Required**: None (fully automated background task triggered during signal collection).
- **Evidence**:
  - Analyzer module: [evaluation_engine/repository_analyzer.py](file:///c:/Users/black/Downloads/Live%20Task%20Review%20Agent%20-%202/Live%20Task%20Review%20Agent%20-%202/evaluation_engine/repository_analyzer.py)
- **Current Status**: **LIVE** (relies on GitHub API or local curl fallback under broken DNS environments).

---

## 3. Submission Review & Lifecycle Tracking
- **Purpose**: Provides CRUD storage, history, and status updates for submitted tasks, enforcing sequential lifecycle states (`assigned` -> `submitted` -> `reviewed`).
- **Input**:
  - Form parameters (`task_title`, `task_description`, `submitted_by`, `github_repo_link`, `module_id`, `schema_version`, optional `pdf_file`).
- **Output**:
  - `submission_id` (string)
  - `submission_timestamp` (ISO datetime)
  - `review_summary`: evaluation result (PASS/FAIL), decision, score, status.
  - `next_task_summary`: next task ID, title, difficulty, and type.
- **Human Involvement Required**: 
  - Required. Submissions are persisted with `review_state="PENDING_REVIEW"`. Transitioning to `APPROVED` or `REJECTED` requires manual invocation of approval endpoints.
- **Evidence**:
  - Lifecycle endpoints: [api/lifecycle.py](file:///c:/Users/black/Downloads/Live%20Task%20Review%20Agent%20-%202/Live%20Task%20Review%20Agent%20-%202/api/lifecycle.py)
  - Persistent store: [db/persistent_storage.py](file:///c:/Users/black/Downloads/Live%20Task%20Review%20Agent%20-%202/Live%20Task%20Review%20Agent%20-%202/db/persistent_storage.py)
- **Current Status**: **LIVE** (maintains the backend dashboard state).

---

## 4. Rule Validation (Sri Satya Rule Engine)
- **Purpose**: Evaluates extracted repository and task signals against 4 sequential binary checks (Schema, Completeness, Logic, Integration) to assign a PASS/FAIL result.
- **Input**:
  - `signals` (dictionary of extracted signals)
  - `rules` (optional dictionary of task-specific overrides from the database)
- **Output**:
  - `evaluation_result` ("PASS" or "FAIL")
  - `failure_type` (string: "schema_violation", "incomplete", "incorrect_logic", "integration_fail", or `None` if PASS)
  - `pac` and `rubric` binary validation dictionaries.
- **Human Involvement Required**: None (deterministic automated checking).
- **Evidence**:
  - Core class: [evaluation_engine/rule_engine.py](file:///c:/Users/black/Downloads/Live%20Task%20Review%20Agent%20-%202/Live%20Task%20Review%20Agent%20-%202/evaluation_engine/rule_engine.py)
- **Current Status**: **LIVE** (governs all task evaluations).

---

## 5. Workflow Routing & Graph Traversal (Parikshak Engine)
- **Purpose**: Evaluates current task ID, PASS/FAIL result, and failure type, traversing the JSON-defined task graph to choose the exact correction or advancement path.
- **Input**:
  - `current_task_id` (string)
  - `evaluation_result` ("PASS" or "FAIL")
  - `failure_type` (string or `None`)
- **Output**:
  - `selected_task_id` (string)
  - `selection_reason` (string)
- **Human Involvement Required**: None for calculation, but the resulting transition remains staged until approved.
- **Evidence**:
  - Graph model: [db/niyantran_tasks.json](file:///c:/Users/black/Downloads/Live%20Task%20Review%20Agent%20-%202/Live%20Task%20Review%20Agent%20-%202/db/niyantran_tasks.json)
  - Traversal engine: [task_selector/task_graph_engine.py](file:///c:/Users/black/Downloads/Live%20Task%20Review%20Agent%20-%202/Live%20Task%20Review%20Agent%20-%202/task_selector/task_graph_engine.py)
  - Convergence handler: [task_selector/final_convergence.py](file:///c:/Users/black/Downloads/Live%20Task%20Review%20Agent%20-%202/Live%20Task%20Review%20Agent%20-%202/task_selector/final_convergence.py)
- **Current Status**: **LIVE** (rigidly routes failed submissions to corresponding correction tasks, and passed submissions to advancement tasks).

---

## 6. Governance Review & Dual Approval (Gov-OS Layer)
- **Purpose**: Validates cryptographic signatures, actor permissions, event payload hashes, and prevents update/delete operations on the event journal database.
- **Input**:
  - `GovernanceEnvelope` (containing checksums, actors, trace ID, signature approvals).
- **Output**:
  - SQLite record appended to the event journal, returning transaction details.
- **Human Involvement Required**: 
  - Dual approval required. Validates that the event's `authorized_by` property matches the allowlist of human governors (`AUTHORIZED_GOVERNORS = {"Akash", "Vinayak"}`).
- **Evidence**:
  - Preventative triggers: [canonical_db/db.py:_init_db](file:///c:/Users/black/Downloads/Live%20Task%20Review%20Agent%20-%202/Live%20Task%20Review%20Agent%20-%202/canonical_db/db.py#L66-L100)
  - Validation code: [canonical_db/db.py:_append_event_sync](file:///c:/Users/black/Downloads/Live%20Task%20Review%20Agent%20-%202/Live%20Task%20Review%20Agent%20-%202/canonical_db/db.py#L106-L157)
  - Constitutional policies: [governance_layer/governance.py](file:///c:/Users/black/Downloads/Live%20Task%20Review%20Agent%20-%202/Live%20Task%20Review%20Agent%20-%202/governance_layer/governance.py)
- **Current Status**: **LIVE** (intercepts every transaction to the SQL event stream).

---

## 7. Replay-based State Reconstruction & Snapshotting
- **Purpose**: Validates database integrity at boot by verifying the SHA-256 chain of events, replaying the event logs to build read models, and restoring state from backup snapshots.
- **Input**:
  - Event sequence number or JSONL audit logs.
- **Output**:
  - Reconstructed read model database, or verification status indicators.
- **Human Involvement Required**: None for automated boot scans; manually triggered by operators for rollback/restoration.
- **Evidence**:
  - Restore engine: [canonical_db/backup.py](file:///c:/Users/black/Downloads/Live%20Task%20Review%20Agent%20-%202/Live%20Task%20Review%20Agent%20-%202/canonical_db/backup.py)
  - Recovery tool: [canonical_db/recovery.py](file:///c:/Users/black/Downloads/Live%20Task%20Review%20Agent%20-%202/Live%20Task%20Review%20Agent%20-%202/canonical_db/recovery.py)
  - Boot gate logic: [canonical_db/integrity.py](file:///c:/Users/black/Downloads/Live%20Task%20Review%20Agent%20-%202/Live%20Task%20Review%20Agent%20-%202/canonical_db/integrity.py)
- **Current Status**: **LIVE** (runs on start to verify database hashes and rollback state).

---

## 8. Observability & System Auditing
- **Purpose**: Tracks operational metrics (database reads/writes, thread queues, error flags, trace IDs) and persists structured execution outputs.
- **Input**:
  - Execution receipts, trace logs.
- **Output**:
  - System performance payloads (CPU, memory, lock contentions).
  - Diagnostic logs.
- **Human Involvement Required**: None.
- **Evidence**:
  - System observer: [observability/observability.py](file:///c:/Users/black/Downloads/Live%20Task%20Review%20Agent%20-%202/Live%20Task%20Review%20Agent%20-%202/observability/observability.py)
  - Audit log writer: [replay_audit/atomic_persistence.py](file:///c:/Users/black/Downloads/Live%20Task%20Review%20Agent%20-%202/Live%20Task%20Review%20Agent%20-%202/replay_audit/atomic_persistence.py)
- **Current Status**: **LIVE** (runs continuously alongside the FastAPI runtime).

---

## 9. Judge Assistance & Low-Confidence Escalation
- **Purpose**: Computes a deterministic confidence score (`(proof + architecture + code + rubric_completeness) / 4`) and flags cases with score `< 0.98` for human judge review.
- **Input**:
  - Evaluation outputs, decision results, and supporting signals.
- **Output**:
  - `ConfidenceMetrics` object.
  - Creation of an escalation record in `storage/escalations`.
- **Human Involvement Required**: 
  - Essential. Judges must manually query the queue and submit override requests to resolve low-confidence tasks.
- **Evidence**:
  - Escalation logic: [task_selector/human_in_loop.py](file:///c:/Users/black/Downloads/Live%20Task%20Review%20Agent%20-%202/Live%20Task%20Review%20Agent%20-%202/task_selector/human_in_loop.py)
- **Current Status**: **LIVE** (runs on every evaluation to protect edge cases).

---

## 10. Vaani Text-to-Speech (TTS) Standalone
- **Purpose**: Generates synthesized speech WAV/MP3 files for task reviews and descriptions, incorporating language/tone-specific prosody mappings.
- **Input**:
  - `text` (string, max 500 chars)
  - `lang` (string language code, e.g. "en")
  - `tone` (string tone, e.g. "friendly")
- **Output**:
  - Synthesized speech audio bytes (`audio/mpeg` or `audio/wav`).
- **Human Involvement Required**: None.
- **Evidence**:
  - API endpoint: [api/tts.py](file:///c:/Users/black/Downloads/Live%20Task%20Review%20Agent%20-%202/Live%20Task%20Review%20Agent%20-%202/api/tts.py)
  - Vaani mappings: [VaaniTTS_Standalone/](file:///c:/Users/black/Downloads/Live%20Task%20Review%20Agent%20-%202/Live%20Task%20Review%20Agent%20-%202/VaaniTTS_Standalone)
- **Current Status**: **PARTIAL** (standalone endpoints work, but it is not integrated into any candidate evaluation or task routing workflow).

---

## 11. Testing Assistance & Diagnostics
- **Provide**: Runs automated integration validation checks against the system boundaries.
- **Input**:
  - Terminal launch commands.
- **Output**:
  - Verification reports and execution exit codes.
- **Human Involvement Required**: Triggered by system administrators.
- **Evidence**:
  - Self-test: [scratch/test_operating_system.py](file:///c:/Users/black/Downloads/Live%20Task%20Review%20Agent%20-%202/Live%20Task%20Review%20Agent%20-%202/scratch/test_operating_system.py)
  - Readiness check: [tests/production_readiness_test.py](file:///c:/Users/black/Downloads/Live%20Task%20Review%20Agent%20-%202/Live%20Task%20Review%20Agent%20-%202/tests/production_readiness_test.py)
- **Current Status**: **LIVE**.
