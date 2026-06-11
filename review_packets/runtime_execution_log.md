# Parikshak Runtime Execution Log

Execution logs for trace `trace-ecosystem-proof-4cd84c2819f5`:

```
[2026-06-09T16:18:00Z] INFO  [niyantran_connection] [NIYANTRAN] Received task T-GOV-002 from Akash
[2026-06-09T16:18:00Z] INFO  [signal_engine] [SIGNAL COLLECTOR] Collecting signals for: Implement Niyantran Connection Proof...
[2026-06-09T16:18:00Z] WARN  [signal_engine] [SIGNAL COLLECTOR] NO SCORING AUTHORITY - Signals only
[2026-06-09T16:18:01Z] INFO  [rule_engine] [RULE ENGINE] Starting deterministic evaluation
[2026-06-09T16:18:01Z] INFO  [rule_engine] [RULE ENGINE] FAIL - incomplete (no code present)
[2026-06-09T16:18:01Z] INFO  [human_in_loop] [ESCALATION] Calculated confidence 0.25 < 0.98. Escalating trace_id=trace-ecosystem-proof-4cd84c2819f5
[2026-06-09T16:18:02Z] INFO  [human_in_loop] [ESCALATION] Appended record to storage/escalations/escalation_trace-ecosystem-proof-4cd84c2819f5.json
[2026-06-09T16:18:04Z] INFO  [governed_pipeline] [MUTATION] Structured Entry submitted by Akash. Checking governor authorization...
[2026-06-09T16:18:04Z] INFO  [governed_pipeline] [MUTATION] Actor Akash is in AUTHORIZED_GOVERNORS. Signature valid.
[2026-06-09T16:18:04Z] INFO  [integrity_validator] [SCAN] Verification of SQLite events starting...
[2026-06-09T16:18:04Z] INFO  [integrity_validator] [SCAN] Blockchain SHA-256 integrity check PASSED.
[2026-06-09T16:18:05Z] INFO  [canonical_db] [COMMIT] Event appended. Sequence=2, Hash=b3568e082b61bf47a3bc6be4dc240548b9b9e8b9bb622aabd972fdec663747ec
[2026-06-09T16:18:05Z] INFO  [backup_manager] [SNAPSHOT] Snapshot created: backup_seq_2.json
[2026-06-09T16:18:05Z] INFO  [ecosystem_integrator] [PROPAGATION] Saarthi Visibility entry added to saarthi_visibility.jsonl
[2026-06-09T16:18:05Z] INFO  [ecosystem_integrator] [PROPAGATION] Niyantran Assignment entry added to niyantran_assignments.jsonl
[2026-06-09T16:18:05Z] INFO  [observability] [EVENT] governed_mutation_committed sequence 2 logged.
```
