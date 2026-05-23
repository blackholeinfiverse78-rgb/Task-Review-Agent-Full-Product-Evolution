# 📄 Gov-OS Core Contracts Specification

This document specifies the validation schemas and Pydantic models governing all state transitions in Parikshak.

---

## 1. Governance Envelope Contract

All events appended to the ledger must conform to the following schema:

| Field | Type | Description |
|---|---|---|
| `trace_id` | string | Minimum 8 characters trace correlation identifier. |
| `schema_version` | string | Version of the event payload schema (e.g. `v1.0`). |
| `actor` | string | The operator or agent committing the change. |
| `actor_role` | string | Role of the actor (e.g., `operator`, `auditor`). |
| `timestamp` | string | RFC3339/ISO UTC formatted timestamp string. |
| `lineage_reference` | string | Lineage trace or parent process hash. |
| `approval_token` | string | Governor sign-off token. |
| `payload_checksum` | string | SHA-256 hash of the canonical JSON serialized payload. |
| `parent_event_hash` | string | SHA-256 hash of the immediate parent event in the journal. |
| `event_type` | string | Target table/schema name. |
| `payload` | dict | Entity data matching target schema. |
| `authorized_by` | string | Authorizing governor (must be a human operator). |

---

## 2. Core Database Schema Registry (9 Entities)

The database registry defines schemas for the following entities, frozen at runtime to prevent drift:

### 2.1 Candidate Profile
```json
{
  "candidate_id": "string",
  "name": "string",
  "github_handle": "string",
  "skills": ["string"],
  "performance_score": "float"
}
```

### 2.2 Task Lineage
```json
{
  "task_id": "string",
  "parent_task_id": "string (optional)",
  "root_task_id": "string",
  "generated_at": "string"
}
```

### 2.3 Review History
```json
{
  "review_id": "string",
  "submission_id": "string",
  "status": "string (APPROVED | REJECTED | MODIFIED)",
  "score": "float",
  "reviewed_by": "string",
  "reviewed_at": "string"
}
```

### 2.4 Assignment History
```json
{
  "assignment_id": "string",
  "candidate_id": "string",
  "task_id": "string",
  "assigned_at": "string",
  "due_at": "string"
}
```

### 2.5 Reasoning Artifacts
```json
{
  "artifact_id": "string",
  "task_id": "string",
  "reasoning_steps": ["string"],
  "conclusion": "string"
}
```

### 2.6 Ecosystem Dependency Context
```json
{
  "context_id": "string",
  "system_name": "string",
  "dependencies": ["string"]
}
```

### 2.7 Product Mapping
```json
{
  "mapping_id": "string",
  "product_name": "string",
  "tasks": ["string"]
}
```

### 2.8 Strategic Notes
```json
{
  "note_id": "string",
  "author": "string",
  "content": "string",
  "created_at": "string"
}
```

### 2.9 Learning Signals
```json
{
  "signal_id": "string",
  "source": "string",
  "value": "float"
}
```
