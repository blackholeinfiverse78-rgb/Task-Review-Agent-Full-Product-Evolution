# REVIEW PACKET — TANTRA UNIFIED INFRASTRUCTURE

## ENTRY POINT
**Primary File**: `main.py`
**Routers registered**:
- `api/lifecycle.py` → `/api/v1`
- `api/tts.py` → `/api/v1`
- `api/production.py` → `/api/v1/production`
- `api/review_routes.py` → `/api/v1/review`

**Orchestrators**:
- `evaluation_engine/execution_pipeline.py` — unified pipeline entry point
- `api/review_routes.py` — human governance approval layer

**Critical Files**:
- `task_selector/task_graph_engine.py` — deterministic graph traversal
- `evaluation_engine/rule_engine.py` — single evaluation authority
- `db/persistent_storage.py` — `ReviewRecord`, `TaskSubmission`, `ProductStorage`
- `contracts/review_models.py` — `ReviewState`, `ReviewActionRequest`, `AuditLogEntry`

Every submission enters a single sequential pipeline. No parallel paths. **trace_id MUST come from upstream. Missing or short trace_id results in HARD REJECT.**

---

## REPO STRUCTURE & OWNERSHIP
The repository has been deterministically flattened to remove ambiguity:
- `/evaluation_engine` -> Rule/Signal evaluation engine.
- `/task_selector` -> Graph traversal.
- `/governance_layer` -> Human constitutional authority.
- `/replay_audit` -> Replay continuity and observability.
- `/observability` -> Metrics.
- `/db` -> Persistence layer.
- `/contracts` -> Unbreakable DTO schemas.
- `/api`, `/frontend`, `/tests`, `/docs`

Ownership map is available at `docs/OWNERSHIP_BOUNDARIES.md`.
Unified Contracts are defined at `contracts/registry.md`.

---

## CORE FLOW
```
POST /api/v1/production/niyantran/submit
    |
    v
[execution_pipeline.execute()]
    |
    ├── trace_id validation          HARD REJECT if missing or < 8 chars
    ├── evaluation_orchestrator      Sri Satya — 4 binary rule checks
    ├── task_graph_engine.traverse   Parikshak — deterministic graph lookup
    ├── _enforce_boundary()          7-field contract validation
    └── _persist()                   Stores ReviewRecord (PENDING_REVIEW)
    |
    v
Response: { review_state: "PENDING_REVIEW", status: "QUEUED" }
    |
    ← NOTHING sent to Niyantran yet ←
    |
    v
[Step 7] Human Governance Layer       api/review_routes.py
    |
    ├── APPROVE  POST /api/v1/review/approve
    │       guard: state must be PENDING_REVIEW
    │       sets:  review_state = APPROVED
    │       logs:  audit entry (action=approve, final_task=selected_task_id)
    │
    ├── REJECT   POST /api/v1/review/reject
    └── MODIFY   POST /api/v1/review/modify
    |
    v
[Step 8] Replay Checkpoint & Bucket Logging
    |
    v
Final assignment reaches Niyantran ONLY after human approval
```

---

## GOVERNANCE MODEL
Governance is CONSTITUTIONAL.
- No auto-approval.
- No semantic bypass.
- Human review is the ONLY authority that can unblock the assignment release.
- Modifying bounding parameters requires dual execution approval.

---

## REPLAY MODEL
Replay engine is separated into `replay_audit/replay_engine.py`.
Reconstruction fetches the event history by `trace_id` and deterministically rebuilds the decision path with checksum verification to prove operational continuity.

---

## FAILURE TESTS
| Case | Trigger | Result |
|---|---|---|
| Concurrent Approvals | Double-call `/approve` | 409 Conflict rejection. |
| Restart Recovery | Persistence Check | ProductStorage safely reconstructs queue via `/pending`. |
| Corrupted Replay | Mismatch Hash | `REPLAY_DIVERGENCE` hard error. |
| Duplicate Submission | Niyantran Task Resubmit | Deterministic fallback to matching `trace_id`. |
| Invalid Transition | Modify w/o Task | 400 Bad Request. |

---

## LIVE PROOF SECTION
**1. Niyantran Execution Log**
```json
{
  "trace_id": "trace-abcdef-001",
  "submission_id": "sub-32616cd5a6c8-cdef-001",
  "evaluation_result": "FAIL",
  "failure_type": "schema_violation",
  "selected_task_id": "T-GOV-F01",
  "selection_reason": "FAIL(schema_violation) -> T-GOV-F01",
  "source": "task_graph"
}
```

**2. State Before Approval**
`Current DB state: PENDING_REVIEW`

**3. Governance Log**
`Approval result: {'status': 'APPROVED', 'submission_id': 'sub-...', 'assigned_task': 'T-GOV-F01', 'event_id': 'evt-6b67a0ce6cf6'}`

**4. State After Approval**
`State after approval: ReviewState.APPROVED`

**5. Replay Trace Proven**
```json
{
  "trace_id": "trace-abcdef-001",
  "date": "2026-05-14",
  "events_found": 1,
  "events": [
    {
      "event_id": "evt-6b67a0ce6cf6",
      "action": "approve",
      "reason_taxonomy": "REQUIREMENT_CORRECTION",
      "system_task": "T-GOV-F01",
      "final_task": "T-GOV-F01",
      "finalized": true,
      "_checksum": "04d1bbd2f3464beb"
    }
  ],
  "integrity": "verified"
}
```

---
---
**FINAL STATUS**: SYSTEM IS TANTRA COMPLIANT & REPLAY SAFE.

---

## CONSTITUTIONAL GOVERNANCE HARDENING
- **Authority Hierarchy**: Rigid role definitions implemented (`REVIEW_OPERATOR`, `EXECUTION_AUTHORIZER`, etc.).
- **Escalation Sovereignty**: `modify` requires dual approval (`authorized_by`) and is restricted strictly to bounded metadata updates.
- **Irreversible States**: `APPROVED`, `REJECTED`, `MODIFIED`, `FINAL_APPROVED`, `AUDIT_LOCKED`, `REPLAY_SEALED`. Locked via `_enforce_pending_state`.
- **Override Restrictions**: Bounded strictly to `OverrideScope`.

## PERSISTENCE DURABILITY & CONCURRENCY
- **Atomic Writes**: `atomic_append` enforces temp-file staging, fsync durability, and atomic rename.
- **Append Serialization**: Cross-platform file locks ensure concurrent append protection.
- **OCC Locking**: Governance actions enforce `expected_version` validation to block concurrent races.

## DASHBOARD CONTAINMENT
- **Blocked Mutation Paths**: The dashboard has no direct DB access. All actions route strictly through `constitutional_validator`.
- **Action Gateway Proof**: Bypassing role authorization instantly triggers `GOVERNANCE_REJECT` HTTP 403.
- **Authority Isolation**: Operator interactions are logged dynamically in an isolated visibility audit layer.

## ADVERSARIAL TESTING LOGS
The `AdversarialSuite` ran 5 corruption simulations. All were successfully trapped and isolated:
1. **Interrupted Writes**: Caught `JSON parse error` and executed partial line recovery without stopping.
2. **Stale Checkpoints**: Identified invalid state hash against recomputed deterministic JSON checksum.
3. **Replay Divergence**: Flagged field mutation (`T-GOV-001` != `T-GOV-002`) and rejected silently mutated execution.
4. **Concurrent Approvals**: Validated Optimistic Concurrency lock. Rejected second request with `GOVERNANCE_LOCK_REJECT`.
5. **Dashboard Privilege Escalation**: Denied standard operator attempting a `modify` traversal bypass.

---
**FINAL CONSTITUTIONAL STATUS**: ADVERSARIAL HARDENING COMPLETE. SYSTEM IS CHECKSUM-VERIFIED, GOVERNANCE-LOCKED, AND MUTATION-PROOF UNDER FAILURE.
