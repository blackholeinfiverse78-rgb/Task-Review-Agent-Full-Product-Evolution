# Merge Summary — Parikshak TANTRA Convergence

**Date:** 2026-05-28
**Version:** v6.0.0

---

## Persistence Layer Convergence

Two persistence layers exist by design — they are NOT duplicates:

| Layer | Location | Purpose | Mutability |
|---|---|---|---|
| ProductStorage | `db/persistent_storage.py` | Operational read-model for API/dashboard | Append + evict (1000 limit) |
| Gov-OS Journal | `canonical_db/db.py` | Governed audit log, replay source of truth | Append-only, trigger-locked |

These layers are unified by `trace_id` — every ProductStorage record carries the same `trace_id` as its corresponding Gov-OS journal event. Replay reconstruction from the journal produces the same state as ProductStorage.

## Changes Made

### canonical_db/integration.py
- Removed all mock data (`mock_eval`, `mock_signals`, `mock_task_data`)
- `propagate_governed_approval()` now accepts real `eval_output`, `supporting_signals`, `graph_result`, `task_data`
- Backward-compatible: if real signals not provided, derives minimal bucket entry from envelope payload

### task_selector/task_graph_engine.py
- Added `COMPLETED` terminal state handling — no longer raises `GRAPH_HARD_REJECT` on lifecycle completion
- `COMPLETED` returns `selected_task_id=COMPLETED` with `selection_reason` documenting terminal state

### canonical_db/ingestion_pipeline.py (new)
- Governed ingestion pipeline for owner-provided historical data
- Validates all entries against `ENTITY_SCHEMAS` before committing any
- Preserves original timestamps, lineage references, reasoning
- Generates ingestion template for owner to fill with real data

## Schema Diff

No schema changes. `ENTITY_SCHEMAS` is frozen. All 9 entity types unchanged:
- `candidate_profiles`, `task_lineage`, `review_history`, `assignment_history`
- `reasoning_artifacts`, `ecosystem_dependency_context`, `product_mapping`
- `strategic_notes`, `learning_signals`

## Trace Lineage Continuity

Every event in the Gov-OS journal carries:
- `trace_id` — upstream Niyantran trace, never regenerated
- `lineage_reference` — pointer to parent trace or ingestion lineage
- `parent_event_hash` — SHA-256 chain link to previous event

Replay reconstruction from any sequence point produces identical state.
