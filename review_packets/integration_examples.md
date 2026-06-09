# Integration Examples & Guides

### Python Client Integration Example

```python
import requests
import json

payload = {
    "mode": "task_review",
    "title": "Implement REST API endpoint",
    "description": "Write a secure REST handler with JWT validation using FastAPI.",
    "submitted_by": "Developer Akash",
    "repo_url": "https://github.com/blackholeinfiverse78-rgb/test-repo",
    "trace_id": "trace-python-client-111"
}

response = requests.post("http://localhost:8000/parikshak/review", json=payload)
data = response.json()

print(f"Status: {data['status']}")
print(f"Score: {data['score']}")
print(f"Next Task Assigned: {data['next_task']}")
```

### cURL CLI Example

```bash
curl -X POST http://localhost:8000/parikshak/review \
     -H "Content-Type: application/json" \
     -d '{
       "title": "Build user auth schema",
       "description": "Create SQLite database schema with hashed passwords.",
       "submitted_by": "Akash",
       "trace_id": "trace-curl-client-222"
     }'
```
