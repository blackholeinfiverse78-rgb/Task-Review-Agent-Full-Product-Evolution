# Handover & Deployment Documentation — Parikshak Production Certification

**Version:** v8.2.0 (Hardened Production Certification Release)  
**Status:** Certified & Production-Hardened  
**Date:** June 29, 2026  

---

## 1. Overview
This document serves as the official technical handover for the production certification closure of the Parikshak review platform. All blockers identified during the executive review (Security, Dependency Integrity, End-to-End Self-Review, and Ingestion Dataset completeness) have been successfully resolved without altering Parikshak's architectural boundaries.

---

## 2. Implemented Capabilities

### A. Closed Security Gate (Role-Based Access Control)
- **Role Enforcement**: Implemented JWT role verification dependencies mapping to four roles: `Governor`, `Reviewer`, `Operator`, and `Read Only`.
- **Protected Endpoints**: Core lifecycle APIs (`/submit`, `/history`, `/review/{submission_id}`, `/next/{submission_id}`) and consumable APIs (`/parikshak/review`, `/human-review/override`) now require Bearer token authorization headers.
- **Replay Protection**: Duplicate approval token/signature hashes are registered in `USED_APPROVAL_TOKENS` and rejected with `409 Conflict` (`REPLAY_REJECT`).
- **Boot Check**: Executes `validate_startup_secrets()` at server boot to warning/error if the default insecure JWT keys are present.
- **Trace Proofs**: Overrides write immutable validation decisions and governance metadata (`validation_decision.json` and `governance_record.json`) to the session trace folder.

### B. Dynamic Dependency Integrity Verification
- **Executable Validator**: The scanner dynamically evaluates packages in the active environment rather than relying on static file checklists.
- **Integrity Constraints**: Verifies strict `==` pinning, resolves transitive dependencies, checks against forbidden libraries (`unverified_lib`, `unsafe_bridge_plugin`, `backdoor`), and handles package name hyphens vs underscores (e.g., `pydantic-core` / `pydantic_core`).
- **CycloneDX SBOM**: Emits a standard `sbom.json` manifest to the trace session folder including component metadata and requirements checksums.
- **Certification Gate**: Hardened `production_certification_engine.py` to correctly block systems with failed dependency validation.

### C. Authoritative Dataset Ingestion
- **17 Ingestion Fields**: Expanded `DatasetIntakeRequest` to validate all 17 authoritative fields requested by Akash.
- **Backward Mappings**: Built a model validator mapping older requests to prevent data loss or ingestion failures.

### D. End-to-End Self-Certification
- **Integrated Test Suite**: Implemented `tests/security_dependency_hardening_test.py` verifying functionally correct reviews, negative security gates, dependency integrity, recovery parity, determinism consistency, and the complete 12-step certification pipeline.

---

## 3. Core File Map

| Component | Absolute Path | Role / Description |
| :--- | :--- | :--- |
| **Security Middleware** | [middleware.py](file:///g:/Live%20Task%20Review%20Agent%20-%202/security/middleware.py) | JWT generation, token verification, role checks, replay prevention, boot validation |
| **Ingestion Handler** | [dataset_intake.py](file:///g:/Live%20Task%20Review%20Agent%20-%202/evaluation_engine/dataset_intake.py) | 17-field validation request model and backward-compatible model validator |
| **Ecosystem Validator** | [ecosystem_participation_validator.py](file:///g:/Live%20Task%20Review%20Agent%20-%202/ecosystem_participation_validator.py) | Dynamic requirements validation, cycle checks, and sbom.json CycloneDX export |
| **Certification Engine** | [production_certification_engine.py](file:///g:/Live%20Task%20Review%20Agent%20-%202/production_certification_engine.py) | Hardened security validations and dependency gate enforcement |
| **Database Mappers** | [persistent_storage.py](file:///g:/Live%20Task%20Review%20Agent%20-%202/db/persistent_storage.py) | Hybrid mapper that merges SQLite database records with memory/JSON fields |
| **Hardening Test Suite** | [security_dependency_hardening_test.py](file:///g:/Live%20Task%20Review%20Agent%20-%202/tests/security_dependency_hardening_test.py) | Full functional, negative security, dependency validation, recovery, and determinism loops |

---

## 4. Execution & Verification Guide

### A. Run Hardening Test Suite
To execute the comprehensive hardening test suite validating functional correctness, role security, dependency integrity, recovery, and determinism:
```bash
python -m unittest tests/security_dependency_hardening_test.py
```

### B. Run Production Certification Tests
To execute the standard certification report validations:
```bash
python -m unittest tests/production_certification_test.py
```

### C. Re-generate local tokens
To obtain a valid JWT token programmatically for testing endpoints:
```python
from security.middleware import SecurityConfig
token = SecurityConfig.create_access_token({"sub": "Akash", "role": "Governor"})
print("Bearer Token:", token)
```
