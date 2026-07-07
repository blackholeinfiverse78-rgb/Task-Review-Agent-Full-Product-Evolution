# Parikshak Runtime Execution Log

Execution logs for trace `trace-ecosystem-proof-2c4faef0c4cf`:

```
[2026-06-09T16:18:00Z] INFO  [niyantran_connection] [NIYANTRAN] Received task T-GOV-002 from Akash
[2026-06-09T16:18:00Z] INFO  [signal_engine] [SIGNAL COLLECTOR] Collecting signals for: Implement Niyantran Connection Proof...
[2026-06-09T16:18:00Z] WARN  [signal_engine] [SIGNAL COLLECTOR] NO SCORING AUTHORITY - Signals only
[2026-06-09T16:18:01Z] INFO  [rule_engine] [RULE ENGINE] Starting deterministic evaluation
[2026-06-09T16:18:01Z] INFO  [rule_engine] [RULE ENGINE] FAIL - incomplete (no code present)
[2026-06-09T16:18:01Z] INFO  [human_in_loop] [ESCALATION] Calculated confidence 0.25 < 0.98. Escalating trace_id=trace-ecosystem-proof-2c4faef0c4cf
[2026-06-09T16:18:02Z] INFO  [human_in_loop] [ESCALATION] Appended record to storage/escalations/escalation_trace-ecosystem-proof-2c4faef0c4cf.json
[2026-06-09T16:18:04Z] INFO  [governed_pipeline] [MUTATION] Structured Entry submitted by Akash. Checking governor authorization...
[2026-06-09T16:18:04Z] INFO  [governed_pipeline] [MUTATION] Actor Akash is in AUTHORIZED_GOVERNORS. Signature valid.
[2026-06-09T16:18:04Z] INFO  [integrity_validator] [SCAN] Verification of SQLite events starting...
[2026-06-09T16:18:04Z] INFO  [integrity_validator] [SCAN] Blockchain SHA-256 integrity check PASSED.
[2026-06-09T16:18:05Z] INFO  [canonical_db] [COMMIT] Event appended. Sequence=2, Hash=456fb720a26582fa58b0c1126e7503438214791eee55a49f593d34af098e7673
[2026-06-09T16:18:05Z] INFO  [backup_manager] [SNAPSHOT] Snapshot created: backup_seq_2.json
[2026-06-09T16:18:05Z] INFO  [ecosystem_integrator] [PROPAGATION] Saarthi Visibility entry added to saarthi_visibility.jsonl
[2026-06-09T16:18:05Z] INFO  [ecosystem_integrator] [PROPAGATION] Niyantran Assignment entry added to niyantran_assignments.jsonl
[2026-06-09T16:18:05Z] INFO  [observability] [EVENT] governed_mutation_committed sequence 2 logged.
```
