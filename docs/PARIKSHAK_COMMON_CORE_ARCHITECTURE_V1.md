# PARIKSHAK COMMON CORE ARCHITECTURE (V1)

This document establishes the architecture of the Parikshak Common Core, defining the internal engines that drive evaluation explainability, task routing, and confidence calibration. It also establishes the boundaries of what the Common Core does and does not own.

---

## 1. Architectural Blueprint

The Parikshak Common Core sits between raw ingestion boundaries (External / Internal) and the immutable governance storage layer, operating as a deterministic intelligence and recommendation engine.

```
                  +-----------------------------------+
                  |        Ingestion Boundary         |
                  |  [External Mode]  [Internal Mode] |
                  +-----------------+-----------------+
                                    |
                                    v
+-----------------------------------v-----------------------------------+
|                        PARIKSHAK COMMON CORE                          |
|                                                                       |
|  +------------------------+  +-------------------+  +--------------+  |
|  |     Evidence Engine    |  | Confidence Engine |  | Replay Engine|  |
|  |  (Collate Repo & Run)  |  | (Deterministic)   |  | (Evaluation) |  |
|  +-----------+------------+  +---------+---------+  +------+-------+  |
|              |                         |                   |          |
|              v                         v                   v          |
|  +-----------v------------+  +---------v---------+  +------v-------+  |
|  |  Explainability Engine |  | Calibration Engine|  |Subject Rec   |  |
|  |  (Human-Readable Notes)|  | (Rule Tuning)     |  | (Gurukul)    |  |
|  +-----------+------------+  +---------+---------+  +------+-------+  |
|              |                         |                   |          |
|              +-------------------------+-------------------+          |
|                                        |                              |
|                                        v                              |
|                      +-----------------v-----------------+            |
|                      |   Assignment Recommendation Engine |            |
|                      |  (Route via Niyantran Graph/Task) |            |
|                      +-----------------+-----------------+            |
+----------------------------------------|------------------------------+
                                         |
                                         v
                  +----------------------+--------------------+
                  |    Gov-OS Storage & Verification Layer    |
                  |  [Event Journal]  [Constitutional Check]  |
                  +-------------------------------------------+
```

---

## 2. Core Engines & Ownership

### 2.1 Evidence Engine
*   **Responsibility**: Gathers and correlates inputs (git diffs, file structures, PDF descriptions, test results) to establish factual evidence of completion.
*   **Functionality**: Inspects whether required layers, directories, files, and functional components exist. Does not make qualitative guesses.

### 2.2 Explainability Engine
*   **Responsibility**: Converts factual evidence and PASS/FAIL outcomes into structured, human-readable override logs and review notes.
*   **Functionality**: Explains the exact failure reasons (e.g., "Failed Completeness: No test files found under `/tests` folder, violating constraint").

### 2.3 Confidence Engine
*   **Responsibility**: Standardizes confidence scores mathematically to check if human intervention is required.
*   **Functionality**: Enforces the deterministic formula `confidence = (proof + architecture + code + rubric_completeness) / 4`. Generates an escalation case if confidence `< 0.98`.

### 2.4 Calibration Engine
*   **Responsibility**: Monitors performance parameters (pass rates, override logs) against ground-truth decisions to prevent threshold drift.
*   **Functionality**: Provides parameters to adjust rule configurations dynamically without rebuilding the core.

### 2.5 Replay Validation Engine
*   **Responsibility**: Evaluates the correctness of the Common Core by executing historical task submissions against new rule sets.
*   **Functionality**: Generates statistical metrics comparing automated predictions with human decisions.

### 2.6 Subject & Course Recommendation Engine
*   **Responsibility**: Recommends learning paths and skill progression modules to candidates who fail specific tasks.
*   **Functionality**: Maps the identified failure reasons (e.g., `incorrect_logic` in Authentication) to Gurukul training packages.

### 2.7 Assignment Recommendation Engine
*   **Responsibility**: Recommends next tasks and project placements for successful candidates, or remediation tasks for failures.
*   **Functionality**: Traverses the task hierarchy and aligns recommendations with candidate skill profiles.

---

## 3. Boundary Definition: What the Common Core DOES NOT Own

To avoid duplicate capabilities and disconnected intelligence, the Common Core strictly delegates the following responsibilities:

1.  **Code Execution & Sandboxing (Delegated to Niyantran)**: Parikshak does not run unit tests, compile source code, or manage runtimes. It consumes the execution report generated by Niyantran's secure sandbox.
2.  **Developer Profiles & Identity (Delegated to Gurukul)**: Parikshak does not maintain developer portfolios, track overall performance histories, or issue certificates. It queries Gurukul profiles dynamically.
3.  **Project Prioritization & Schedules (Delegated to TMS)**: Parikshak does not determine the roadmaps of live projects or schedule deadlines. It requests priority task backlogs from TMS.
4.  **Transaction Mutations (Delegated to MDU/Saarthi)**: Parikshak does not execute state updates on live candidate pipelines or persist records directly to system ledgers. It generates recommendation payloads which are committed via Gov-OS.
5.  **Final Governance Approvals (Delegated to GC)**: Parikshak cannot autonomously release task assignments or override failures. All mutations must be signed off by a human Governor (GC).
