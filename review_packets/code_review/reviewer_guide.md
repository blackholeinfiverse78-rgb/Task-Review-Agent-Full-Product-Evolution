# Parikshak Operational Reviewer Guide

This guide is designed for systems operators and compliance officers to verify the production convergence and integration compliance of the Parikshak pipeline.

---

## 1. Automated Validation Executions
Reviewers can trigger the automated verification tests using the following commands:

### A. Run Core Security & Hardening Tests
Verifies negative security gates, JWT authorization token verification, dependency pinning, and DB event-sourcing replay recovery:
```bash
python -m unittest tests/security_dependency_hardening_test.py
```

### B. Run API & Review Pipeline Integration
Verifies the intake post endpoint, queuing state machine, and automatic assignment creations under valid auth:
```bash
python -m pytest tests/test_candidate_review_pipeline.py
```

### C. Run Master Operational Validation Harness
Re-executes performance benchmarks, adversarial input checks, and logs 22 compliance reports:
```bash
python tests/run_operational_validation.py
```

### D. Run 7-Phase Production Readiness Gates
Verifies the complete compliance checklist:
```bash
python tests/production_readiness_test.py
```

---

## 2. Local Manual Verification Steps

### Step 1: Start the Backend Server
Initialize the FastAPI server locally:
```bash
python main.py
```

### Step 2: Extract a Valid Governor Token for Testing
Use this Python snippet to output a Bearer Token for manual CURL queries:
```python
from security.middleware import SecurityConfig, UserRole
token = SecurityConfig.create_access_token({"sub": "Akash", "role": UserRole.GOVERNOR.value})
print("Bearer Token:", token)
```

### Step 3: Trigger a Manual Ingestion
Send a POST request with the authentication header:
```bash
curl -X POST http://127.0.0.1:8000/api/v1/production/intake \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d "{ ... }"
```

### Step 4: Verify Event Emitters in Sqlite DB
Open the DB and verify sequence lineage hashes are recorded properly in Gov-OS journal table:
```sql
SELECT sequence, event_type, event_hash, parent_event_hash FROM events ORDER BY sequence;
```
