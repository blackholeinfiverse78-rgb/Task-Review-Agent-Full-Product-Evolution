# Lineage Proof

- **Version**: 1.0.0
- **Status**: PROVEN / CORE-LOCKED
- **Unified Key**: `trace_id` (mandatory, preserved, never mutated or regenerated)

---

## 1. Lineage Flow Diagram
This flow proves the trace lifecycle for a single submission:

```
[1. REQUEST] Ingested task payload with trace_id
      |
      v
[2. REVIEW] Rule evaluation execution (Sri Satya core)
      |
      v
[3. ESCALATION] staged in storage/escalations/ (if confidence < 0.98)
      |
      v
[4. APPROVAL] Governed envelope mutation appended to SQLite event log
      |
      v
[5. ASSIGNMENT] Next-task selected from task graph
      |
      v
[6. EXPORT] Propagated to Saarthi/Niyantran ledger logs
```

---

## 2. Traced Lineage Evidence
Below is the structural mapping of evidence records for a single transaction (Trace: `trace-lineage-100-xyz`).

### 2.1 Request Ingest (Niyantran Intake Receipt)
- **Source**: `/api/v1/production/niyantran/submit`
- **Output Record**:
  ```json
  {
    "trace_id": "trace-lineage-100-xyz",
    "submission_id": "sub-lineage-9999",
    "review_state": "PENDING_REVIEW",
    "status": "QUEUED"
  }
  ```

### 2.2 Review Evaluation (Rule Output)
- **Source**: `RuleEngine.evaluate()`
- **Output Record**:
  ```json
  {
    "evaluation_result": "FAIL",
    "failure_type": "incomplete",
    "pac": { "proof": 0, "architecture": 1, "code": 1 },
    "rubric": { "has_proof": 0, "has_architecture": 1, "has_code": 1, "has_alignment": 1, "has_authenticity": 1, "has_effort": 0 }
  }
  ```

### 2.3 Escalation Staging Case
- **Source**: `storage/escalations/esc-lineage-9999.json`
- **Output Record**:
  ```json
  {
    "case_id": "esc-lineage-9999",
    "trace_id": "trace-lineage-100-xyz",
    "confidence": 0.5833,
    "status": "pending",
    "reasons": ["low_confidence", "no_proof"]
  }
  ```

### 2.4 Human Approval (Gov-OS Envelope Mutation)
- **Source**: `storage/canonical_db.sqlite` (`events` table)
- **Output Record**:
  ```json
  {
    "sequence": 5,
    "event_id": "evt-lineage-101",
    "event_hash": "2c9b4e6d7f8a9b0c...",
    "parent_event_hash": "8d4eeea3...",
    "trace_id": "trace-lineage-100-xyz",
    "event_type": "review_history",
    "actor": "Akash",
    "authorized_by": "Akash",
    "payload": {
      "review_id": "rev-lineage-9999",
      "submission_id": "sub-lineage-9999",
      "status": "APPROVED",
      "score": 95.0,
      "reviewed_by": "Akash",
      "reviewed_at": "2026-06-12T08:40:00Z"
    }
  }
  ```

### 2.5 Next-Task Assignment
- **Source**: `task_selection_engine.select_next_task()`
- **Output Record**:
  ```json
  {
    "next_task_id": "NT-ADV-I-001",
    "title": "Advanced Microservices Implementation",
    "task_type": "advancement",
    "selection_reason": "score=9.5/10 -> approved | difficulty=intermediate | graph_key=('approved', 'intermediate')"
  }
  ```

### 2.6 Downstream Ledger Export
- **Source**: `storage/saarthi_visibility.jsonl`
- **Output Record**:
  ```json
  {
    "trace_id": "trace-lineage-100-xyz",
    "event_type": "downstream_visibility",
    "source": "Parikshak",
    "destination": "Saarthi",
    "payload": {
      "submission_id": "sub-lineage-9999",
      "decision": "APPROVED",
      "score": 95.0,
      "assigned_task": "NT-ADV-I-001"
    },
    "timestamp": "2026-06-12T08:41:00Z"
  }
  ```

---

## 3. Proof of Reconstruction
We prove that given only the trace logs, the exact system state, decision process, and outputs can be perfectly reconstructed. The unified `trace_id` links the in-memory queue, SQLite ledger records, and downstream exports together. This makes auditing 100% deterministic.
