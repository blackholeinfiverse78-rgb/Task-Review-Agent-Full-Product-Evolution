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
{'trace_id': 'trace-ecosystem-proof-999', 'schema_version': 'v1.0', 'actor': 'Akash', 'actor_role': 'operator', 'timestamp': '2026-06-15T11:03:32.613331Z', 'lineage_reference': 'genesis', 'event_type': 'review_history', 'payload': {'review_id': 'rev-trace-ec', 'submission_id': 'sub-trace-ec', 'trace_id': 'trace-ecosystem-proof-999', 'evaluation_result': 'PASS', 'failure_type': None, 'decision': 'APPROVED', 'failure_reasons': [], 'improvement_hints': [], 'analysis': {'technical_quality': 95, 'clarity': 95, 'discipline_signals': 95}, 'reviewed_by': 'Akash', 'reviewed_at': '2026-06-15T11:03:32.613331Z', 'evaluation_time_ms': 15, 'missing_features': [], 'evaluation_summary': 'Passed evaluation requirements.', 'selected_task_id': 'T-GOV-003', 'selection_reason': 'Advancement to next evolutionary stage', 'review_state': 'APPROVED', 'score': 95, 'readiness_percent': 95, 'status': 'pass', 'candidate_name': 'Akash', 'task_title': 'Implement Niyantran Connection Proof'}, 'authorized_by': 'Akash', 'approval_token': 'token-default-123', 'payload_checksum': '45496e48e086826b57ee7ed781addcb759f6d63d25645001c5261e6922ba8c01', 'checksum': '45496e48e086826b57ee7ed781addcb759f6d63d25645001c5261e6922ba8c01', 'parent_event_hash': '6b1bf74f2953f7ae94750f5d91087a7a7f3fdd8810cd3561a341f82856eb941f'}
```

## 4. Export State
```json
{'status': 'PROPAGATED', 'commit_details': {'status': 'SUCCESS', 'sequence': 2, 'event_id': 'evt-b0a97401f3d0', 'event_hash': '5989c04cc07cbcb421f8b622a31922a54e7086a239a2a23af2f36dc5dd8c1f5e', 'snapshot': 'storage/backups\\snapshot_seq_2_20260615_110332.json'}, 'saarthi_ledger': 'D:\\ISHAN\\Live Task Review Agent - 2\\Live Task Review Agent - 2\\scratch\\temp_p3_saarthi.jsonl', 'niyantran_ledger': 'D:\\ISHAN\\Live Task Review Agent - 2\\Live Task Review Agent - 2\\scratch\\temp_p3_niyantran.jsonl'}
```
