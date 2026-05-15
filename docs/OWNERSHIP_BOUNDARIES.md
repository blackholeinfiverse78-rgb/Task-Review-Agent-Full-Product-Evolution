# TANTRA UNIFIED INFRASTRUCTURE — OWNERSHIP BOUNDARIES

## 1. /evaluation_engine
**Owner:** Sri Satya
**Domain:** deterministic evaluation only
**Boundary:** Maps raw input to binary fields. Emits a strict 8-field evaluation contract.
**Prohibited:** Cannot alter state, route tasks, or make business decisions. Cannot inject replay metadata.

## 2. /task_selector
**Owner:** Parikshak Traversal Engine
**Domain:** deterministic traversal only
**Boundary:** Accepts evaluation_result and failure_type. Outputs exactly one selected_task_id or FAILS.
**Prohibited:** Cannot evaluate input, cannot guess, cannot fallback.

## 3. /governance_layer
**Owner:** Human-in-the-Loop Authority
**Domain:** bounded human approval only
**Boundary:** Enforces irreversible states and OCC locks. Only point in the system that can transition a submission from PENDING_REVIEW to APPROVED/REJECTED.
**Prohibited:** Cannot modify evaluation or graph traversal.

## 4. /replay_audit
**Owner:** Operations & Observability
**Domain:** replay lineage + forensic integrity
**Boundary:** Exclusively owns replay metadata (`event_type`, `parent_event_hash`, `replay_checkpoint_id`, `expected_version`). Uses append-only atomic persistence with fsync durability.
**Prohibited:** Cannot modify operational DB or interfere with execution.

## 5. /observability
**Owner:** System Monitoring
**Domain:** structured operational visibility
**Boundary:** Metrics, dashboarding, system health checks.
**Prohibited:** Cannot modify state.

## 6. /contracts
**Owner:** TANTRA Core Protocol
**Domain:** Unbreakable schemas and DTOs shared across modules (e.g., 8-field Evaluation Contract).

## 7. /db
**Owner:** Persistence Layer
**Domain:** Immutable storage of facts, definitions, and states. Uses checksum continuity and corruption isolation.
