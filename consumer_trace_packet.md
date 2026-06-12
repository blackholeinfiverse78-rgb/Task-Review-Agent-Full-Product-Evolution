# Consumer Trace Packet

- **Version**: 1.0.0
- **Trace ID**: `trace-lineage-100-xyz`
- **Output File Representation**: A unified trace packet representation generated for audits.

---

## 1. Unified Trace JSON Bundle
The following JSON block represents the complete, self-contained audit packet for transaction `trace-lineage-100-xyz`. Any external system can parse this single packet to verify compliance.

```json
{
  "trace_id": "trace-lineage-100-xyz",
  "schema_version": "v1.0",
  "lifecycle_stages": {
    "ingestion": {
      "timestamp": "2026-06-12T08:30:00Z",
      "payload": {
        "task_id": "T-GOV-001",
        "task_title": "REST API with Layered Architecture",
        "task_description": "Objective: Build a production-ready REST API service. Requirements: Implement service, controller, and data layers.",
        "submitted_by": "Ishan Shirode",
        "repository_url": "https://github.com/blackholeinfiverse78-rgb/task-repo",
        "module_id": "task-review-agent"
      },
      "receipt": {
        "submission_id": "sub-lineage-9999",
        "review_state": "PENDING_REVIEW",
        "status": "QUEUED"
      }
    },
    "evaluation_core": {
      "timestamp": "2026-06-12T08:30:02Z",
      "rule_engine_outputs": {
        "evaluation_result": "FAIL",
        "failure_type": "incomplete",
        "reasons": ["missing_tests"],
        "signals": {
          "file_count": 5,
          "readme_present": false,
          "tests_found": []
        }
      },
      "confidence_calculation": {
        "proof": 0.0,
        "architecture": 1.0,
        "code": 1.0,
        "rubric_completeness": 0.3333,
        "confidence_score": 0.5833,
        "requires_escalation": true,
        "escalation_reasons": ["low_confidence", "no_proof"]
      }
    },
    "escalation_staging": {
      "timestamp": "2026-06-12T08:30:05Z",
      "case_id": "esc-lineage-9999",
      "status": "pending",
      "assigned_reviewer": null
    },
    "governance_approval": {
      "timestamp": "2026-06-12T08:40:00Z",
      "governor": "Akash",
      "role": "operator",
      "notes": "Manually verified repository. The code layers are correct and tests were written but not matching name conventions. Approving.",
      "override_decision": {
        "evaluation_result": "PASS",
        "decision": "APPROVED",
        "score": 95.0
      },
      "ledger_entry": {
        "sequence": 5,
        "event_id": "evt-lineage-101",
        "event_hash": "2c9b4e6d7f8a9b0c6d5e...",
        "parent_event_hash": "8d4eeea32de1ed3e12d0..."
      }
    },
    "assignment_routing": {
      "timestamp": "2026-06-12T08:40:05Z",
      "assigned_task_id": "NT-ADV-I-001",
      "task_title": "Advanced Microservices Implementation",
      "difficulty": "advanced",
      "selection_reason": "score=9.5/10 -> approved | difficulty=intermediate | graph_key=('approved', 'intermediate')"
    },
    "downstream_export": {
      "timestamp": "2026-06-12T08:41:00Z",
      "saarthi_ledger": {
        "status": "PROPAGATED",
        "destination": "Saarthi",
        "timestamp": "2026-06-12T08:41:00Z"
      },
      "niyantran_ledger": {
        "status": "PROPAGATED",
        "destination": "Niyantran",
        "assignment_id": "assign-trace-li",
        "timestamp": "2026-06-12T08:41:00Z"
      }
    }
  }
}
```
