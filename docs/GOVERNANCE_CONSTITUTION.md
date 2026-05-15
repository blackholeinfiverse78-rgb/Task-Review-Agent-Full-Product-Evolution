# GOVERNANCE CONSTITUTION — TANTRA OPERATIONAL AUTHORITY

## 1. AUTHORITY HIERARCHY
1. `REVIEW_OPERATOR`: Can view and approve/reject standard queue items.
2. `SENIOR_REVIEW_OPERATOR`: Can perform all above, plus initiate high-risk `modify` escalations.
3. `EXECUTION_AUTHORIZER`: Dual-approval authority. Required to co-sign any `modify` action.
4. `SYSTEM_AUDITOR`: Read-only operational oversight.
5. `REPLAY_AUDITOR`: Has authority to run forensic divergence reports and reconstruct execution.

**Rule**: No single operator can silently control the full execution path.

## 2. ESCALATION SOVEREIGNTY
- `modify` operations represent an escalation to bypass the deterministic graph.
- An escalation requires an explicit `authorized_by` signature.
- Escalations may ONLY alter the selected task boundary (`override_task_id`), leaving the audit lineage untouched.
- Traversal logic itself is sealed and immutable to operators.

## 3. IRREVERSIBLE GOVERNANCE STATES
The following states are monotonically locked and cannot be reverted without a formal superseding governance event:
- `APPROVED`
- `REJECTED`
- `MODIFIED`
- `FINAL_APPROVED`
- `AUDIT_LOCKED`
- `REPLAY_SEALED`

Once entering these states, any attempt to transition the state again will fail with `HTTP 409 Conflict`. All transitions are protected by strict **Optimistic Concurrency Control (OCC) locking** utilizing the `expected_version` parameter to prevent concurrent race conditions.

## 4. DASHBOARD CONTAINMENT
The operational dashboard is an observability surface ONLY.
- **Action Gateway**: Every button click is forced through `api/review_routes.py` which executes `constitutional_validator.validate()`.
- **Authority Isolation**: The dashboard cannot mutate traversal logic, skip the approval queue, or alter replay events.
- **Operator Visibility**: `OPERATOR_VISIBILITY_LOG` tracks all actions, including blocked requests, in an append-only JSONL format.
