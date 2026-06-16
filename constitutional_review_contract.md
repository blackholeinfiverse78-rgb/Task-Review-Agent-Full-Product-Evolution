# Constitutional Review Contract (Parikshak – TANTRA Readiness Layer)

- **Version**: 1.0.0
- **Status**: FROZEN
- **Context**: Evolving Parikshak into the Constitutional Review Layer for TANTRA.

---

## 1. Purpose
This contract establishes the rules, input schemas, output states, and deterministic decision criteria for verifying the readiness of TANTRA traces. It ensures that any independent reviewer can reconstruct and trust a trace starting only with its `trace_id` and the persisted artifacts.

---

## 2. Inputs
The contract consumes files persisted in `storage/traces/{trace_id}/`. The files are grouped into five logical bundles:

| Bundle Name | Artifact File Name | Source | Key Fields & Validation Rules |
| :--- | :--- | :--- | :--- |
| **Evidence Bundle** | `evidence_bundle.json` | Pratham | `trace_id`, `files` (list of `{path, hash, size}`), `checksum`, `timestamp`. Verify that files exist and their actual SHA-256 hashes match. |
| **Lineage Bundle** | `lineage_bundle.json` | Pratham | `trace_id`, `parent_trace_id`, `lineage_path` (ordered list of parent IDs), `integrity_hash`. |
| **Replay Bundle** | `replay_bundle.json` | Pratham | `trace_id`, `replay_script`, `replay_status` (`SUCCESS`, `FAILURE`), `replay_logs`, `checksum`. |
| **Governance Bundle** | `validation_decision.json`<br>`governance_record.json`<br>`registration_reference.json`<br>`lineage_registration.json`<br>`lineage_chain.json` | Ansh (SHAKTI) | `decision` (`APPROVED`, `REJECTED`), `signed_by` (authorized human governor e.g. "Akash"), `signature`, `valid_authority` (boolean), `registered_at`, `valid_chain` (boolean). |
| **Convergence Bundle** | `tms_convergence_status.json`<br>`handover_bundle.json` | TANTRA | `convergence_status` (`CONVERGED`, `PENDING`, `FAILED`), `registration_exists` (boolean), `recipient`, `handover_status`. |

---

## 3. Outputs
The Review Engine must classify each trace into one of three deterministic states:

### 3.1 READY
* **Description**: The trace is fully verified, reconstructable, and ready for TANTRA convergence.
* **Conditions**:
  1. All 10 expected files exist in the trace directory.
  2. Evidence integrity verification succeeds (all actual file hashes match `evidence_bundle.json` and the bundle checksum is correct).
  3. Replay is fully successful (`replay_status == "SUCCESS"` with no fatal log errors).
  4. Governance decision is explicitly `APPROVED` with a valid governor signature and authority.
  5. Lineage chain is fully intact (`valid_chain == true` and parents reconstructable).
  6. Convergence status is `CONVERGED` and registration exists.

### 3.2 NEEDS_REVIEW
* **Description**: The trace has minor anomalies, missing optional metadata, or warnings, but is not corrupt or rejected. Requires human oversight.
* **Conditions**:
  1. Reconstructable trace but with minor warnings in logs or non-fatal missing files.
  2. Lineage chain is incomplete but not broken (e.g. parent trace ID exists but lineage bundle has warnings/unresolved nodes).
  3. Replay status is `WARNINGS` or contains partial logs.
  4. Governance record contains warning flags, but not a rejection.

### 3.3 REJECTED
* **Description**: The trace is untrusted, broken, or explicitly rejected by governance.
* **Conditions**:
  1. Governance decision is explicitly `REJECTED` or signed by an unauthorized actor.
  2. Replay status is `FAILURE` or missing entirely.
  3. Lineage break (invalid parent hash, or mismatch with actual DB events).
  4. Integrity failure (mismatch in SHA-256 hash of files or checksums).
  5. Convergence failure (`convergence_status == "FAILED"` or missing registration reference).

---

## 4. Deterministic Decision Matrix

| Evidence Integrity | Replay Status | Governance Decision | Lineage State | Convergence Status | Final Output State |
| :---: | :---: | :---: | :---: | :---: | :---: |
| Valid | SUCCESS | APPROVED | Complete | CONVERGED | **READY** |
| Valid | SUCCESS | APPROVED | Partial | CONVERGED | **NEEDS_REVIEW** |
| Valid | WARNINGS | APPROVED | Complete/Partial | CONVERGED | **NEEDS_REVIEW** |
| Valid | SUCCESS | APPROVED | Complete | PENDING | **NEEDS_REVIEW** |
| Corrupted | * | * | * | * | **REJECTED** |
| * | FAILURE | * | * | * | **REJECTED** |
| * | * | REJECTED | * | * | **REJECTED** |
| * | * | * | Broken / Gaps | * | **REJECTED** |
| * | * | * | * | FAILED | **REJECTED** |
| Missing | * | * | * | * | **REJECTED** |
