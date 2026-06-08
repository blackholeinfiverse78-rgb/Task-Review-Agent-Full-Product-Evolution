# REVIEW PACKET — Parikshak v7.0.0 (Common Core Integrated)

## ENTRY POINT

**Primary File**: `main.py`  
**Secondary Files**: `api/production.py`, `api/review_routes.py`, `api/gov_os_routes.py`

**Routes**:
*   `POST /api/v1/production/niyantran/submit` → `api/production.py` — Intake endpoint for submissions (external or internal).
*   `GET /api/v1/production/niyantran/health` → `api/production.py`
*   `GET /api/v1/review/pending` → `api/review_routes.py`
*   `POST /api/v1/review/approve` → `api/review_routes.py`
*   `POST /api/v1/review/reject` → `api/review_routes.py`
*   `POST /api/v1/gov-os/mutate` → `api/gov_os_routes.py`

*Note on trace_id discipline*: Ingests raw task execution events. The `trace_id` must come from upstream (Niyantran/Saarthi) and is preserved across all pipeline and governance steps.

---

## CORE FLOW & COMMON CORE ALIGNMENT

Parikshak does not compile code, run tests, or maintain candidate skill portfolios. The Common Core consumes raw signals from the BHIV ecosystem and runs a deterministic recommendation pipeline.

```
       Submission Intake (trace_id required from Niyantran)
                                |
                                v
+---------------------------------------------------------------+
|                      COMMON CORE PIPELINE                     |
|                                                               |
| [Step 0] REVIEW_PACKET Hard Gate (Validate markdown structure)|
|                                |                              |
| [Step 1] Ingest Ecosystem data (Niyantran runs, Gurukul skills)|
|                                |                              |
| [Step 2] Signal Engine (Collate repository and test metrics)   |
|                                |                              |
| [Step 3] Sri Satya Rule Engine (4 binary checks in order):    |
|          Check 1: schema_violation                            |
|          Check 2: incomplete                                  |
|          Check 3: incorrect_logic                             |
|          Check 4: integration_fail                            |
|                                |                              |
| [Step 4] Confidence & Escalation Engine                       |
|          Calculate: (proof + arch + code + rubric) / 4        |
|          Threshold: confidence < 0.98 -> Escalate             |
|                                |                              |
| [Step 5] Recommendation Engine                                |
|          approved -> next task in Graph (TMS prerequisites)   |
|          rejected -> remediation task / course (Gurukul)      |
|                                |                              |
| [Step 6] Output Contract Enforcement (Enforce 8-field JSON)   |
+-------------------------------|-------------------------------+
                                |
                                v
+---------------------------------------------------------------+
|                     GOVERNANCE & LIFECYCLE                    |
|                                                               |
| [Step 7] In-Memory Staging (review_state = PENDING_REVIEW)    |
|                                |                              |
| [Step 8] Gov-OS Approval (Signed mutation by Governor)        |
|                                |                              |
| [Step 9] Event Journal Commit (SQLite immutable SHA-256 chain)|
+---------------------------------------------------------------+
```

---

## LIVE FLOW

**Endpoint**: `POST /api/v1/production/niyantran/submit`

**Request**:
```json
{
  "task_id": "T-GOV-001",
  "task_title": "REST API Service with Layered Architecture",
  "task_description": "Objective: Build a production-ready REST API service. Requirements: Implement service, controller, and data layers.",
  "submitted_by": "Akash Dev",
  "repository_url": "https://github.com/developer/sec-auth",
  "module_id": "task-review-agent",
  "schema_version": "v1.0",
  "trace_id": "trace-a3f2c1d48b9e4f2a"
}
```

**Sequential Processing**:
1.  `review_packet_parser.enforce_packet_requirement(".")` → valid=True.
2.  `registry_validator.validate_complete(...)` → validates schema and actor.
3.  **Ecosystem Fetch**: Fetch unit test results from **Niyantran** and skills profile from **Gurukul**.
4.  `rule_engine.evaluate(signals)` → runs Sri Satya logic.
5.  `human_in_loop.process_with_human_loop(...)` → escalates if confidence $< 0.98$.
6.  `task_graph_engine.traverse(...)` → selects next task based on outcomes and prerequisites.
7.  `execution_pipeline._enforce_boundary(...)` → verifies exactly 8 fields in the output JSON.

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

## PASS CONDITIONS (Sri Satya Binary Gate Heuristics)

| Check | Rule | Threshold | Signal Source |
|---|---|---|---|
| **Schema** | No repo → description word count | $\ge 50$ words | Ingestion Payload |
| **Completeness: code** | Repository contains source code files | `file_count > 0` | Sampada / GitHub Crawler |
| **Completeness: proof** | README documentation or test files exist | `readme_val >= 1` OR `test_files > 0` | Sampada / GitHub Crawler |
| **Completeness: arch** | Architecture keywords present or folders $\ge 2$ | `layer_count >= 2` or keywords matched | Sampada / GitHub Crawler |
| **Completeness: files** | Minimum files in code repository | $\ge 3$ files | Sampada / GitHub Crawler |
| **Logic: alignment** | Submissions match task deliverables | `delivery_ratio >= 0.6` | Niyantran sandbox outputs |
| **Logic: effort** | Descriptions or documentation length | `word_count >= 80` OR `readme_val >= 1` | Ingestion / Sampada |
| **Integration** | Repository accessible with metadata | Metadata matches, no connection errors | Sampada / GitHub API |

---

## GOV-OS ENFORCEMENT

All database mutations and routing overrides pass through:
*   `canonical_db/pipeline.py` → `GovernedPipeline.submit_mutation()`.
*   Requires signature approval matching `AUTHORIZED_GOVERNORS = {"Akash", "Vinayak"}`.
*   Enforces append-only triggers on SQLite table transactions.
*   Verifies event hashes at boot to prevent schema drift and snapshot divergence.
