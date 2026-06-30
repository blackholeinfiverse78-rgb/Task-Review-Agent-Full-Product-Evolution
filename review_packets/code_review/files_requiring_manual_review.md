# Files Requiring Manual Review

The following production components contain critical security boundaries, event sourcing models, or dependency gates. Operations and security officers should manually review these files.

---

## 1. Security Gates
### [security/middleware.py](file:///g:/Live%20Task%20Review%20Agent%20-%202/security/middleware.py)
* **Lines of Interest**: [L41-132](file:///g:/Live%20Task%20Review%20Agent%20-%202/security/middleware.py#L41-132)
* **What to verify**:
    * JWT decode logic and verification of expiration metadata.
    * Replay validation: duplicate signatures must register in `USED_APPROVAL_TOKENS` and return `409 Conflict`.
    * Boot check `validate_startup_secrets()` to ensure default secrets are not loaded.

---

## 2. Ingestion Model Compliance
### [evaluation_engine/dataset_intake.py](file:///g:/Live%20Task%20Review%20Agent%20-%202/evaluation_engine/dataset_intake.py)
* **What to verify**:
    * Schema verification of all 17 fields in the authoritative intake specification.
    * Backward compatibility mapping functions to prevent ingestion failures on legacy submissions.

---

## 3. Dependency Pinning & SBOM Manifest Generation
### [ecosystem_participation_validator.py](file:///g:/Live%20Task%20Review%20Agent%20-%202/ecosystem_participation_validator.py)
* **What to verify**:
    * Checks against unverified or unsafe package installations (`unverified_lib`, etc.).
    * CycloneDX standard `sbom.json` manifest structure export.

---

## 4. Production Score calculations
### [production_certification_engine.py](file:///g:/Live%20Task%20Review%20Agent%20-%202/production_certification_engine.py)
* **What to verify**:
    * Weighted metrics for computing the 12 core readiness dimensions.
    * Rules blocking systems with failures in security, recovery, or layer checks.

---

## 5. Storage Layer
### [db/persistent_storage.py](file:///g:/Live%20Task%20Review%20Agent%20-%202/db/persistent_storage.py)
* **What to verify**:
    * Serialized sqlite transaction loops and hybrid JSON/sqlite memory mappers.
