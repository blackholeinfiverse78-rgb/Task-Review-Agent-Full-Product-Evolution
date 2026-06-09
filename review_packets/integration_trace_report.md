# Parikshak Integration Trace Report

This document records the payloads and metadata captured during the live end-to-end integration chain.

## 1. Trace Overview
- **Trace ID**: `trace-ecosystem-proof-999`
- **Evaluation Decision**: `APPROVED (PASS)`
- **Next Task Routing**: `T-GOV-003`

## 2. API Request Payload (Submission Intake)
```json
{
  "task_id": "T-GOV-002",
  "task_title": "Implement Niyantran Connection Proof",
  "task_description": "Verify tasks are correctly propagated to Niyantran and Saarthi loggers.",
  "submitted_by": "Akash",
  "github_repo_link": "https://github.com/blackholeinfiverse78-rgb/test-repo"
}
```

## 3. Human Approval Envelope (Governance Gate)
```json
{'trace_id': 'trace-ecosystem-proof-999', 'schema_version': 'v1.0', 'actor': 'Akash', 'actor_role': 'operator', 'timestamp': '2026-06-09T06:55:36.879313Z', 'lineage_reference': 'genesis', 'event_type': 'review_history', 'payload': {'review_id': 'rev-trace-ec', 'submission_id': 'sub-trace-ec', 'trace_id': 'trace-ecosystem-proof-999', 'evaluation_result': 'PASS', 'failure_type': None, 'decision': 'APPROVED', 'failure_reasons': [], 'improvement_hints': [], 'analysis': {'technical_quality': 95, 'clarity': 95, 'discipline_signals': 95}, 'reviewed_by': 'Akash', 'reviewed_at': '2026-06-09T06:55:36.879313Z', 'evaluation_time_ms': 15, 'missing_features': [], 'evaluation_summary': 'Passed evaluation requirements.', 'selected_task_id': 'T-GOV-003', 'selection_reason': 'Advancement to next evolutionary stage', 'review_state': 'APPROVED', 'score': 95, 'readiness_percent': 95, 'status': 'pass', 'candidate_name': 'Akash', 'task_title': 'Implement Niyantran Connection Proof'}, 'authorized_by': 'Akash', 'approval_token': 'token-default-123', 'payload_checksum': 'e61b8dbf7dc17b5f92013af76353474f695d1b3265479a2ffc134eecfdd67634', 'checksum': 'e61b8dbf7dc17b5f92013af76353474f695d1b3265479a2ffc134eecfdd67634', 'parent_event_hash': 'ee10244e2f116f29fa9ff68fd97bebc84a866aca2cedfd8f3a35f5934d5d271a'}
```

## 4. Export State
```json
{'status': 'PROPAGATED', 'commit_details': {'status': 'SUCCESS', 'sequence': 2, 'event_id': 'evt-a31bdc0a448c', 'event_hash': '1d23e14257eda367d4dc02a85a2499860c0439eac31f895df6e31041e0b60313', 'snapshot': 'storage/backups\\snapshot_seq_2_20260609_065536.json'}, 'saarthi_ledger': 'C:\\Users\\black\\Downloads\\Live Task Review Agent - 2\\Live Task Review Agent - 2\\scratch\\temp_p3_saarthi.jsonl', 'niyantran_ledger': 'C:\\Users\\black\\Downloads\\Live Task Review Agent - 2\\Live Task Review Agent - 2\\scratch\\temp_p3_niyantran.jsonl'}
```
