# DETERMINISTIC API MAP

## 1. Production Injection
`POST /api/v1/production/niyantran/submit`
**Purpose**: Single entry point for tasks coming from Niyantran.
**Enforcement**: Requires trace_id. ReturnsQUEUED status. Never auto-approves.

## 2. Constitutional Governance Layer
`POST /api/v1/review/approve`
**Purpose**: Transition state to APPROVED. Releases assignment.
**Enforcement**: Requires PENDING_REVIEW state. Idempotent block on re-approvals. Requires `expected_version` for OCC locking.

`POST /api/v1/review/reject`
**Purpose**: Transition state to REJECTED.
**Enforcement**: Requires PENDING_REVIEW state. Requires `expected_version` for OCC locking.

`POST /api/v1/review/modify`
**Purpose**: Adjust bounded metadata ONLY.
**Enforcement**: Dual-approval needed (authorizer + operator). Requires `expected_version` for OCC locking.

## 3. Observability & Replay
`GET /api/v1/review/pending`
**Purpose**: Fetch queue for operator dashboard.

`GET /api/v1/production/system/metrics`
**Purpose**: Core determinism metrics.

`GET /api/v1/production/bucket/evaluation/{trace_id}`
**Purpose**: Fetch historical trace reconstruction.
