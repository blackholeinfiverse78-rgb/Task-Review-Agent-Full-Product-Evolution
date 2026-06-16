# PARIKSHAK COORDINATION SUMMARY (V1)

This document establishes the charter, participant roles, communication protocols, and meeting minutes for the **Parikshak Coordination Group**. This group ensures cross-team alignment and manages integrations between Parikshak and other BHIV ecosystem components.

---

## 1. Group Charter & Participant Mandate

The group meets daily to monitor convergence, track dependency states, acquire calibration data, and evaluate integration readiness.

### Participants & Roles
*   **Akash Sir (Leadership / Owner)**: Directs long-term convergence, review approvals, and data accessibility.
*   **Jeetu Sir (Operations / Sponsor)**: Coordinates office schedules and provides human reviews/override resources.
*   **Sri Satya (Intelligence Layer)**: Aligns Common Core rules, explainability engines, and calibration parameters.
*   **Nikhil (Niyantran Integration)**: Validates candidate run execution logs, test outputs, and webhook adapters.
*   **Rishabh (Workflow Validation)**: Validates live developer workflows and checks integration boundaries.
*   **Soham (Gurukul Integration)**: Aligns developer competency schemas, certifications, and progression data.
*   **HackaVerse Members**: Facilitate testing, sandbox execution, and feedback collection.

---

## 2. Daily Update Template

To maintain clear and structured communication, participants will submit their daily reports using the following template:

```markdown
### Parikshak Daily Status Report: [Date]
**Reporter**: [Name] | **Role**: [E.g., Gurukul Integration]

#### 1. Accomplishments (Last 24 Hours)
*   [Detail completed tasks, api integrations, or documentation updates]

#### 2. Core Dependencies & Blockers
*   [List any blocking issues or dependencies on other teams]

#### 3. Integration Readiness Status
*   [Current state: Green / Yellow / Red]
*   [Contracts verified: Yes/No]

#### 4. Planned Actions (Next 24 Hours)
*   [Detail targeted goals for the next sprint day]
```

---

## 3. First Coordination Meeting Minutes

**Date**: June 8, 2026  
**Chair**: Akash Sir  
**Attendees**: Akash Sir, Jeetu Sir, Sri Satya, Nikhil, Rishabh, Soham  

### Agenda
1.  **Common Core Alignment**: Define the boundary map between Parikshak and external components.
2.  **Calibration Data Acquisition**: Establish timelines for extracting the historical database.
3.  **Integration Adapters Contract**: Align on REST APIs and schema formats.

### Discussion & Decisions
*   **Common Core Boundary**: The group unanimously approved the division of ownership. Parikshak will consume execution logs from Niyantran and skill profiles from Gurukul, rather than maintaining independent records.
*   **Data Extraction Schedule**: Akash Sir committed to providing a sanitized SQLITE database (`calibration_history.sqlite`) containing historical reviews and assignments within 48 hours.
*   **Unified Lineage Checks**: Nikhil and Soham agreed to append the standard `trace_id` header to all transaction envelopes to enable end-to-end replay audit tracking.
*   **External vs Internal Focus**: Rishabh highlighted the need for distinct dashboard interfaces. The group decided to separate the endpoints for External Judges (MahaIT) and Internal Team Leads.

### Action Items
*   **Nikhil**: Prepare the Niyantran adapter to export sandboxed unit test metrics using the new `run_status` contract. (Due: June 10)
*   **Soham**: Deploy the Gurukul skill profile query API endpoint for candidate skill lookup. (Due: June 11)
*   **Sri Satya**: Calibrate the rule engine configurations using the upcoming calibration dataset. (Due: June 12)
*   **Rishabh**: Set up automated readiness tests for the dual-mode ingestion interfaces. (Due: June 10)
