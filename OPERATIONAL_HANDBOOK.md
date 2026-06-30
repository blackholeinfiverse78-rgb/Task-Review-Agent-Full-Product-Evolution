# Parikshak Operational Handbook

This handbook provides instructions for ongoing monitoring, log analysis, and system maintenance of the Parikshak platform in production.

---

## 1. Observability and Monitoring

### Health Checks
The system exposes a standard health check endpoint that does not require authorization:
* **Endpoint**: `GET /health`
* **Response**: `{"status": "healthy", "version": "1.1.0"}`

---

## 2. Telemetry and Dashboard Metrics

The system calculates metrics dynamically from sqlite records. The executive dashboards can be consumed at:

### A. Builder Quality Overview
* **Route**: `/api/v1/dashboard/builder-quality`
* **Purpose**: Tracks pass/fail rates and quality averages per engineer.

### B. Product Readiness Status
* **Route**: `/api/v1/dashboard/product-readiness`
* **Purpose**: Lists products, scores, and active TANTRA statuses.

### C. Ecosystem Health Metrics
* **Route**: `/api/v1/dashboard/ecosystem-health`
* **Purpose**: General compliance rates and count of open risks.

---

## 3. Log Locations & Analysis

All core system logs write to stdout/stderr and sync to file handles inside the `storage/` directory:

* **Audit Logs**: `storage/audit_logs/audit_YYYY-MM-DD.jsonl` (detailed state transitions and action journals).
* **Ingested Traces**: `storage/traces/{trace_id}/` (ingested artifacts and evaluation packets).
* **Bucket logs**: `storage/bucket_logs/evaluation_index.jsonl` (provenance audit trails).
* **Niyantran assignments**: `storage/niyantran_assignments.jsonl` (training task dispatches).
* **Pravah replay**: `storage/pravah_replay.jsonl` (lineage and replay sequences).
