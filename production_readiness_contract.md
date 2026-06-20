# BHIV Production Readiness Contract

- **Version**: 1.0.0
- **Status**: FROZEN / MANDATORY GOVERNANCE
- **Scope**: Independent Production Readiness Certification Service (Parikshak Phase IV)

This contract defines the mandatory production readiness dimensions, required evidence, and pass/fail/unknown thresholds that determine if a system is ready to participate inside the **TANTRA** ecosystem.

---

## Mandatory Production Dimensions

| Dimension | Required Evidence (Artifact Files) | Pass Criteria | Failure Criteria | Unknown State behavior | Weight |
| :--- | :--- | :--- | :--- | :--- | :---: |
| **1. Runtime** | `evidence_bundle.json`, `handover_bundle.json` | `handover_status == "COMPLETE"` and trace ID matches correctly. | `handover_status == "FAILED"` or explicit runtime crash logged. | Treated as missing context; falls to **UNKNOWN**; weight is skipped or penalizes score depending on model. | 10% |
| **2. Observability** | `observability_telemetry.json` or `replay_logs` metrics | Contains active metrics definitions and OpenTelemetry span propagation markers. | Observability explicitly disabled or logs show telemetry initiation failure. | Telemetry records absent; defaults to **UNKNOWN**. | 10% |
| **3. Replayability** | `replay_bundle.json`, `replay_verification.json` | `replay_status == "SUCCESS"` and Ansh verified status is `VERIFIED`. | `replay_status == "FAILURE"` or replay verification mismatch. | Missing replay verification logs; defaults to **UNKNOWN**. | 10% |
| **4. Governance** | `governance_record.json`, `validation_decision.json`, `constitutional_history.json` | Governance validated, decision is `APPROVED`, no active violations in history. | Decision is `REJECTED`, invalid signature authority, or active block. | Missing governance details; defaults to **UNKNOWN**. | 10% |
| **5. Provenance** | `lineage_bundle.json`, `provenance_chain.json` (or `lineage_chain.json`), `lineage_registration.json` | Lineage chain is registered, intact, and links correctly to genesis. | Chain gaps detected or invalid hash links between parent nodes. | Missing lineage data; defaults to **UNKNOWN**. | 10% |
| **6. Security** | `security_metadata.json` | 0 critical/high vulnerabilities and valid cryptographic payload hashes. | Security checks fail, critical vulnerabilities found, or signature corrupt. | Security scan absent; defaults to **UNKNOWN**. | 10% |
| **7. Versioning** | `schema_metadata.json`, `registration_reference.json` | Schema version matches registry, system version is semver compliant. | Schema drift detected or version is incompatible with the target layer. | Versioning info missing; defaults to **UNKNOWN**. | 5% |
| **8. Recovery** | `recovery_metadata.json` or snapshot logs | Active rollback anchors present and recovery test status is successful. | No rollback checkpoints registered or recovery mechanism failed. | Recovery data missing; defaults to **UNKNOWN**. | 5% |
| **9. Human Approval** | `validation_decision.json` | Signed by an authorized human governor (e.g. `Akash`, `Ansh`, `Saarthi_Governor`). | Signed by an unauthorized actor, or missing signature block. | Decision block missing; defaults to **UNKNOWN**. | 10% |
| **10. Layer Placement** | `ecosystem_placement.json` | Declared placement matches TANTRA framework topology. | Layer placement is invalid or undeclared. | Placement info missing; defaults to **UNKNOWN**. | 5% |
| **11. Dependency Integrity** | `dependency_graph.json` | Complete dependency list declared, 0 circular dependency loops. | Circular loops found or blacklisted package imported. | Graph missing; defaults to **UNKNOWN**. | 5% |
| **12. Ecosystem Participation**| `consumer_registration.json`, `architectural_participation.json` | System registered in TMS and actively mapped to upstream/downstream nodes. | System unregistered or disconnected from TMS topology. | TMS participation missing; defaults to **UNKNOWN**. | 10% |

---

## Evaluation Metrics

### Scoring & Weighting
*   **Total Weight**: 100%
*   **PASS**: Receives the full weight percentage.
*   **WARNING**: Receives 50% of the weight percentage.
*   **FAIL**: Receives 0% of the weight percentage.
*   **UNKNOWN**: Receives 0% of the weight percentage (treated as untested/unverified).

### Decision Rules
*   **READY**: Score $\ge 90\%$, no **FAIL** in any dimension, and no **UNKNOWN** in critical dimensions (Runtime, Replayability, Governance, Security, Human Approval).
*   **READY WITH OBSERVATIONS**: Score $\ge 75\%$ and $< 90\%$, no critical **FAIL**, but may have warnings or non-critical unknowns.
*   **NEEDS REVIEW**: Score $\ge 50\%$ and $< 75\%$, or some critical dimensions are **UNKNOWN**.
*   **NOT PRODUCTION READY**: Score $< 50\%$ or any dimension has a status of **FAIL**.
*   **UNKNOWN**: If all or critical dimensions are **UNKNOWN** due to missing evidence.
