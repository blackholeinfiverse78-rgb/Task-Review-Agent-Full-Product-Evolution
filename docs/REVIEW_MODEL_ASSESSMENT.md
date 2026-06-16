# Parikshak Review Model Assessment

This document assesses the operational capabilities, missing features, manual processes, and technical evidence for each core review model in Parikshak today.

---

## 1. Task Review
- **What exists today**:
  - Deterministic processing of legacy and lifecycle task submissions.
  - Objective extraction using title/description word parsing.
  - Rule-based routing mapping PASS/FAIL outcomes to correction or advancement task sequences using a pre-defined JSON graph.
- **What is missing**:
  - Code execution and testing: The system does not run the candidate's code or tests.
  - Deep semantic parsing: Intent extraction is limited to basic keyword checks.
- **What is manual**:
  - Releasing assignments: All evaluations land in `PENDING_REVIEW` and require human operator approval.
- **Evidence**:
  - Core orchestrator: [task_selector/review_orchestrator.py](file:///c:/Users/black/Downloads/Live%20Task%20Review%20Agent%20-%202/Live%20Task%20Review%20Agent%20-%202/task_selector/review_orchestrator.py)
  - Convergence rules: [task_selector/final_convergence.py](file:///c:/Users/black/Downloads/Live%20Task%20Review%20Agent%20-%202/Live%20Task%20Review%20Agent%20-%202/task_selector/final_convergence.py)

---

## 2. Repository Review
- **What exists today**:
  - GitHub tree crawling (using REST API with curl fallback for DNS-degraded environments).
  - Language detection based on file extensions.
  - Heuristic classification of files (e.g. matching 'route' to routes, 'service' to services).
  - Basic layer check verifying folders for API, Service, and Models are present.
  - Heuristic README scoring based on size (e.g. score=3 if size > 1000 bytes).
- **What is missing**:
  - AST analysis: Filename patterns are inspected, but code syntax or logical correctness are not validated.
  - Non-GitHub support: Only public GitHub URLs are supported.
  - Security/secret scanning: No capability to flag exposed passwords or keys.
- **What is manual**:
  - Providing credentials: Private repo access requires manually injecting the `GITHUB_TOKEN` environment variable.
- **Evidence**:
  - Crawler & classifier: [evaluation_engine/repository_analyzer.py](file:///c:/Users/black/Downloads/Live%20Task%20Review%20Agent%20-%202/Live%20Task%20Review%20Agent%20-%202/evaluation_engine/repository_analyzer.py)

---

## 3. Submission Review
- **What exists today**:
  - In-memory persistent database (`persistent_storage.py`) serialized as JSON to `storage/product_state.json`.
  - Maintains `submissions`, `reviews`, and `next_tasks` models.
  - Implements process-safe locking using a custom `FileLock` to prevent database corruption.
  - Implements automatic LRU eviction, capping total submissions to 1000 items.
- **What is missing**:
  - Relational integrity: The store uses Pydantic objects serialized to a single flat JSON file. No true SQLite or PostgreSQL relational database constraints.
  - Query parameters: Cannot query submissions by range, date, or complex criteria.
- **What is manual**:
  - Initiating reviews: Submissions are loaded and reviewed one-by-one; no automated batch pipelines exist.
- **Evidence**:
  - In-memory store: [db/persistent_storage.py](file:///c:/Users/black/Downloads/Live%20Task%20Review%20Agent%20-%202/Live%20Task%20Review%20Agent%20-%202/db/persistent_storage.py)

---

## 4. Judge Assistance
- **What exists today**:
  - Computes a deterministic confidence score based on the presence of code, proof, architecture, and rubric completeness.
  - Triggers low-confidence escalation if confidence `< 0.98`, writing a record to `storage/escalations`.
  - Exposes override API endpoints `/human-review/pending` and `/human-review/override` to apply manual decisions and reviewer notes.
- **What is missing**:
  - Notification triggers: Judges must poll the API endpoint; no email or webhook notifications exist.
  - Multi-judge consensus: No support for multiple reviewers voting or resolving conflicts.
- **What is manual**:
  - Reviewing details: Judges must read the escalation context, review the candidate's repository manually, and type notes before overriding.
- **Evidence**:
  - Escalation logic: [task_selector/human_in_loop.py](file:///c:/Users/black/Downloads/Live%20Task%20Review%20Agent%20-%202/Live%20Task%20Review%20Agent%20-%202/task_selector/human_in_loop.py)
  - Review routes: [api/production.py](file:///c:/Users/black/Downloads/Live%20Task%20Review%20Agent%20-%202/Live%20Task%20Review%20Agent%20-%202/api/production.py)

---

## 5. Candidate Assessment
- **What exists today**:
  - Pydantic schema for `CandidateProfile` in the frozen registry.
  - Ability to log profile changes as events to the event journal.
- **What is missing**:
  - Automated candidate skill grading: Profiles must be manually submitted and updated.
  - Progress charting: No dashboard exists to visualize candidate skill changes over time.
- **What is manual**:
  - Creating profiles: Done manually via governance mutations.
- **Evidence**:
  - Schema: [canonical_db/contracts.py:CandidateProfile](file:///c:/Users/black/Downloads/Live%20Task%20Review%20Agent%20-%202/Live%20Task%20Review%20Agent%20-%202/canonical_db/contracts.py#L38-L44)

---

## 6. Task Assignment Recommendation
- **What exists today**:
  - Strategic approval engine (`StrategicApprovalEngine`) can generate task suggestions as advisory text.
- **What is missing**:
  - Adaptive recommendation: Suggestions are static templates matching score thresholds; they do not learn from candidate success.
- **What is manual**:
  - Enforcing recommendation: The recommendations are non-binding and require manual governor signatures to execute.
- **Evidence**:
  - Logic engine: [canonical_db/strategic_approval.py](file:///c:/Users/black/Downloads/Live%20Task%20Review%20Agent%20-%202/Live%20Task%20Review%20Agent%20-%202/canonical_db/strategic_approval.py)

---

## 7. Testing Recommendation
- **What exists today**:
  - **No capability exists**. Parikshak does not recommend test modifications, test files, or quality improvements. It only flags "incomplete" if no test files exist in the repository.
- **What is missing**:
  - Test suggestions, test-generation pipelines, coverage targets.
- **What is manual**:
  - Identifying and writing all tests remains 100% manual for the candidate.
- **Evidence**:
  - Absence of files under `/evaluation_engine` or `/task_selector` relating to test recommendation.

---

## 8. Quality Gate Support
- **What exists today**:
  - Enforces a mandatory hard gate check for `REVIEW_PACKET.md` in the submission.
  - Validates markdown sections (`## Entry Point`, `## Current Execution Flow`, etc.) and orders.
  - Extracts JSON blocks from the review packet to verify that mandatory fields (`score`, `decision`, `trace_id`) are present.
- **What is missing**:
  - Code linter integration (no pylint, black, or flake8 checks).
  - Test coverage parsing (doesn't measure candidate test coverage percentage).
- **What is manual**:
  - Evaluating code quality: Judges must manually inspect files to verify quality, as the automated tool only checks for the presence of files.
- **Evidence**:
  - Parser logic: [evaluation_engine/review_packet_parser.py](file:///c:/Users/black/Downloads/Live%20Task%20Review%20Agent%20-%202/Live%20Task%20Review%20Agent%20-%202/evaluation_engine/review_packet_parser.py)
