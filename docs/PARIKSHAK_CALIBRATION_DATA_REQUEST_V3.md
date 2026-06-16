# PARIKSHAK CALIBRATION DATA REQUEST (V3)

**To**: Akash Sir  
**From**: Parikshak Integration Team  
**Subject**: Historical Calibration Data Request (Real Dataset Requirement)  

This document outlines the detailed historical dataset requested to calibrate the Parikshak Common Core. To guarantee recommendation safety and explainability, **synthetic calibration datasets are strictly prohibited**. We require raw, real-world operational logs and records mapped to the schemas below.

---

## 1. Required Data Categories & Schemas

We request the historical records from the following 9 categories, formatted as a unified SQLite database (`calibration_history.sqlite`) or as structured JSONL extracts.

### 1.1 Task Assignments (`task_assignments`)
Tracks the initial allocation of tasks to candidates.
*   `assignment_id` (TEXT, PK): Unique assignment identifier.
*   `task_id` (TEXT, FK): Identifier of the assigned task.
*   `candidate_id` (TEXT): Anonymized candidate identifier.
*   `assigned_by` (TEXT): Role or system that initiated the assignment.
*   `assigned_at` (TIMESTAMP): Date and time of assignment.

### 1.2 Task Reviews (`task_reviews`)
Tracks the grading rubric and high-level evaluation metadata.
*   `review_id` (TEXT, PK): Unique review identifier.
*   `task_id` (TEXT, FK): Task identifier.
*   `reviewer_id` (TEXT): Anonymized identifier of the reviewing judge.
*   `score` (INTEGER): Raw score assigned (e.g., 0–100).
*   `rubric_score_details` (TEXT): JSON containing sub-scores (Completeness, Code Quality, Architecture).
*   `comments` (TEXT): Verbal remarks and feedback from the reviewer.

### 1.3 Submission Reviews (`submission_reviews`)
Factual check of the repository deliverables.
*   `submission_id` (TEXT, PK): Unique submission identifier.
*   `assignment_id` (TEXT, FK): Reference to the assignment record.
*   `repository_url` (TEXT): Git repository path.
*   `submitted_at` (TIMESTAMP): Date and time of candidate submission.
*   `commit_sha` (TEXT): Git commit identifier of the submission.
*   `review_packet_present` (BOOLEAN): Status of the review packet file.

### 1.4 Testing Reports (`testing_reports`)
Sandbox output data from code executions.
*   `report_id` (TEXT, PK): Unique report identifier.
*   `submission_id` (TEXT, FK): Reference to the submission record.
*   `tests_total` (INTEGER): Number of tests found.
*   `tests_passed` (INTEGER): Number of tests passed successfully.
*   `build_status` (TEXT): E.g., `SUCCESS`, `COMPILE_ERROR`, `TIMEOUT`.
*   `coverage_percent` (REAL): Test coverage ratio.

### 1.5 Acceptance Decisions (`acceptance_decisions`)
Records of tasks approved for progression.
*   `decision_id` (TEXT, PK): Unique decision identifier.
*   `submission_id` (TEXT, FK): Reference to the submission record.
*   `accepted_by` (TEXT): Authorizing Governor (e.g., "Akash", "Vinayak").
*   `accepted_at` (TIMESTAMP): Date and time of approval.
*   `notes` (TEXT): Justification notes for acceptance.

### 1.6 Rejection Decisions (`rejection_decisions`)
Records of tasks rejected and reasons why.
*   `decision_id` (TEXT, PK): Unique decision identifier.
*   `submission_id` (TEXT, FK): Reference to the submission record.
*   `rejected_by` (TEXT): Authorizing Governor.
*   `rejected_at` (TIMESTAMP): Date and time of rejection.
*   `failure_type` (TEXT): Classified reason (e.g., `schema_violation`, `incomplete`, `incorrect_logic`).
*   `rejection_notes` (TEXT): Detailed explanation of failure constraints.

### 1.7 Progression Records (`progression_records`)
Tracks candidate advancement along skill levels.
*   `progression_id` (TEXT, PK): Unique record identifier.
*   `candidate_id` (TEXT): Anonymized candidate identifier.
*   `stage_from` (TEXT): Preceding tier (e.g., `beginner`).
*   `stage_to` (TEXT): Advanced tier (e.g., `intermediate`).
*   `transitioned_at` (TIMESTAMP): Timestamp of stage completion.

### 1.8 Escalation Records (`escalation_records`)
Tracks low-confidence evaluations routed to judges.
*   `escalation_id` (TEXT, PK): Unique escalation identifier.
*   `submission_id` (TEXT, FK): Reference to the submission.
*   `confidence_score` (REAL): Evaluation confidence (e.g., `< 0.98`).
*   `escalated_at` (TIMESTAMP): Timestamp of trigger.
*   `resolved_by` (TEXT): Reviewing judge signature.
*   `resolved_at` (TIMESTAMP): Timestamp of resolution.
*   `resolution_action` (TEXT): E.g., `OVERRIDDEN_PASS`, `CONFIRMED_FAIL`.

### 1.9 Assignment Changes (`assignment_changes`)
Tracks modifications and manual overrides to task assignments.
*   `change_id` (TEXT, PK): Unique change identifier.
*   `assignment_id` (TEXT, FK): Target assignment.
*   `original_task_id` (TEXT): Task before modification.
*   `new_task_id` (TEXT): Task after modification.
*   `changed_by` (TEXT): Authorizing Governor.
*   `changed_at` (TIMESTAMP): Timestamp of action.
*   `reason` (TEXT): Explanation for manual assignment override.

---

## 2. Extraction & Anonymization Guidelines

1.  **PII Sanitization**: Replace developer names, phone numbers, and emails with deterministic hashes (`candidate_id = SHA256(real_name + salt)`). Preserve mapping integrity so that progression tracks across the same candidate can be analyzed.
2.  **Repository Integrity**: Keep historical repository references and directory paths intact. Do not delete test folders, README files, or architecture structures.
3.  **Delivery Format**: Provide data in standard SQLITE format to allow direct replay validation.
