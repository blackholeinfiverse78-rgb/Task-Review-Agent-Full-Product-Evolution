# 🧪 Testing & Validation Guide (Gov-OS Hardened)

This guide documents the test execution pipeline for verifying Gov-OS constraints, database hardening, and deterministic event sourcing.

---

## 1. Gov-OS Self-Test Diagnostic Suite

We run a dedicated, low-level system diagnostic suite to verify core security, integrity, and synchronization guarantees.

### Running Diagnostics
Execute the suite with UTF-8 encoding enabled:
```bash
python -X utf8 scratch/test_operating_system.py
```

### Verified Scenarios (TEST-01 to TEST-12)
1. **TEST-01 (DB Init)**: Confirms correct database initialization and event schema creation.
2. **TEST-02 (Write Validation)**: Checks event serialization, checksum generation, and hash-chaining logic.
3. **TEST-03 (Corruption Detection)**: Verifies the integrity scanner detects hash mismatches, schema drift, and invalid event sequences.
4. **TEST-04 (Restore Proof)**: Validates state restoration using backup manifests.
5. **TEST-05 (Replay Reconstruction)**: Verifies database reconstruction from raw JSONL journals.
6. **TEST-06 (GPT Boundary)**: Assures the GPT bridge remains isolated and cannot commit mutations directly.
7. **TEST-07 (Human Approval Lock)**: Ensures standard operations reject mutations lacking a governor's signature.
8. **TEST-08 (Autonomous Release Rejection)**: Blocks releases that are not explicitly human-approved (`AutonomousReleaseBlocked`).
9. **TEST-09 (Ecosystem Integration)**: Verifies propagation to external adapters (`niyantran`, `saarthi`, etc.).
10. **TEST-10 (Concurrency)**: Validates mutex protection against race conditions under parallel write pressure.
11. **TEST-11 (Schema Drift)**: Confirms the static schema registry blocks invalid payloads.
12. **TEST-12 (Determinism)**: Assures that multiple sequential state reconstructions produce identical, deterministic states.

---

## 2. Running Proof Generators

The proof generator script produces validation files under `/proofs`, `/snapshots`, `/test_vectors`, `/integrity_reports`, and `/replay_logs`:
```bash
python -X utf8 scripts/generate_proofs.py
```
This is required before deploying code to confirm system properties.
