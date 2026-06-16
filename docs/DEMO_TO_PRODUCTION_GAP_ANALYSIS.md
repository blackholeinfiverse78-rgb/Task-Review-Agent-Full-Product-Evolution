# Parikshak Demo to Production Gap Analysis

This document outlines the gap between Parikshak's current status and a production-ready deployment, separated into operational, partially operational, conceptual, and missing systems.

---

## A. Operational Today
*   **Immutable append-only event journal**: SQLite backend with triggers blocking `UPDATE` and `DELETE` queries on the `events` table.
*   **Monotonic sequence verification**: Chronological transaction commits ordered exclusively by SQLite autoincrement sequence numbers.
*   **Boot validation safety gate**: Verifies SHA-256 chain hashes and event payload checksums at startup. Blocks initialization on any mismatch.
*   **Governance envelope validation**: Checks trace ID length, event schemas against the frozen registry, actor role allowlists, and human signatures.
*   **Single-writer mutex containment**: Thread-safe write lock serializing SQLite writes.
*   **Low-confidence human escalation queue**: Creates persistent escalation records in `storage/escalations` when evaluation confidence score `< 0.98`.
*   **Process-level file locking**: Enforces cross-process mutex locks on the JSON persistent store using PID checking.
*   **Deterministic graph traversal**: Traverses `db/niyantran_tasks.json` based on binary PASS/FAIL results.

---

## B. Partially Operational
*   **Vaani TTS Integration**: The standalone speak, prosody, and language API endpoints exist and connect with `VaaniTTS_Standalone`, but they are completely disconnected from candidate evaluations or task selection routing.
*   **Startup Checkpoint Isolation**: The boot scanner loads all JSON files in `storage/backups`. Since the directory is shared, manifests from different SQLite databases (e.g. created during test runs or separate deployments) conflict, triggering `CHECKPOINT_MISMATCH` and blocking database boot.
*   **GitHub Tree Analyzer**: Recursively crawls file tree names and extension types, but it is restricted to public repositories (unless GITHUB_TOKEN is manually injected) and has a shallow check for "test" or "route" keywords in paths.
*   **Ecosystem Propagation**: The integrations module contains scripts (`niyantran_adapter.py`, etc.) that read database events, but they are not automated daemon/listener processes. They must be triggered manually or via API routes.

---

## C. Conceptual
*   **Strategic Recommendations**: `StrategicApprovalEngine` creates advisory suggestion objects for candidates, but these are unused by the task router.
*   **Candidate Profile Tracking**: The frozen registry allows registering `CandidateProfile` payloads, but candidate history is not updated dynamically or analyzed.

---

## D. Missing
*   **Content-to-Intent Validation**: The system checks if file counts and generic filenames exist, but it does not check if the code matches the task topic. This enables unrelated files to receive a `PASS`.
*   **Tech Stack Match Enforcement**: `FeatureMatcher` calculates the tech stack match ratio, but the `RuleEngine` completely ignores it. Python tasks can be completed in Javascript, Go, or Java.
*   **Architecture Match Enforcement**: `FeatureMatcher` computes whether architecture layer folders match, but `RuleEngine` completely ignores it.
*   **Code Compilation & Execution**: The system cannot compile, test, or execute code.
*   **Scalable Persistent Storage**: Operational data is stored in-memory and dumped to a flat JSON file (`product_state.json`) on every write. This layer is hard-capped at 1,000 active records.
