# OPEN QUESTIONS REGISTER

This register tracks ongoing design issues, integration risks, and open questions across the Parikshak Common Core implementation.

---

## 1. Active Open Questions

### Q1: Ingestion of Private Repositories in Sandboxed Evaluations
*   **Description**: How will Parikshak crawl and analyze private GitHub repositories submitted by candidates?
*   **Impact**: **High**. If credentials are not accessible, Repository Crawling will return `integration_fail`.
*   **Proposed Solution**: Ingest a scoped GITHUB_TOKEN header dynamically from Niyantran's API call, rather than storing credentials in Parikshak.
*   **Owner**: Nikhil (Niyantran) / Sampada
*   **Status**: **Open**

---

### Q2: Versioning of Gurukul Competence Profile Records
*   **Description**: How do we handle changes in candidate skill profiles over time during calibration replays? Replays need to evaluate the candidate's skill state *at the time of the historical submission*, not their current state.
*   **Impact**: **Medium**. If Gurukul only stores current skill levels, replay recommendations will suffer from look-ahead bias.
*   **Proposed Solution**: Gurukul should expose an event-sourced history of skill mutations, allowing Parikshak to query the candidate profile at any arbitrary historical timestamp.
*   **Owner**: Soham (Gurukul)
*   **Status**: **Open**

---

### Q3: Calibration Threshold Tuning Criteria
*   **Description**: What is the acceptable threshold for False Positives (machine PASS, human REJECT) during the calibration phase?
*   **Impact**: **High**. Setting the threshold too tight triggers excessive escalations, while setting it too loose permits substandard submissions.
*   **Proposed Solution**: Target a False Positive rate of $< 1.0\%$. If replay results exceed this limit, tighten the Sri Satya evaluation constraints.
*   **Owner**: Sri Satya / Akash Sir
*   **Status**: **Open**

---

### Q4: Parallel Commits at Gov-OS Event Ledger
*   **Description**: If multiple submissions are processed simultaneously, how do we enforce monotonic sequence ordering without locking database connections indefinitely?
*   **Impact**: **Critical**. Concurrency conflicts could block evaluations in production.
*   **Proposed Solution**: Enforce a Single-Writer queue mutex inside the SQLite adapter to serialize commits, keeping read models non-blocking via WAL mode.
*   **Owner**: MDU (Canonical Data Discipline)
*   **Status**: **Resolved** (Implemented in `canonical_db/db.py`)
