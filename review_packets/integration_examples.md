# Parikshak Integration Examples

This document provides complete, runnable curl and python examples demonstrating integration with the Parikshak API.

### Python Integration Example
```python
import requests

url = "http://localhost:8000/api/v1/production/niyantran/submit"
payload = {
    "task_id": "T-GOV-001",
    "task_title": "REST API Service with Layered Architecture",
    "task_description": "Objective: Build a production-ready REST API service. Requirements: Implement service, controller, and data layers.",
    "submitted_by": "Akash Dev",
    "github_repo_link": "https://github.com/developer/sec-auth",
    "module_id": "task-review-agent",
    "schema_version": "v1.0",
    "trace_id": "trace-integration-example-999"
}

response = requests.post(url, json=payload)
print(response.status_code)
print(response.json())
```

### Curl Submission Example
```bash
curl -X POST http://localhost:8000/api/v1/production/niyantran/submit \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "T-GOV-001",
    "task_title": "REST API Service with Layered Architecture",
    "task_description": "Objective: Build a production-ready REST API service.",
    "submitted_by": "Akash Dev",
    "github_repo_link": "https://github.com/developer/sec-auth",
    "module_id": "task-review-agent",
    "schema_version": "v1.0",
    "trace_id": "trace-integration-example-888"
  }'
```
