# STAKEHOLDER DISCUSSIONS LOG

This document records the alignment and design discussions held with stakeholders across the BHIV ecosystem to define integration boundaries and contracts.

---

## 1. Summary of Stakeholder Alignments

```
+------------------+------------------------------+-------------------------------------------------+
| Stakeholder      | Alignment Area               | Core Agreement / Outcome                        |
+------------------+------------------------------+-------------------------------------------------+
| Sri Satya        | Shared Common Core           | Sri Satya engine retains sole PASS/FAIL authority|
| Nikhil           | Niyantran Integration        | Ingest test runner outputs from Niyantran sandbox|
| Rishabh          | Workflow Validation          | Verify developer submission states dynamically  |
| Soham            | Gurukul Integration          | Fetch developer competence profiles dynamically |
| MDU / Saarthi    | Canonical Data Discipline    | Lock sqlite event schemas & trace ID references|
| GC               | Governance Boundaries        | Enforce governor signatures on overrides        |
| TMS              | Ecosystem Direction          | Map task recommendations to prerequisite graphs|
+------------------+------------------------------+-------------------------------------------------+
```

---

## 2. Detailed Alignment Logs

### 2.1 Sri Satya (Intelligence Layer)
*   **Discussion Goal**: Define how the rule engine is shared between modes.
*   **Outcome**: Sri Satya's Rule Engine acts as the single evaluation authority. Both External and Internal modes execute the same 4 binary checks (Schema, Completeness, Logic, Integration). To prevent heuristic drift, the engine configuration will be tuned solely using parameters, keeping the core code compile-locked.

### 2.2 Nikhil (Niyantran Integration)
*   **Discussion Goal**: Prevent duplication of code compilation and run tracking.
*   **Outcome**: Nikhil confirmed that Niyantran already compiles candidate code and runs tests in a sandbox environment. Parikshak will not implement code compilation or running. Instead, Nikhil's adapters will export standard test execution metrics (`tests_passed`, `tests_total`, `build_output`) which Parikshak's Evidence Engine will consume.

### 2.3 Rishabh (Workflow Validation)
*   **Discussion Goal**: Validate live developer interactions within team workflows.
*   **Outcome**: Rishabh agreed to inspect the submission lifecycle state. Parikshak will stage evaluations as `PENDING_REVIEW` and transition them to `APPROVED` or `REJECTED` only when matching a signed event from Rishabh's workflow validation service.

### 2.4 Soham (Gurukul Integration)
*   **Discussion Goal**: Align task placement with candidate skill growth.
*   **Outcome**: Soham agreed to expose an endpoint to retrieve candidate profiles (`skills` dictionary and certificates). Parikshak's Recommendation Engine will query this endpoint during next-task calculations to ensure proposed assignments match the candidate's active skill level.

### 2.5 MDU (Canonical Data Discipline)
*   **Discussion Goal**: Guarantee event lineage and database replay integrity.
*   **Outcome**: MDU validated the schema triggers on the SQLite event store. MDU requested that all reasoning artifacts and governance signatures are logged in the append-only journal, enabling complete history reconstruction during rollbacks.

### 2.6 GC (Governance Boundaries)
*   **Discussion Goal**: Limit AI recommendation authority.
*   **Outcome**: GC insisted that Parikshak remains a recommendation-only system. Final assignment commits require a human signature. If Parikshak's confidence falls below $0.98$, the system will route the evaluation to GC's human reviewer queue.

### 2.7 TMS (Ecosystem Direction)
*   **Discussion Goal**: Maintain a unified task prerequisite tree.
*   **Outcome**: TMS requested that task graphs are stored in a standard JSON format (`niyantran_tasks.json`) to allow long-term convergence. TMS will manage task creation, while Parikshak maps candidates along these predefined nodes.
