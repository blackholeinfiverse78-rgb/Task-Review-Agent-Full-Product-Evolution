# UNIFIED CONTRACT REGISTRY

This registry defines the unbreakable deterministic interfaces between TANTRA infrastructure modules.

## 1. Intake Contract (Niyantran -> Parikshak)
```json
{
  "task_id": "string (min 1, max 100)",
  "task_title": "string (min 5, max 200)",
  "task_description": "string",
  "submitted_by": "string",
  "trace_id": "string (min 8) - MANDATORY FROM UPSTREAM"
}
```

## 2. Execution Result Contract (Parikshak -> Governance Queue)
```json
{
  "trace_id": "string",
  "submission_id": "string",
  "review_state": "PENDING_REVIEW",
  "status": "QUEUED"
}
```

## 3. Internal Deterministic Output Contract (Eval -> Traversal)
```json
{
  "trace_id": "string",
  "submission_id": "string",
  "evaluation_result": "PASS | FAIL",
  "failure_type": "string | null",
  "selected_task_id": "string",
  "selection_reason": "string",
  "source": "task_graph"
}
```

## 4. Governance Action Contract (Human -> System)
```json
{
  "trace_id": "string",
  "submission_id": "string",
  "operator_id": "string",
  "operator_role": "REVIEW_OPERATOR | SENIOR_REVIEW_OPERATOR",
  "action": "approve | reject | modify",
  "reason_taxonomy": "string"
}
```

## 5. Audit Log Contract (System -> Replay)
```json
{
  "event_id": "string",
  "trace_id": "string",
  "submission_id": "string",
  "action": "string",
  "timestamp": "iso-string",
  "finalized": "boolean"
}
```
