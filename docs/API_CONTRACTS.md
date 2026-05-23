# 📡 API Contracts Reference (v6.0 - Gov-OS Hardened)

> Base URL: `http://localhost:8000/api/v1`  
> Interactive Docs: `http://localhost:8000/docs`

---

## 1. Niyantran Production Endpoints

### `POST /production/niyantran/submit`
Evaluates a task submission and places it in the human review queue.

**Request** `application/json`
```json
{
  "trace_id": "trace-12345",
  "task_id": "T-GOV-001",
  "task_title": "Implement triggers",
  "task_description": "Add SQLite update/delete prevent triggers to events log.",
  "submitted_by": "cand-001",
  "repository_url": "https://github.com/bhiv/parikshak"
}
```

**Response** `200 OK`
```json
{
  "trace_id": "trace-12345",
  "submission_id": "sub-md5hash",
  "evaluation_result": "PASS",
  "failure_type": null,
  "selected_task_id": "T-GOV-002",
  "selection_reason": "PASS -> next_tasks[0] = T-GOV-002",
  "source": "task_graph"
}
```

---

## 2. Gov-OS Hardened Endpoints (`/api/v1/gov-os`)

### `POST /gov-os/mutate`
Appends a validated, human-signed governance envelope to the event journal.

**Request** `application/json`
```json
{
  "envelope": {
    "trace_id": "trace-test-12345",
    "schema_version": "v1.0",
    "actor": "operator-1",
    "actor_role": "operator",
    "event_type": "candidate_profiles",
    "payload": {
      "candidate_id": "cand-001",
      "name": "Nikhil",
      "github_handle": "nikhil-dev",
      "skills": ["python", "sqlite"],
      "performance_score": 95.5
    },
    "authorized_by": "Akash",
    "lineage_reference": "lineage-ref-abc",
    "approval_token": "token-123",
    "payload_checksum": "sha256-hash-of-canonical-payload",
    "parent_event_hash": "sha256-hash-of-parent-event"
  },
  "executor_actor": "operator-1"
}
```

**Response** `200 OK`
```json
{
  "status": "COMMITTED",
  "event": {
    "sequence": 1,
    "event_id": "evt-xxxxx",
    "event_type": "candidate_profiles",
    "event_hash": "...",
    "parent_event_hash": "...",
    "timestamp": "2026-05-23T01:20:30Z"
  },
  "snapshot": "storage/backups/snapshot_seq_1_timestamp.json"
}
```

### `GET /gov-os/export`
Exports the current system state, signed by Parikshak.
**Response** `200 OK`
```json
{
  "system_signature": "sha256-signature-hash",
  "exported_at": "2026-05-23T01:20:30Z",
  "state": {
    "candidate_profiles": {...},
    "review_history": {...}
  }
}
```

### `POST /gov-os/scaffold`
Receives raw GPT scaffolding payload, performs schema verification, and packages it in an `AWAITING_HUMAN_APPROVAL` governance envelope.
**Request** `application/json`
```json
{
  "payload": {
    "candidate_id": "cand-gpt-99",
    "name": "Scaffold Candidate"
  },
  "event_type": "candidate_profiles",
  "trace_id": "trace-gpt-123",
  "actor": "gpt"
}
```

**Response** `200 OK`
```json
{
  "status": "AWAITING_HUMAN_APPROVAL",
  "bridge_validation": "PASSED",
  "envelope": {
    "trace_id": "trace-gpt-123",
    "schema_version": "v1.0",
    "actor": "gpt",
    "event_type": "candidate_profiles",
    "payload": {...},
    "authorized_by": null
  }
}
```

### `POST /gov-os/rollback`
Rollbacks the database state to a target sequence number anchor.
**Request** `application/json`
```json
{
  "target_seq": 1
}
```

### `POST /gov-os/reconstruct`
Reconstructs the SQLite database from a JSONL audit journal.
**Request** `application/json`
```json
{
  "jsonl_path": "storage/audit_logs/audit_2026-05-23.jsonl",
  "new_db_path": "storage/reconstructed_db.sqlite"
}
```

### `POST /gov-os/integrate`
Propagates a mutation to the external ecosystem adapters.
**Request** `application/json`
```json
{
  "task_payload": {...},
  "trace_id": "trace-integrated-123"
}
```
