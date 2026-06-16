# BHIV Calibration Data Request

This document lists the historical operational data required from leadership to evaluate and calibrate Parikshak against real Blackhole Infiverse (BHIV) history.

---

## 1. Candidate Submission Data (Raw Inputs)
To test Parikshak's intent extraction and repository analysis models, we require:
- **Submission Repository Links**: URLs of actual GitHub repositories submitted by candidates for historical tasks.
- **Task Definitions**: The exact historical task titles and description texts that matches each repository URL.
- **PDF Specifications**: Any accompanying task documentation, rules, or requirements files provided to candidates.
- **Metadata**: Candidate identifiers, timestamps of submission, and attempt numbers.

---

## 2. Historical Review Records (Ground Truth Outcomes)
To evaluate the accuracy of the rule engine's PASS/FAIL outcomes, we require:
- **Historical Evaluations**: The final binary outcome (PASS or FAIL) received by each candidate submission.
- **Failure Types**: The primary reason assigned for each failure, mapped to one of:
  - `schema_violation` (e.g., missing repositories, bad module registrations).
  - `incomplete` (e.g., missing code files, missing documentation or README).
  - `incorrect_logic` (e.g., missing features, low completion ratios).
  - `integration_fail` (e.g., repository fetching errors).
- **Quality Rubric Scores**: Stored scores and grading levels (A, B, C, D) assigned by judges.

---

## 3. Human Reviewer Reasoning (Cognitive Calibration)
To align Parikshak's automated routing reasons and override notes with human judge consensus, we require:
- **Reviewer Rationales**: Written comments, notes, or reviews created by human judges explaining *why* a submission passed or failed.
- **Override History**: Instances where a judge overrode an automated evaluation result, including:
  - The original machine output.
  - The manual override decision.
  - The justification notes written by the judge.

---

## 4. Assignment Records & Task Lineage (Routing Accuracy)
To calibrate the traversal logic and next-task selections, we require:
- **Task Traversal History**: Records of next tasks assigned to candidates following a review.
- **Task Graph Lineage**: The chronological hierarchy of tasks:
  - Parent-child task mappings.
  - Correction tasks assigned for specific failure types.
  - Advancement tasks assigned for successful submissions.
  - Evolutionary stages and focus areas.
- **Prerequisite trees**: Static or dynamic dependencies between historical tasks.
