# CAPABILITY CONSUMPTION PACKET

This document outlines how external clients (e.g. HackaVerse, Niyantran) consume Parikshak as a reusable capability provider.

---

## 1. API Contract Specifications

### 1.1 REST Endpoint: POST `/parikshak/review`
Evaluates an engineering task submission and provides a structured evaluation response.

- **Request Headers**:
  - `Content-Type`: `application/json`
- **Response Codes**:
  - `200 OK`: Request parsed and evaluated successfully. (Payload returns evaluation status PASS, PARTIAL, or FAIL).
  - `400 Bad Request`: Payload missing or invalid JSON format.
  - `422 Unprocessable Entity`: Validation failure against Pydantic schema constraints.
  - `500 Internal Server Error`: Critical backend execution failure.

---

## 2. API JSON Schemas

### 2.1 Request Schema (`request_schema.json`)
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "ReviewRequest",
  "type": "object",
  "properties": {
    "mode": {"type": "string", "enum": ["task_review"]},
    "title": {"type": "string", "minLength": 5, "maxLength": 100},
    "description": {"type": "string", "minLength": 10, "maxLength": 2000},
    "submitted_by": {"type": "string", "minLength": 2, "maxLength": 50},
    "submission": {"type": "string"},
    "repo_url": {"type": "string", "format": "uri"},
    "trace_id": {"type": "string", "minLength": 8}
  },
  "required": ["title", "description", "submitted_by", "trace_id"]
}
```

### 2.2 Response Schema (`response_schema.json`)
Standardized evaluation outcome payload:
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "ReviewResponse",
  "type": "object",
  "properties": {
    "status": {"type": "string", "enum": ["PASS", "PARTIAL", "FAIL"]},
    "review": {"type": "string"},
    "score": {"type": "integer", "minimum": 0, "maximum": 100},
    "next_task": {"type": "string"},
    "trace_id": {"type": "string"}
  },
  "required": ["status", "review", "score", "next_task", "trace_id"]
}
```

### 2.3 Error Schema (`error_schema.json`)
Structured error response for validation and server-side errors:
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "ErrorResponse",
  "type": "object",
  "properties": {
    "detail": {"type": "string"},
    "error_code": {"type": "string"},
    "timestamp": {"type": "string", "format": "date-time"}
  },
  "required": ["detail"]
}
```

---

## 3. Versioning & Resilience Policies

### 3.1 Versioning Strategy
- **Current Version**: `v1.1.0`
- **URI Routing**: Updates introducing breaking structural changes will utilize `/api/v2/parikshak/review`.
- **Payload Guarantee**: Minor patch updates (v1.x) will never deprecate, rename, or remove response JSON fields.

### 3.2 Timeout Behavior
- Deterministic checks generally complete in `< 2 ms`.
- The system enforces a strict gateway timeout of **`1500 ms`** per API invocation. Requests exceeding this limit receive a `504 Gateway Timeout` with error code `TIMEOUT_EXPIRED`.

### 3.3 Retry Behavior
- Downstream clients should implement **Exponential Backoff** retries (Base delay: 1s, Multiplier: 2x, Max delay: 30s, Max attempts: 5) for 5xx server errors.
- Client validation errors (4xx) should not be retried without payload correction.

---

## 4. Consumer Integration Examples

### 4.1 HackaVerse Style Consumer (Node.js/TypeScript)
```typescript
import axios from 'axios';

interface ReviewResponse {
  status: 'PASS' | 'PARTIAL' | 'FAIL';
  review: string;
  score: number;
  next_task: string;
  trace_id: string;
}

async function requestReview(repoUrl: string, developer: string, traceId: string): Promise<ReviewResponse> {
  const payload = {
    mode: "task_review",
    title: "Implement Authentication Module",
    description: "Build a production-ready authentication component using JWT and bcrypt hashing.",
    submitted_by: developer,
    repo_url: repoUrl,
    trace_id: traceId
  };

  const response = await axios.post<ReviewResponse>('http://localhost:8000/parikshak/review', payload, {
    timeout: 1500
  });
  return response.data;
}
```

### 4.2 Niyantran Style Consumer (Python/FastAPI)
```python
import requests
import time

def dispatch_evaluation(task_data: dict, max_retries=3) -> dict:
    url = "http://localhost:8000/parikshak/review"
    headers = {"Content-Type": "application/json"}
    
    for attempt in range(max_retries):
        try:
            resp = requests.post(url, json=task_data, headers=headers, timeout=1.5)
            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code in (500, 503):
                time.sleep(2 ** attempt)  # exponential backoff
        except requests.Timeout:
            print("Request timed out. Retrying...")
    raise RuntimeError("Failed to obtain evaluation from Parikshak")
```

### 4.3 Generic External Consumer (cURL CLI)
```bash
curl -X POST http://localhost:8000/parikshak/review \
     -H "Content-Type: application/json" \
     -d '{
       "title": "Build user auth schema",
       "description": "Create SQLite database schema with hashed passwords.",
       "submitted_by": "Akash Dev",
       "trace_id": "trace-generic-client-001"
     }'
```
