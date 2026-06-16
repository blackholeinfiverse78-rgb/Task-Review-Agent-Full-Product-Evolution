# Consumer Safety Model

- **Version**: 1.0.0
- **Status**: ACTIVE / VERIFIED
- **Target Audience**: Integrators, Architects, Security Auditors

---

## 1. Safety Architecture Overview
The safety model of Parikshak ensures that it functions strictly as a **deterministic policy evaluator** rather than an execution or scoring authority. By enforcing strict boundaries at runtime, the system protects both itself from malicious inputs and external consumers from accidental authority leakage.

```
+-------------------------------------------------------------+
|               EXTERNAL CONSUMER (HackaVerse, etc.)         |
+-------------------------------------------------------------+
                              |
                              v  (Submit Task, trace_id required)
+-------------------------------------------------------------+
|                     PARIKSHAK SYSTEM                        |
|                                                             |
|  [Ingestion Gate] ------> [Binary Rule Core]                |
|         |                        |                          |
|         v                        v                          |
|  (Pydantic Schema)       (Static Structures Only)           |
|                                  |                          |
|                                  v                          |
|                      [Confidence Calculation]               |
|                                  |                          |
|                                  v                          |
|                      [Escalation staging]                   |
+-------------------------------------------------------------+
                              |
                              v  (Confidence < 0.98 -> HALT)
+-------------------------------------------------------------+
|                    GOVERNED HUMAN OVERRIDE                  |
|                                                             |
|  Authorized Signatures Only: {"Akash", "Vinayak", etc.}     |
|  No AI or Autonomous System approval allowed.               |
+-------------------------------------------------------------+
                              |
                              v  (Append Mutation)
+-------------------------------------------------------------+
|               GOV-OS IMMUTABLE EVENT LEDGER                 |
|                                                             |
|  SQLite WAL Mode. Update/Delete disabled via SQL Triggers.  |
+-------------------------------------------------------------+
```

---

## 2. Bounded Ownership Map

### 2.1 What Parikshak Owns
- **Input Payload Verification**: Enforcing Pydantic models at entry.
- **Evidence Extraction (Signal Engine)**: Parsing metadata (file counts, README header structure, and PDF text).
- **Evaluation Decisioning (Sri Satya Gates)**: Deterministic evaluation of extracted signals against binary gates.
- **Escalation Detection**: Isolating borderline submissions and writing to the `storage/escalations` queue.
- **Ledger Persistence**: Appending cryptographically chained, sequence-tracked events to the database journal.

### 2.2 What Parikshak DOES NOT Own
- **AI/LLM-based Qualitative Assessment**: Heuristics are explicitly deleted.
- **Code Compilation or Active Test Run Execution**: Parikshak never runs sandbox container tests or compiles code; it reads generated execution output profiles.
- **Dynamic Grade Generation or Portfolio Mapping**: Scoring is static placeholder grading, and recommendations are pre-defined templates.
- **Direct Assignment Dispatch**: It cannot directly release a task to active student lists; it publishes events, and downstream integrators dispatch them.

---

## 3. Operational Ceilings

### 3.1 Authority Ceiling
- **Definition**: No autonomous release of assignments.
- **Safety Bound**: All ingestion results are staged as `PENDING_REVIEW` in a queue. Even if a submission receives a clean `PASS`, it must pass through the governor approval loop before being committed and propagated downstream.

### 3.2 Execution Ceiling
- **Definition**: Sandbox code isolation.
- **Safety Bound**: The system does not write, execute, or build user code. It performs shallow structure checks (e.g. file counts, directory layouts, and keyword occurrence checks) to completely eliminate remote code execution (RCE) vectors.

### 3.3 Governance Ceiling
- **Definition**: Immutable journal sequence and hard-coded reviewer credentials.
- **Safety Bound**: Only actions signed by pre-defined actors are accepted. SQLite-level database triggers reject all `UPDATE` or `DELETE` commands, making database manipulation impossible even for administrative processes.

### 3.4 Scoring Ceiling
- **Definition**: Static placebo scores.
- **Safety Bound**: The dynamic grading engine is entirely removed. The score returned is a static constant:
  - `100` for a successful `PASS`
  - `40` for an evaluation `FAIL`
  - `0` for validation or intake hard-gate rejections.

### 3.5 Assignment Ceiling
- **Definition**: No dynamic task generation.
- **Safety Bound**: The next-task selection is deterministic and mapped directly to a pre-defined static task registry file. It is impossible for the system to invent new tasks or change prerequisite routes dynamically.
