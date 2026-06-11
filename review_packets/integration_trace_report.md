# Parikshak Integration Trace Report

This document records the end-to-end trace lineage for a single task submission propagating through the ecosystem layers.

## Trace Lineage Metadata
* **Ecosystem Trace ID**: `trace-ecosystem-proof-4cd84c2819f5`
* **Associated Submission ID**: `sub-trace-ec`
* **Authorized Sign-off Governor**: `Akash`

## Sequence Map and Timestamps
1. **Intake Ingested**: Ingested by `EcosystemIntegrator` at `2026-06-11T06:13:04.544345Z`
2. **Escalation Triggered**: Low confidence score (`0.25`) triggered escalation to human review queue.
3. **Governor Override Signature**: Governance mutation sign-off signed by authorized actor `Akash`.
4. **Canonical Event Ledger Commit**: Transaction appended as Event Sequence `2` with Hash `b3568e082b61bf47a3bc6be4dc240548b9b9e8b9bb622aabd972fdec663747ec`.
5. **Downstream Dispatch**:
   - **Saarthi Visibility Ledger**: Written to `saarthi_visibility.jsonl`
   - **Niyantran Assignment Ledger**: Written to `niyantran_assignments.jsonl`

*Verified: 2026-06-11T06:13:04.544345Z UTC*
