# Parikshak Integration Trace Report

This document records the end-to-end trace lineage for a single task submission propagating through the ecosystem layers.

## Trace Lineage Metadata
* **Ecosystem Trace ID**: `trace-ecosystem-proof-9783fc8edc93`
* **Associated Submission ID**: `sub-trace-ec`
* **Authorized Sign-off Governor**: `Akash`

## Sequence Map and Timestamps
1. **Intake Ingested**: Ingested by `EcosystemIntegrator` at `2026-06-30T10:38:25.841068Z`
2. **Escalation Triggered**: Low confidence score (`0.25`) triggered escalation to human review queue.
3. **Governor Override Signature**: Governance mutation sign-off signed by authorized actor `Akash`.
4. **Canonical Event Ledger Commit**: Transaction appended as Event Sequence `2` with Hash `8e57fe03974ff28239df21148db82dffe3c289a365956c3d5e8d90a658965778`.
5. **Downstream Dispatch**:
   - **Saarthi Visibility Ledger**: Written to `saarthi_visibility.jsonl`
   - **Niyantran Assignment Ledger**: Written to `niyantran_assignments.jsonl`

*Verified: 2026-06-30T10:38:25.841129Z UTC*
