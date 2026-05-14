# TANTRA UNIFIED INFRASTRUCTURE — OWNERSHIP BOUNDARIES

## 1. /evaluation_engine
**Owner:** Sri Satya
**Domain:** Deterministic extraction of intent, rules, and signals.
**Boundary:** Maps raw input to 4 binary fields (schema, completeness, logic, semantic_match).
**Prohibited:** Cannot alter state, route tasks, or make business decisions.

## 2. /task_selector
**Owner:** Parikshak Traversal Engine
**Domain:** Deterministic graph traversal based on evaluation results.
**Boundary:** Accepts evaluation_result and failure_type. Outputs exactly one selected_task_id or FAILS.
**Prohibited:** Cannot evaluate input, cannot guess, cannot fallback.

## 3. /governance_layer
**Owner:** Human-in-the-Loop Authority
**Domain:** Constitutional approval and state transition.
**Boundary:** Only point in the system that can transition a submission from PENDING_REVIEW to APPROVED/REJECTED.
**Prohibited:** Cannot modify evaluation or graph traversal.

## 4. /replay_audit
**Owner:** Operations & Observability
**Domain:** Deterministic reconstruction of system state.
**Boundary:** Append-only log of critical state transitions and system boundaries.
**Prohibited:** Cannot modify operational DB or interfere with execution.

## 5. /contracts
**Owner:** TANTRA Core Protocol
**Domain:** Unbreakable schemas and DTOs shared across modules.
**Boundary:** Single source of truth for Request/Response boundaries.
**Prohibited:** Cannot contain business logic.

## 6. /db
**Owner:** Persistence Layer
**Domain:** Immutable storage of facts, definitions, and states.

## 7. /api
**Owner:** Integration Boundary
**Domain:** Rest API endpoints.

## 8. /observability
**Owner:** System Monitoring
**Domain:** Metrics, dashboarding, system health checks.
