# 📡 API Contracts Reference (v6.0)

> Base URL: `http://localhost:8000/api/v1`  
> Interactive Docs: `http://localhost:8000/docs`

---

## 1. Production (Niyantran) Endpoint

### `POST /production/niyantran/submit`

Primary deterministic entry point for task evaluation and selection.

**Request** — `application/json`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `trace_id` | string | ✅ | Minimum 8 characters. Must come from Niyantran. |
| `task_id` | string | ✅ | Current task ID from the database. |
| `task_title` | string | ✅ | Title of the submitted task. |
| `task_description`| string | ✅ | Full description for evaluation. |
| `submitted_by` | string | ✅ | Candidate identifier. |
| `repository_url` | string | ✅ | GitHub repository URL. |

**Response** `200 OK` (Strict 7-field Contract)

```json
{
  "trace_id":          "trace-a3f2c1d48b9e4f2a",
  "submission_id":     "sub-eb2e07e7c652-d42768ed",
  "evaluation_result": "PASS",
  "failure_type":      null,
  "selected_task_id":  "T-GOV-002",
  "selection_reason":  "PASS -> next_tasks[0] = T-GOV-002",
  "source":            "task_graph"
}
```

**Constraints**:
- **Deterministic**: Same input + `trace_id` → Same output.
- **Contract Enforcement**: Extra fields are stripped; missing fields trigger `CONTRACT_VIOLATION`.

---

## 2. Status & Health

### `GET /production/niyantran/health`
Returns system health and bucket statistics.

### `GET /production/bucket/logs`
Returns the 100 most recent evaluation logs from the deterministic bucket.

---

## 3. Lifecycle (SPA Support)

### `POST /lifecycle/submit`
Legacy/SPA support for multipart submissions. Internally routes to the same deterministic pipeline.

### `GET /lifecycle/review/{id}`
Retrieves review details. Note: Numeric scores are no longer generated; this returns the PASS/FAIL result and failure type.

---

## 4. Error Responses

The system uses standard HTTP status codes combined with deterministic error types.

| Status | Error Context | Cause |
|--------|---------------|-------|
| `400`  | `NIYANTRAN_HARD_REJECT` | Missing or invalid `trace_id`. |
| `404`  | `GRAPH_HARD_REJECT` | `task_id` not found in database. |
| `500`  | `CONTRACT_VIOLATION` | System output failed 7-field validation. |
| `500`  | `MANDALA_HARD_REJECT` | Task selection logic failed internal mapping. |

**Error JSON Format**:
```json
{
  "detail": "Error code: MESSAGE"
}
```
Example:
`{ "detail": "GRAPH_HARD_REJECT: task_id 'INVALID' not in task DB." }`
