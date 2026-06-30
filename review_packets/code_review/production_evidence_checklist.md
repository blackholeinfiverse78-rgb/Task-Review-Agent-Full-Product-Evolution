# Production Evidence Checklist

This checklist maps each participating service in the BHIV ecosystem to its deterministic proof of validation.

| Service | Responsibility | Operational Evidence / Location | Status |
| :--- | :--- | :--- | :--- |
| **TANTRA** | Participant Registration & Gov Execution | Verification of placement layers, ownership declarations, and boundary compliance rules in [ecosystem_flow_proof.md](file:///g:/Live%20Task%20Review%20Agent%20-%202/review_packets/ecosystem_flow_proof.md). | **PASSED** |
| **GC** | Constitutional Overrides & Validation | Validation decisions and signed credentials stored in [final_gc_review.md](file:///g:/Live%20Task%20Review%20Agent%20-%202/review_packets/final_gc_review.md). | **PASSED** |
| **MDU** | Replay Integrity & Schema Stability | Lineage hash pointer chains and drift checks verified in [runtime_evidence_report.md](file:///g:/Live%20Task%20Review%20Agent%20-%202/review_packets/runtime_evidence_report.md). | **PASSED** |
| **Gov-OS** | Production Event Journaling | Event journal commits logged in `storage/canonical_db.sqlite` and verified in [event_journal_proof.md](file:///g:/Live%20Task%20Review%20Agent%20-%202/review_packets/event_journal_proof.md). | **PASSED** |
| **Saarthi** | Visibility Propagation | Appends logged in `storage/saarthi_visibility.jsonl` verifying entry propagation. | **PASSED** |
| **Bucket** | Ingested Knowledge Auditing | Index lines logged in `storage/bucket_logs/evaluation_index.jsonl`. | **PASSED** |
| **Niyantran** | Automatic Task Re-assignment | Creation of recommended next tasks in `storage/niyantran_assignments.jsonl`. | **PASSED** |
| **Pravah** | Replay Continuity | Lineage and cryptographic event hash pairs validated in `storage/pravah_replay.jsonl`. | **PASSED** |
| **Vinayak** | Production Testing & Acceptance | Verified by the 7-phase readiness test script [production_readiness_test.py](file:///g:/Live%20Task%20Review%20Agent%20-%202/tests/production_readiness_test.py) and ecosystem acceptance tests [test_ecosystem_acceptance.py](file:///g:/Live%20Task%20Review%20Agent%20-%202/tests/test_ecosystem_acceptance.py). | **PASSED** |
| **Central Depository**| Handover Acceptance Package | Assembly of complete deployment and rollback manuals in root directory. | **PASSED** |

