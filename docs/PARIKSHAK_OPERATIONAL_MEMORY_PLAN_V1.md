# PARIKSHAK OPERATIONAL MEMORY PLAN (V1)

This document outlines the canonical population strategy and SQLite database schema designed to prepare Parikshak's long-term memory. The goal is to ingest real historical logs from the BHIV ecosystem and structure them for search, explainability, and replay.

---

## 1. Database Architecture

We define a relational SQLite schema (`parikshak_memory.sqlite`) that preserves data lineage, provenance, and governance references.

```
       +--------------------+          +--------------------+
       |     candidates     |          |       tasks        |
       +---------+----------+          +---------+----------+
                 |                               |
                 | 1                             | 1
                 |                               |
                 | N                             | N
       +---------v----------+          +---------v----------+
       |    assignments     +----------+      test_runs     |
       +---------+----------+ 1      N +---------+----------+
                 |                               |
                 | 1                             | 1
                 |                               |
                 | N                             | N
       +---------v----------+          +---------v----------+
       |      reviews       +----------+   reasoning_logs   |
       +---------+----------+ 1      1 +--------------------+
                 |
                 | 1
                 |
                 v
       +--------------------+
       |  governance_logs   |
       +--------------------+
```

---

## 2. Table Definitions

### 2.1 Candidate Profiles (`candidates`)
Tracks candidate identity and cumulative performance metrics.
```sql
CREATE TABLE candidates (
    candidate_id TEXT PRIMARY KEY,
    name_hash TEXT NOT NULL,
    skills TEXT NOT NULL,                -- JSON string: {"python": 0.8, "sql": 0.6}
    certified_competencies TEXT,         -- JSON array: ["REST_API", "JWT_AUTH"]
    current_stage TEXT NOT NULL          -- beginner, intermediate, advanced
);
```

### 2.2 Task Registry (`tasks`)
Static definition of available assignments.
```sql
CREATE TABLE tasks (
    task_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    difficulty TEXT NOT NULL,            -- beginner, intermediate, advanced
    prerequisites TEXT                   -- JSON array of task_id dependencies
);
```

### 2.3 Assignment Registry (`assignments`)
Tracks the relationship between a candidate, a task, and its status.
```sql
CREATE TABLE assignments (
    assignment_id TEXT PRIMARY KEY,
    candidate_id TEXT NOT NULL,
    task_id TEXT NOT NULL,
    assigned_by TEXT NOT NULL,
    assigned_at TEXT NOT NULL,
    status TEXT NOT NULL,                -- pending, submitted, reviewed, closed
    FOREIGN KEY(candidate_id) REFERENCES candidates(candidate_id),
    FOREIGN KEY(task_id) REFERENCES tasks(task_id)
);
```

### 2.4 Submission Reviews (`reviews`)
Records of evaluation outcomes.
```sql
CREATE TABLE reviews (
    review_id TEXT PRIMARY KEY,
    assignment_id TEXT NOT NULL,
    trace_id TEXT NOT NULL UNIQUE,
    evaluation_result TEXT NOT NULL,    -- PASS, FAIL
    failure_type TEXT,                  -- schema_violation, incomplete, incorrect_logic, integration_fail
    score INTEGER NOT NULL,
    decision TEXT NOT NULL,              -- APPROVED, REJECTED, MODIFIED
    reviewed_at TEXT NOT NULL,
    FOREIGN KEY(assignment_id) REFERENCES assignments(assignment_id)
);
```

### 2.5 Testing Outcomes (`test_runs`)
Factual code runner outcomes imported from Niyantran.
```sql
CREATE TABLE test_runs (
    run_id TEXT PRIMARY KEY,
    submission_id TEXT NOT NULL,
    tests_total INTEGER NOT NULL,
    tests_passed INTEGER NOT NULL,
    build_status TEXT NOT NULL,          -- SUCCESS, COMPILE_ERROR, TIMEOUT
    coverage_percent REAL NOT NULL,
    executed_at TEXT NOT NULL
);
```

### 2.6 Reasoning Artifacts (`reasoning_logs`)
Human and machine explanations for decisions.
```sql
CREATE TABLE reasoning_logs (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    review_id TEXT NOT NULL,
    evaluator_type TEXT NOT NULL,        -- machine, human_override
    comments TEXT NOT NULL,
    confidence_score REAL NOT NULL,
    FOREIGN KEY(review_id) REFERENCES reviews(review_id)
);
```

### 2.7 Lineage Links (`lineage_links`)
Tracks parent-to-child progression chains.
```sql
CREATE TABLE lineage_links (
    link_id INTEGER PRIMARY KEY AUTOINCREMENT,
    trace_id TEXT NOT NULL,
    parent_trace_id TEXT,
    sequence_number INTEGER NOT NULL,
    event_type TEXT NOT NULL             -- submission, assignment_change, progression
);
```

### 2.8 Governance References (`governance_logs`)
Cryptographic hashes and human signatures.
```sql
CREATE TABLE governance_logs (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_id TEXT NOT NULL,             -- reference to review_id or assignment_id
    actor TEXT NOT NULL,                 -- governor who signed off
    signature TEXT NOT NULL,             -- cryptographic validation hash
    parent_event_hash TEXT NOT NULL,
    event_hash TEXT NOT NULL
);
```

---

## 3. Data Ingestion Pipeline Strategy

To populate the operational memory, we define a 4-step ETL pipeline:

```
[Extract: Niyantran & Saarthi logs] ---> [Transform & Cleanse] ---> [Verify Hash Chains] ---> [Commit to SQLite Memory]
```

1.  **Extract**: Pull historical payloads from Niyantran and Saarthi log databases.
2.  **Transform**: Parse unstructured review files and extract JSON payloads. Format all timestamps to ISO-8601. Map human remarks to the `reasoning_logs` schema.
3.  **Validate**: Verify that every record has a corresponding `trace_id`. Remove duplicates.
4.  **Load (Committing)**: Insert records into the tables using a transaction manager. Ensure that database foreign key constraints are enabled (`PRAGMA foreign_keys = ON`).

---

## 4. Verification & Diagnostic Queries

To audit the database after population, the following diagnostic queries will be executed:

*   **Audit Check 1: Find Orphan Reviews** (Reviews missing valid assignments)
    ```sql
    SELECT review_id, trace_id FROM reviews 
    WHERE assignment_id NOT IN (SELECT assignment_id FROM assignments);
    ```
*   **Audit Check 2: Measure Decision Parity** (Check discrepancies where low machine confidence was resolved by human overrides)
    ```sql
    SELECT r.review_id, r.evaluation_result, rl.confidence_score, rl.comments 
    FROM reviews r 
    JOIN reasoning_logs rl ON r.review_id = rl.review_id 
    WHERE rl.evaluator_type = 'human_override' AND rl.confidence_score < 0.98;
    ```
*   **Audit Check 3: Check Event Chain Integrity** (Find breaks in sequence ordering)
    ```sql
    SELECT l1.trace_id, l1.sequence_number, l2.sequence_number 
    FROM lineage_links l1
    LEFT JOIN lineage_links l2 ON l1.trace_id = l2.trace_id AND l2.sequence_number = l1.sequence_number + 1
    WHERE l2.link_id IS NULL AND l1.sequence_number < (SELECT MAX(sequence_number) FROM lineage_links WHERE trace_id = l1.trace_id);
    ```
