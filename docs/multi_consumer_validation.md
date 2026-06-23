# Multi-Consumer Validation

- **Version**: 1.0.0
- **Status**: PROVEN / CORE-LOCKED
- **Endpoint**: `/api/v1/production/niyantran/submit` (or unified Python connection service)

---

## 1. Safety & Uniformity Principles
To survive as a long-term ecosystem service, Parikshak enforces a strict **No-Fork Policy**:
- **Same API Route**: All external clients route task submissions through the exact same intake controller.
- **No Consumer-Specific Logic**: There is no `if consumer == "HackaVerse"` logic in the engine. All routing, grading, and validations apply the same binary rules and graph traversal keys.
- **Deterministic Separation**: Consumer payloads are separated strictly by metadata keys (`trace_id`, `submitted_by`) rather than execution pathways.

---

## 2. Ingestion Validation Results
We have successfully run simulated submissions for multiple consumers. The resulting logs show identical response formats and standard next-task mapping.

### 2.1 Consumer 1: HackaVerse
- **Input Record**: [hackaverse_integration.json](file:///g:/Live%20Task%20Review%20Agent%20-%202/integration_proofs/hackaverse_integration.json)
- **Ingestion Receipt**:
  ```json
  {
    "trace_id": "trace-consumer-000-Hack",
    "submission_id": "sub-9ebc4a5afb04-000-Hack",
    "evaluation_result": "FAIL",
    "failure_type": "schema_violation",
    "selected_task_id": "T-GOV-F01",
    "selection_reason": "FAIL(schema_violation) → failure_tasks['schema_violation'][0] = T-GOV-F01",
    "source": "task_graph"
  }
  ```

### 2.2 Consumer 2: Niyantran
- **Input Record**: [niyantran_integration.json](file:///g:/Live%20Task%20Review%20Agent%20-%202/integration_proofs/niyantran_integration.json)
- **Ingestion Receipt**:
  ```json
  {
    "trace_id": "trace-consumer-001-Niya",
    "submission_id": "sub-f5a6b0c2e391-001-Niya",
    "evaluation_result": "FAIL",
    "failure_type": "schema_violation",
    "selected_task_id": "T-GOV-F01",
    "selection_reason": "FAIL(schema_violation) → failure_tasks['schema_violation'][0] = T-GOV-F01",
    "source": "task_graph"
  }
  ```

### 2.3 Consumer 3: Generic External Consumer
- **Input Record**: [generic_external_consumer_integration.json](file:///g:/Live%20Task%20Review%20Agent%20-%202/integration_proofs/generic_external_consumer_integration.json)
- **Ingestion Receipt**:
  ```json
  {
    "trace_id": "trace-consumer-002-Gene",
    "submission_id": "sub-4b7c8d9e0f1a-002-Gene",
    "evaluation_result": "FAIL",
    "failure_type": "schema_violation",
    "selected_task_id": "T-GOV-F01",
    "selection_reason": "FAIL(schema_violation) → failure_tasks['schema_violation'][0] = T-GOV-F01",
    "source": "task_graph"
  }
  ```

---

## 3. Compatibility Summary
All external clients receive the identical 7-field receipt contract: `trace_id`, `submission_id`, `evaluation_result`, `failure_type`, `selected_task_id`, `selection_reason`, and `source`. The integration remains entirely decoupled from the internal Python libraries or rules, allowing seamless REST-based or database-stream consumption.
