# Parikshak Integration Trace Report

This document records the end-to-end trace lineage for a single task submission propagating through the ecosystem layers.

## Trace Lineage Metadata
* **Ecosystem Trace ID**: `trace-ecosystem-proof-2c4faef0c4cf`
* **Associated Submission ID**: `sub-trace-ec`
* **Authorized Sign-off Governor**: `Akash`

## Sequence Map and Timestamps
1. **Intake Ingested**: Ingested by `EcosystemIntegrator` at `2026-07-07T07:26:48.600151Z`
2. **Escalation Triggered**: Low confidence score (`0.25`) triggered escalation to human review queue.
3. **Governor Override Signature**: Governance mutation sign-off signed by authorized actor `Akash`.
4. **Canonical Event Ledger Commit**: Transaction appended as Event Sequence `2` with Hash `456fb720a26582fa58b0c1126e7503438214791eee55a49f593d34af098e7673`.
5. **Downstream Dispatch**:
   - **Saarthi Visibility Ledger**: Written to `saarthi_visibility.jsonl`
   - **Niyantran Assignment Ledger**: Written to `niyantran_assignments.jsonl`

*Verified: 2026-07-07T07:26:48.600163Z UTC*
