# Parikshak Capability Map (Evidence-Backed)

This map evaluates documented system capabilities against active runtime evidence.

### 1. Task Review (Ad-hoc API)
* **Description**: Evaluates legacy task submissions containing description and repository links.
* **Evidence Source**: `api/task_review.py`, `tests/run_eval.py`
* **Operational Status**: **LIVE**
* **Confidence Level**: High (1.00)
* **Dependencies**: `ReviewOrchestrator`, Pydantic schemas.

### 2. Repository Review & Analysis
* **Description**: Clones/scans repository directory structure and computes file/architecture metrics.
* **Evidence Source**: `evaluation_engine/repository_analyzer.py`, `tests/production_readiness_test.py`
* **Operational Status**: **LIVE**
* **Confidence Level**: High (1.00)
* **Dependencies**: GitHub API, git client, local fallback.

### 3. Submission Review & Lifecycle Tracking
* **Description**: Provides CRUD storage, history, and status updates for submitted tasks.
* **Evidence Source**: `api/lifecycle.py`, `db/persistent_storage.py`
* **Operational Status**: **LIVE**
* **Confidence Level**: High (1.00)
* **Dependencies**: Persistent storage models.

### 4. Rule Validation (Sri Satya Rule Engine)
* **Description**: Evaluates signals against sequential binary checks (Schema, Completeness, Logic, Integration).
* **Evidence Source**: `evaluation_engine/rule_engine.py`, `tests/adversarial_attack_suite.py`
* **Operational Status**: **LIVE**
* **Confidence Level**: High (1.00)
* **Dependencies**: Intent Extractor, Feature Matcher.

### 5. Workflow Routing & Graph Traversal (Parikshak Engine)
* **Description**: Chooses exact correction or advancement path based on evaluation outcome.
* **Evidence Source**: `task_selector/task_graph_engine.py`, `task_selector/final_convergence.py`
* **Operational Status**: **LIVE**
* **Confidence Level**: High (1.00)
* **Dependencies**: `niyantran_tasks.json` task graph data.

### 6. Governance Review & Dual Approval (Gov-OS Layer)
* **Description**: Validates cryptographic signatures, event parent hashes, and blocks unauthorized update/delete actions.
* **Evidence Source**: `canonical_db/db.py`, `canonical_db/pipeline.py`
* **Operational Status**: **LIVE**
* **Confidence Level**: High (1.00)
* **Dependencies**: SQLite triggers, `SingleWriterQueue` mutex.

### 7. Replay-based State Reconstruction & Snapshotting
* **Description**: Validates event ledger chain at boot, replays transaction logs, and creates snapshot backups.
* **Evidence Source**: `canonical_db/backup.py`, `canonical_db/integrity.py`
* **Operational Status**: **LIVE**
* **Confidence Level**: High (1.00)
* **Dependencies**: `BackupManager` file writing.

### 8. Observability & System Auditing
* **Description**: Logs database operations, transaction sequences, and error metrics.
* **Evidence Source**: `observability/observability.py`, `replay_audit/atomic_persistence.py`
* **Operational Status**: **LIVE**
* **Confidence Level**: High (1.00)
* **Dependencies**: System log observers.

### 9. Judge Assistance & Low-Confidence Escalation
* **Description**: Flags cases with confidence score < 0.98 for human judge override review.
* **Evidence Source**: `task_selector/human_in_loop.py`, `tests/production_readiness_test.py`
* **Operational Status**: **LIVE**
* **Confidence Level**: High (1.00)
* **Dependencies**: `ConfidenceMetrics` logic, file storage escalations.

### 10. Vaani Text-to-Speech (TTS) Integration
* **Description**: Synthesizes speech review files with language-specific prosody mappings, integrated into execution pipelines.
* **Evidence Source**: `api/tts.py`, `VaaniTTS_Standalone/`, `evaluation_engine/execution_pipeline.py`, `task_selector/review_orchestrator.py`
* **Operational Status**: **LIVE**
* **Confidence Level**: High (1.00)
* **Dependencies**: gTTS, pyttsx3.

### 11. Testing Assistance & Diagnostics
* **Description**: Runs automated self-tests and readiness checks.
* **Evidence Source**: `tests/production_readiness_test.py`, `tests/runtime_benchmarks.py`
* **Operational Status**: **LIVE**
* **Confidence Level**: High (1.00)
* **Dependencies**: test suites.

*Verified: 2026-07-07T07:26:48.603856Z UTC*
