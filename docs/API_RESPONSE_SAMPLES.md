# API Response Samples - Validated Deterministic Output

The following samples represent the **EXACT** 7-field contract enforced by the Parikshak system.

## 1. PASS Case (Success)

```json
{
  "trace_id": "trace-pass-verified-001",
  "submission_id": "sub-8d2f1b3e9a7c-4e2a1b3d",
  "evaluation_result": "PASS",
  "failure_type": null,
  "selected_task_id": "T-GOV-002",
  "selection_reason": "PASS -> next_tasks[0] = T-GOV-002",
  "source": "task_graph"
}
```

## 2. FAIL Case (schema_violation)

Triggered by missing repository link or description length < 50 words.

```json
{
  "trace_id": "trace-fail-schema-001",
  "submission_id": "sub-3f1a2b3c4d5e-6f7a8b9c",
  "evaluation_result": "FAIL",
  "failure_type": "schema_violation",
  "selected_task_id": "T-GOV-F01",
  "selection_reason": "FAIL(schema_violation) -> failure_tasks['schema_violation'][0] = T-GOV-F01",
  "source": "task_graph"
}
```

## 3. FAIL Case (incomplete)

Triggered by missing implementation proof (README, tests) or file count < 3.

```json
{
  "trace_id": "trace-fail-incomplete-001",
  "submission_id": "sub-9e8d7c6b5a4f-3e2d1c0b",
  "evaluation_result": "FAIL",
  "failure_type": "incomplete",
  "selected_task_id": "T-GOV-F01",
  "selection_reason": "FAIL(incomplete) -> failure_tasks['incomplete'][0] = T-GOV-F01",
  "source": "task_graph"
}
```

## 4. FAIL Case (incorrect_logic)

Triggered by low delivery ratio or low effort (word count < 80).

```json
{
  "trace_id": "trace-fail-logic-001",
  "submission_id": "sub-1a2b3c4d5e6f-7g8h9i0j",
  "evaluation_result": "FAIL",
  "failure_type": "incorrect_logic",
  "selected_task_id": "T-GOV-F02",
  "selection_reason": "FAIL(incorrect_logic) -> failure_tasks['incorrect_logic'][0] = T-GOV-F02",
  "source": "task_graph"
}
```

## 5. FAIL Case (integration_fail)

Triggered by repository fetch errors (e.g., private repo or network timeout).

```json
{
  "trace_id": "trace-fail-integration-001",
  "submission_id": "sub-0k9j8i7h6g5f-4e3d2c1b",
  "evaluation_result": "FAIL",
  "failure_type": "integration_fail",
  "selected_task_id": "T-SYS-F00",
  "selection_reason": "FAIL(integration_fail) -> failure_tasks['integration_fail'][0] = T-SYS-F00",
  "source": "task_graph"
}
```

---

## Output Contract Rules

1. **Exact Fields**: The output must contain exactly 7 fields.
2. **Fixed Names**: Field names are constant and case-sensitive.
3. **No Drift**: `trace_id` is preserved from input; `submission_id` is a pure function of input.
4. **Binary Result**: `evaluation_result` is always "PASS" or "FAIL".
5. **Valid Enums**: `failure_type` must be one of the 4 defined types if result is FAIL.