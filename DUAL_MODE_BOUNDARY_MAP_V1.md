# DUAL MODE BOUNDARY MAP (V1)

This document establishes the functional boundary map for Parikshak's dual modes of operation. While both modes leverage the same underlying Common Core, they serve distinct operational contexts:
1.  **External Mode**: MahaIT / Government Review Copilot (assisting external judges and recommending subjects).
2.  **Internal Mode**: BHIV Execution Copilot (assisting developer workflows, candidate placement, and task transitions).

---

## 1. Dual Mode System Boundaries

```
                 +---------------------------------------+
                 |          Parikshak Core               |
                 | (Rule Heuristics, Confidence Formula, |
                 |  Immutable Event Journal Ingestion)   |
                 +-------------------+-------------------+
                                     |
             +-----------------------+-----------------------+
             |                                               |
             v                                               v
+------------v------------+                     +------------v------------+
|      External Mode      |                     |      Internal Mode      |
| (MahaIT Gov Copilot)    |                     | (BHIV Execution Copilot)|
|                         |                     |                         |
| * Judge Assistance      |                     | * Candidate Placement   |
| * Subject Recs (Courses)|                     | * Task Routing Graph    |
| * Copilot Advisory UI   |                     | * Dependency Maps       |
| * External Audit Logs   |                     | * Run Execution Advisory|
+------------+------------+                     +------------+------------+
             |                                               |
             +-----------------------+-----------------------+
                                     |
                                     v
                 +-------------------v-------------------+
                 |        Human Approval Points          |
                 |  (Gov-OS Signature Release Gates)     |
                 +---------------------------------------+
```

---

## 2. Component Taxonomy

### 2.1 Shared Common Core Components
These components run identically across both modes to ensure consistency, reproducibility, and security.
*   **Sri Satya Rule Engine**: Executes the 4 sequential evaluation checks.
*   **Confidence Calibration Engine**: Computes deterministic confidence metrics and triggers human-in-the-loop escalations.
*   **Immutable SQLite Event Journal**: Commit database mutations under monotonic sequence ordering.
*   **Repository Tree Crawler**: Inspects directories, README files, testing suites, and configurations.
*   **Observability Monitor**: Logs performance statistics, error counts, and API response delays.

### 2.2 External-Only Components (MahaIT / Government Copilot)
Designed for public sector governance and judge support.
*   **Judge Assistance Console**: UI for government reviewers to inspect escalated cases and register override votes.
*   **Subject Recommendation Engine**: Recommends study topics, reference manuals, or regulatory guidelines from Gurukul based on failure reasons.
*   **Explainable Rationale Generator**: Formulates detailed documentation logs showing exactly how a submission performed against governance rules.

### 2.3 Internal-Only Components (BHIV Execution Copilot)
Designed for internal developer velocity and team coordination.
*   **Candidate Placement Engine**: Recommends optimal candidate placements onto team structures based on Gurukul skill matrices.
*   **Task Graph Dependency Map**: Computes prerequisite pathways and tracks parallel workflows.
*   **Run Execution Advisor**: Recommends immediate code fixes or test adjustments to developers based on Niyantran sandbox failures.

---

## 3. Human Approval Points (Gov-OS Gates)

To guarantee that AI recommendations do not autonomously mutate the ecosystem state, we enforce strict human approval checkpoints:

```
[System Recommendation] ---> [Confidence Check] ---> [Approval Checkpoint] ---> [Signed Mutation]
                                                            |
                                                   Signature Verified?
                                                   /                 \
                                                 YES                  NO
                                                 /                     \
                                     [Appended to Event Log]    [REJECTED & Blocked]
```

### 3.1 External Mode Approval Gate
*   **Event**: Releasing a final candidate grade or certifying a task completion.
*   **Checkpoint**: If automated confidence $< 0.98$, the task is escalated. A signed cryptographic token from an **Authorized Judge** is required to resolve the escalation.
*   **Enforcement**: The SQLite database rejects commits that do not contain a valid, signed `authorized_by` payload in the `GovernanceEnvelope`.

### 3.2 Internal Mode Approval Gate
*   **Event**: Assigning a new correction or advancement task to a developer, or updating a skill certificate.
*   **Checkpoint**: All task assignment recommendations are advisory. Committing a transition to Niyantran's active database requires approval from the **Team Lead** or **Project Governor**.
*   **Enforcement**: Any mutation submitted directly by an AI actor raises `AutonomousReleaseBlocked`.
