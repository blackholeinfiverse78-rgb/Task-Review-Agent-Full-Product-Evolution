# REVIEW PACKET — Parikshak v8.0.0 (Production Readiness Certification Service)

## ENTRY POINT

The primary execution entry point of the Parikshak Production Readiness Certification Service is located in [main.py](file:///g:/Live%20Task%20Review%20Agent%20-%202/main.py). 
The FastAPI routes are defined inside [api/production.py](file:///g:/Live%20Task%20Review%20Agent%20-%202/api/production.py). 

The key API endpoints exposed are:
*   `GET /api/v1/production/certification/{trace_id}`: Standard HTTP endpoint to execute production certification.
*   `GET /api/v1/production/ecosystem-participation/{trace_id}`: Standard HTTP endpoint to validate topological ecosystem roles.
*   `GET /api/v1/production/constitutional-review/{trace_id}`: Legacy readiness lookup.

## CORE FLOW

The certification pipeline executes a sequence of deterministic steps:
1.  **Ingestion Gate**: The system fetches execution traces and artifact files from `storage/traces/{trace_id}/`.
2.  **Evidence Validation**: Runs checks on Pratham outputs (evidence, replay, lineage, and handover bundles) to verify integrity and correctness.
3.  **Governance Gate**: Shakti validations verify that a validation decision exists, is approved, and contains an authorized signature.
4.  **Ecosystem Validation**: Runs checks on layer placement, boundaries, dependencies, and registrations.
5.  **Readiness Score Computation**: Calculates the score using a strict weighted model of the 12 production dimensions.
6.  **Decision Mapping**: Evaluates the decision tree to output the final verdict: `READY`, `READY WITH OBSERVATIONS`, `NEEDS REVIEW`, `NOT PRODUCTION READY`, or `UNKNOWN`.
7.  **Standard Report Export**: Writes the standard dashboard JSON conforming to the schema and returns the output packet.

## LIVE FLOW

To certify a system, send an HTTP GET request to the Parikshak certification endpoint:
`GET /api/v1/production/certification/{trace_id}`

The intake processing sequence is:
1.  **Request Handler**: Receives `trace_id` and forwards it to the `ProductionCertificationEngine`.
2.  **File Loading**: Scans `storage/traces/{trace_id}/` for all Pratham, Shakti, MDU, and TMS bundles.
3.  **Dimension checks**: Evaluates the 12 mandatory production dimensions (Runtime, Replayability, Governance, Security, versioning, recovery, etc.) and records reasons.
4.  **Ecosystem check**: Checks layer boundaries, dependencies, and registrations.
5.  **Score calculation**: Computes the readiness percentage and formats the final status.
6.  **JSON Response**: Returns the report conforming exactly to the standard dashboard schema.

## OUTPUT SAMPLE

Here is a sample response payload returned by the Parikshak certification service:

```json
{
  "system_information": {
    "trace_id": "trace-prod-ready",
    "certified_at": "2026-06-20T06:00:00Z",
    "verifier": "Parikshak Production Certification Engine v1.0"
  },
  "dimensions": {
    "Runtime": "PASS",
    "Observability": "PASS",
    "Replayability": "PASS",
    "Governance": "PASS",
    "Provenance": "PASS",
    "Security": "PASS",
    "Versioning": "PASS",
    "Recovery": "PASS",
    "Human Approval": "PASS",
    "Layer Placement": "PASS",
    "Dependency Integrity": "PASS",
    "Ecosystem Participation": "PASS"
  },
  "production_score": 100,
  "certification_decision": "READY",
  "critical_failures": [],
  "warnings": [],
  "risk_summary": "System demonstrates compliant architectural boundaries, verified replay safety, and full ecosystem integration. Approved for governed TANTRA production.",
  "evidence_summary": {
    "evidence_bundle.json": "PRESENT",
    "handover_bundle.json": "PRESENT"
  },
  "replay_status": "PASS",
  "governance_status": "PASS",
  "observability_status": "PASS",
  "security_status": "PASS",
  "recovery_status": "PASS",
  "dependencies": {
    "status": "PASS"
  },
  "evaluation_result": "PASS",
  "failure_type": null,
  "trace_id": "trace-prod-ready"
}
```

---

## ARCHITECTURE & SYSTEM DESIGN

Parikshak has been evolved from a file-bound verification engine into a canonical Production Engineering Platform using the following layout:

```mermaid
graph TD
    Ingestion[Trace & Ingestion Gate] --> Engine[Production Certification Engine]
    Engine --> DB[Parikshak Database Layer]
    Engine --> Fallback[JSON File Sync System]
    Engine --> Assignment[Automatic Assignment Engine]
    Assignment --> DB
    DB --> Dashboard[Executive Dashboard APIs]
    DB --> Legacy[Backward Compatibility API Queries]
```

### Flow Sequence of Trace Ingestion & Task Generation

```mermaid
sequenceLineage
    actor Builder as Builder/CI
    participant API as Ingestion API (api/production.py)
    participant Engine as Certification Engine
    participant DB as SQL Database Layer
    participant AE as Automatic Assignment Engine
    
    Builder ->> API: GET /api/v1/production/certification/{trace_id}
    API ->> Engine: load_trace_and_run_dimensions(trace_id)
    Engine ->> Engine: Calculate production score & checks (12 dimensions)
    Engine ->> DB: store_certification() & store_review()
    Engine ->> AE: trigger_assessment(failed_dimensions)
    AE ->> AE: Calculate Priority, Difficulty, AI Effort
    AE ->> DB: store_assignments()
    Engine ->> API: return evaluation report
    API ->> Builder: HTTP 200 JSON Receipt
```

---

## DATABASE DOCUMENTATION

Parikshak DB is built on top of SQLAlchemy with an Alembic-backed migration path. Below is the Entity-Relationship (ER) layout of the database:

```mermaid
erDiagram
    BUILDERS ||--o{ ASSIGNMENTS : receives
    PRODUCTS ||--o{ REPOSITORIES : maps
    PRODUCTS ||--o{ CERTIFICATIONS : certifies
    PRODUCTS ||--o{ HISTORICAL_METRICS : aggregates
    REVIEWS ||--o{ EVIDENCE : links
    REVIEWS ||--o{ ARTIFACTS : stores
    REVIEWS ||--o{ DIMENSION_RESULTS : scores
    REVIEWS ||--o{ ASSIGNMENTS : triggers
    REVIEWS ||--o{ RISK_REGISTER : registers
    TASK_SUBMISSIONS }|--|| REVIEWS : reviews
    TRACE_SESSIONS }|--|| REVIEWS : traces
```

### Table Mappings & Schema Descriptions
All models are structured inside [models.py](file:///g:/Live%20Task%20Review%20Agent%20-%202/db/models.py). The key columns and constraints are detailed below:
1. **`builders`**: Uniquely tracks registered builder engineers (`id` PRIMARY KEY, `name`, `email`, `deleted_at`).
2. **`products`**: Uniquely tracks certified software modules (`id` PRIMARY KEY, `name`, `description`).
3. **`repositories`**: Maps repository URLs and branches to products (`id` PRIMARY KEY, `product_id` FOREIGN KEY, `repo_url`, `branch`).
4. **`task_submissions`**: Stores ingested pipeline task payloads (`submission_id` PRIMARY KEY, `task_id`, `task_title`, `submitted_by`).
5. **`reviews`**: Stores detailed grading decisions (`review_id` PRIMARY KEY, `score`, `evaluation_result` PASS/FAIL, `status`, `decision`).
6. **`evidence`**: Stores files and URLs extracted from runtime traces (`id` PRIMARY KEY, `review_id` FOREIGN KEY, `file_path`).
7. **`assignments`**: Tracks corrective training and tasks generated dynamically by Parikshak (`id` PRIMARY KEY, `builder_id` FOREIGN KEY, `review_id` FOREIGN KEY, `next_task_id`, `priority`, `difficulty`, `est_ai_effort`).
8. **`risk_register`**: Live tracking table for critical risks identified during verification (`id` PRIMARY KEY, `review_id` FOREIGN KEY, `risk_type`, `severity`, `status`).

---

## EXECUTIVE DASHBOARD API SPECIFICATION

The new dashboard router is mounted in [main.py](file:///g:/Live%20Task%20Review%20Agent%20-%202/main.py) and exposes the endpoints listed below under `/api/v1`:

### 1. Builder Quality
* **Route**: `GET /api/v1/dashboard/builder-quality`
* **Response Sample**:
  ```json
  {
    "builders": [
      {
        "builder_name": "Test_Builder",
        "total_reviews": 4,
        "passed_reviews": 3,
        "failed_reviews": 1,
        "average_score": 82.5,
        "pass_rate_percent": 75.0
      }
    ],
    "timestamp": "2026-06-23T12:00:00Z"
  }
  ```

### 2. Product Readiness
* **Route**: `GET /api/v1/dashboard/product-readiness`
* **Response Sample**:
  ```json
  {
    "products": [
      {
        "product_id": "prod-tantra",
        "product_name": "TANTRA Core",
        "certification_status": "READY",
        "readiness_score": 95,
        "certified_at": "2026-06-23T11:45:00Z"
      }
    ],
    "timestamp": "2026-06-23T12:00:00Z"
  }
  ```

### 3. Ecosystem Health
* **Route**: `GET /api/v1/dashboard/ecosystem-health`
* **Response Sample**:
  ```json
  {
    "status": "HEALTHY",
    "total_products": 12,
    "certified_products": 10,
    "certification_ratio": 83.33,
    "compliance_ratio_percent": 90.0,
    "active_tasks_count": 3,
    "unresolved_risks_count": 1,
    "timestamp": "2026-06-23T12:00:00Z"
  }
  ```

---

## ENVIRONMENT SETUP & DEPLOYMENT GUIDE

### Prerequisites
- Python 3.11+
- PostgreSQL database (or local file system for SQLite fallback)
- Dev packages defined in [requirements.txt](file:///g:/Live%20Task%20Review%20Agent%20-%202/requirements.txt)

### Environment Variables
Configure the following inside `.env`:
```env
# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/parikshak_db
# (Fallback to sqlite:///storage/parikshak.db if DATABASE_URL is not set)
```

### Database Migration Guide
To initialize or migrate the database schemas:
1. Run Alembic upgrade to apply migrations:
   ```bash
   alembic upgrade head
   ```
2. For testing, schema auto-creation will invoke programmatically if SQLite fallback is used.

### Execution Instructions
To start the FastAPI production server locally:
```bash
python main.py
```

---

## ROADMAP & KNOWN LIMITATIONS

1. **SQLite Concurrency**: When fallback mode is active, parallel writes might trigger minor sequential delays due to SQLite single-writer locking constraints. Use PostgreSQL in production environments.
2. **Hardcoded User Roles**: Corrective assignments default to assignee names defined in trace files. A mapping service should be integrated with an external IAM identity database in the next major update.

---

## BHIV CANDIDATE SUBMISSION VALIDATION

Parikshak has been evolved into the default first-stage reviewer for BHIV candidate submissions, handling end-to-end dataset intake, real automated evaluations, next-task recommendations, and ecosystem integration:

1. **Dataset Intake Module** ([dataset_intake.py](file:///g:/Live%20Task%20Review%20Agent%20-%202/evaluation_engine/dataset_intake.py)): Handles validation of required intake fields (assigned task, task document, review packet, repository/commit, dates, and evidence) and serializes the validated packets to `storage/traces/{trace_id}/intake_packet.json`.
2. **Production Review Pipeline** ([bhiv_review_engine.py](file:///g:/Live%20Task%20Review%20Agent%20-%202/evaluation_engine/bhiv_review_engine.py)): Executes the evaluation pipeline. Uses the Groq LLM API (`llama-3.3-70b-versatile`) to generate a structured executive-quality report with 8 mandatory fields. A deterministic rule-based fallback is implemented if the LLM API is rate-limited or unavailable.
3. **Next-Task Recommendation Engine** ([task_graph_engine.py](file:///g:/Live%20Task%20Review%20Agent%20-%202/task_selector/task_graph_engine.py)): Dynamically determines the next assignment using the state graph and provides architectural, ecosystem, and readiness justifications.
4. **Ecosystem Integrations** ([integration.py](file:///g:/Live%20Task%20Review%20Agent%20-%202/canonical_db/integration.py)): When reviews are human-approved through `/api/v1/review/approve`, the transaction is committed to the Gov-OS event journal, and propagated to the Saarthi visibility ledger, Niyantran assignments ledger, and the Pravah replay ledger ([pravah_replay.jsonl](file:///g:/Live%20Task%20Review%20Agent%20-%202/storage/pravah_replay.jsonl)) with full trace continuity.
5. **Executive Review Comparison** ([compare_reviews.py](file:///g:/Live%20Task%20Review%20Agent%20-%202/scripts/compare_reviews.py)): Automatically compares Parikshak automated reviews against manual human reviews ([final_gc_review.md](file:///g:/Live%20Task%20Review%20Agent%20-%202/review_packets/final_gc_review.md)) and writes the comparison to the report ([executive_comparison_report.md](file:///g:/Live%20Task%20Review%20Agent%20-%202/review_packets/executive_comparison_report.md)) detailing agreements, differences, and alignment score.
6. **Safety Gate Isolation**: Both `IntegrityValidator` and `BackupManager` now dynamically calculate their backup directories based on the SQLite file basename (e.g., `storage/backups/canonical_db`) if no path is provided. This isolates test environments from production backups and prevents `STARTUP_SAFETY_GATE_BLOCKED` validation errors.

---

## PHASE IV HARDENED PRODUCTION CERTIFICATION

In Phase IV, Parikshak has been hardened for production certification. The following mechanisms have been introduced:

### 1. Close Security Gate (Role-Based Access Control)
- **Role Enforcement**: Enforces strictly defined roles (`Governor`, `Reviewer`, `Operator`, `Read Only`) across all endpoints.
- **JWT Middleware**: Validates signatures, expiration (`Expired credentials` error), and role permissions.
- **Replay Attack Protection**: An in-memory token registry rejects duplicate approval token hashes with `409 Conflict` (`REPLAY_REJECT`).
- **Startup Secrets Validation**: Executes `validate_startup_secrets()` at boot time to block execution if insecure or default secret keys are configured.
- **Signed Governance Proofs**: Every override action persists `validation_decision.json` (signature, timestamp, version, signer details) and `governance_record.json` to the trace directory.

### 2. Executable Dependency Verification
- **Dynamic Scanner**: Resolves packages dynamically from the active runtime environment rather than static files.
- **Pinning & Normalization**: Verifies strict `==` pinning, checks version compatibility, detects circular dependencies, and filters out forbidden packages (`unverified_lib`, `unsafe_bridge_plugin`, `backdoor`). Normalizes package name hyphens and underscores (e.g., `pydantic-core` / `pydantic_core`).
- **SBOM Export**: Dynamically generates and writes a CycloneDX v1.5 compliant `sbom.json` containing version metadata and package checksums to the trace folder.
- **Verdict Enforcement**: Fails production certification if dependency validation fails.

### 3. Dataset Intake & Self-Certification
- **17 production fields**: Expanded dataset intake pipeline to support: *Assigned Task, Original Assignment Document, Repository Path, Repository Commit / Branch, Review Packet, Expected Deliverables, Candidate Name, Candidate Identifier, Submission Timestamp, Due Date, Supporting Evidence, Architecture Notes, Integration Notes, Runtime Evidence, Test Evidence, Documentation Evidence, and Additional Instructions*.
- **Backward Compatibility**: A custom Pydantic `@model_validator` maps older payloads cleanly without data loss.
- **Self-Certification Loop**: Full pipeline runs deterministically: Intake -> Evaluation -> Human Review Escalate -> human Override -> Gov-OS Commit -> Saarthi -> Bucket -> Pravah Replay -> Production Certification -> Evidence Export.

---

## PRODUCTION HANDOVER PACKETS & MANUALS

All operational handovers, rollback manuals, and evidence checklists are organized inside the repository:

### 1. Operations and Maintenance Manuals (Root)
* **Deployment Guide**: [DEPLOYMENT_GUIDE.md](file:///g:/Live%20Task%20Review%20Agent%20-%202/DEPLOYMENT_GUIDE.md)
* **Rollback Playbook**: [ROLLBACK_GUIDE.md](file:///g:/Live%20Task%20Review%20Agent%20-%202/ROLLBACK_GUIDE.md)
* **Disaster Recovery Guide**: [RECOVERY_GUIDE.md](file:///g:/Live%20Task%20Review%20Agent%20-%202/RECOVERY_GUIDE.md)
* **Operational Handbook**: [OPERATIONAL_HANDBOOK.md](file:///g:/Live%20Task%20Review%20Agent%20-%202/OPERATIONAL_HANDBOOK.md)

### 2. Code Review Packets (review_packets/code_review/)
* **Changed Files**: [changed_file_list.md](file:///g:/Live%20Task%20Review%20Agent%20-%202/review_packets/code_review/changed_file_list.md)
* **API Payload Specs**: [api_samples.md](file:///g:/Live%20Task%20Review%20Agent%20-%202/review_packets/code_review/api_samples.md)
* **Deployment Proof Logs**: [deployment_proof.md](file:///g:/Live%20Task%20Review%20Agent%20-%202/review_packets/code_review/deployment_proof.md)
* **Runtime Logging Traces**: [runtime_logs.md](file:///g:/Live%20Task%20Review%20Agent%20-%202/review_packets/code_review/runtime_logs.md)
* **Executive Dashboards**: [executive_screenshots.md](file:///g:/Live%20Task%20Review%20Agent%20-%202/review_packets/code_review/executive_screenshots.md)
* **Systems Reviewer Guide**: [reviewer_guide.md](file:///g:/Live%20Task%20Review%20Agent%20-%202/review_packets/code_review/reviewer_guide.md)
* **Manual Inspection Areas**: [files_requiring_manual_review.md](file:///g:/Live%20Task%20Review%20Agent%20-%202/review_packets/code_review/files_requiring_manual_review.md)
* **Ecosystem Checklist Matrix**: [production_evidence_checklist.md](file:///g:/Live%20Task%20Review%20Agent%20-%202/review_packets/code_review/production_evidence_checklist.md)




