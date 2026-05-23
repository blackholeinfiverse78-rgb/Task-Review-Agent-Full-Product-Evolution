# Testing Documentation — Gov-OS Operational Workflow

This document describes the validation workflow for Parikshak's hardened Gov-OS API routes.

---

## 1. Gov-OS Test Suite

The system includes automated tests executing all safety gates and locks.

### Run Automated Tests
```bash
python -X utf8 scratch/test_operating_system.py
```

---

## 2. Manual Curl Integration Workflows

### Submit a Mutation (Mutate Event Journal)
Appends a validated governance envelope to the log.
```bash
curl -X POST http://localhost:8000/api/v1/gov-os/mutate \
  -H "Content-Type: application/json" \
  -d '{
    "envelope": {
      "trace_id": "trace-manual-101",
      "schema_version": "v1.0",
      "actor": "operator-1",
      "actor_role": "operator",
      "event_type": "candidate_profiles",
      "payload": {
        "candidate_id": "cand-manual-101",
        "name": "Manual Candidate",
        "github_handle": "manual-git",
        "skills": ["c++", "rust"],
        "performance_score": 88.0
      },
      "authorized_by": "Akash",
      "lineage_reference": "lineage-manual",
      "approval_token": "token-manual-abc",
      "payload_checksum": "595914fa6791bf279a4d8c6d7a4de8b209e99238382092109823908129038d12",
      "parent_event_hash": "0000000000000000000000000000000000000000000000000000000000000000"
    },
    "executor_actor": "operator-1"
  }'
```

### Export Signed State for GPT
Retrieves the signed current state of reconstructed read models.
```bash
curl http://localhost:8000/api/v1/gov-os/export
```

### Scaffold GPT Import Awaiting Human Approval
Submits a raw payload that is validated and wrapped into an `AWAITING_HUMAN_APPROVAL` envelope.
```bash
curl -X POST http://localhost:8000/api/v1/gov-os/scaffold \
  -H "Content-Type: application/json" \
  -d '{
    "payload": {
      "candidate_id": "cand-gpt-12",
      "name": "GPT Scaffolded",
      "skills": ["llm"]
    },
    "event_type": "candidate_profiles",
    "trace_id": "trace-gpt-scaffold-12",
    "actor": "gpt"
  }'
```

### Rollback to Checkpoint Anchor
```bash
curl -X POST http://localhost:8000/api/v1/gov-os/rollback \
  -H "Content-Type: application/json" \
  -d '{"target_seq": 1}'
```

---

## 3. Autonomous Release Rejection Verification
To verify that autonomous AI releases are blocked:
1. Attempt to post a mutation using `actor: "AI_Orchestrator_Agent"`.
2. Verify the server rejects the request with HTTP 422/403 and outputs the error `AutonomousReleaseBlocked`.
