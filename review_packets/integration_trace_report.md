# Parikshak Integration Trace Report

This document records the end-to-end trace lineage for a single task submission propagating through the ecosystem layers.

## Trace Lineage Metadata
* **Ecosystem Trace ID**: `trace-ecosystem-proof-305b6c39b9f0`
* **Associated Submission ID**: `sub-trace-ec`
* **Authorized Sign-off Governor**: `Akash`

## Sequence Map and Timestamps
1. **Intake Ingested**: Ingested by `EcosystemIntegrator` at `2026-07-03T08:06:50.983525Z`
2. **Escalation Triggered**: Low confidence score (`0.25`) triggered escalation to human review queue.
3. **Governor Override Signature**: Governance mutation sign-off signed by authorized actor `Akash`.
4. **Canonical Event Ledger Commit**: Transaction appended as Event Sequence `2` with Hash `2014b0983caaec7e7bcfbcf4a4d12600265b61556a0879440ffe4644f968844e`.
5. **Downstream Dispatch**:
   - **Saarthi Visibility Ledger**: Written to `saarthi_visibility.jsonl`
   - **Niyantran Assignment Ledger**: Written to `niyantran_assignments.jsonl`

*Verified: 2026-07-03T08:06:50.983534Z UTC*
