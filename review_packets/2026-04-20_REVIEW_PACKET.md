# Parikshak Task Graph Integration - Review Packet

**Date:** 2026-04-20
**Prepared For:** Vinayak Tiwari / Structural Enforcement
**Status:** Live Testing Complete & Verified

## Overview
Parikshak is now live, usable, deterministic, and integrated directly into the `app/services/final_convergence.py` layer. All task generation intelligence has been replaced by strict DB mapping and exact graph traversal, ensuring canonical datasets accurately power user assignments.

## 1. Entry Point
- **`app/services/final_convergence.py`** -> `process_with_convergence()`
- Responsible for validating and orchestrating the task generation strictly utilizing Phase 1 to 4 engines, completely bypassing ML fallback inference or runtime ranking.

## 2. Core Flow
The strict deterministic flow is embedded as follows:
1. **Submission Generation**: The core properties (title, description, score) are extracted.
2. **Evaluation (Sri Satya)**: Evaluates whether a submission passes or fails numerically.
3. **Mandala Mapping**: `/engine/mandala_mapper.py` derives Layer, Subsystem, Capability and Product STRICTLY from `/db/mandala.json`.
4. **DB Lookup**: The specific task definition is resolved locally from `/db/niyantran_tasks.json`.
5. **Task Graph Traversal**: `/engine/task_graph_engine.py` is invoked with score input and active context.
6. **Task Selection**: The next exact deterministically resolved `next_task_id` is computed.
7. **Output Emission**: Graph result is packaged with deterministic traces, bypassing Shraddha fallback emergencies.

## 3. Database Structure
### `db/mandala.json`
- **Purpose:** Central taxonomy that binds all tasks to explicit product hierarchies.
- **Rules:** No text-based drift; capability resolution depends entirely on exact mapping combinations derived from incoming descriptions.
- **Levels Defined:** `product`, `layer`, `subsystem`, `capability`.

### `db/niyantran_tasks.json`
- **Purpose:** Strict capability to next-hop state machine implementation.
- **Fields:** `task_id`, `product`, `layer`, `subsystem`, `capability`, `prerequisites[]`, `next_tasks[]`, `failure_tasks[]`, `completion_signals[]`, `dharma`.
- **Content:** Holds fully deterministic definitions for advancement scenarios alongside regression fail-safe paths.

## 4. Graph Logic
The graph execution sits in `/engine/task_graph_engine.py`:
```python
def resolve_next_task(self, current_task_id: str, score: float) -> str:
    # Deterministic mapping
    score >= 6 -> task["next_tasks"][0]
    score < 6  -> task["failure_tasks"][0]
```
- **Rules Followed:** ABSOLUTELY NO LLM inference. ABSOLUTELY NO probability-based routing.

## 5. Real Outputs (Local Live Trace)
Below are condensed fragments demonstrating successful pipeline execution:

### Case 1: PASS (Score >= 6)
```json
{
  "next_task_id": "T-GOV-002",
  "task_type": "advancement",
  "title": "Task Modification",
  "difficulty": "intermediate",
  "objective": "Adapt dynamically.",
  "product": "Niyantran",
  "layer": "Governance",
  "subsystem": "Task Review Engine",
  "capability": "Submission Evaluation",
  "selection_reason": "Score is 8.5. Proceeding to next task.",
  "source": "task_graph"
}
```

### Case 2: FAIL (Score < 6)
```json
{
  "next_task_id": "T-COR-F01",
  "task_type": "correction",
  "title": "Relational Storage",
  "difficulty": "intermediate",
  "objective": "Data resilience.",
  "product": "Niyantran",
  "layer": "Core",
  "subsystem": "Database",
  "capability": "Relational Storage",
  "selection_reason": "Score is 4.0. Proceeding to failure recovery task.",
  "source": "task_graph"
}
```

### Case 3: EDGE (Unknown Mapping Reject & Recovery)
When an unknown mapping enters, it triggers the fallback to `"Unknown"` strict types via the fail-safe and logs:
```
[FINAL CONVERGENCE] Mandala mapping failed: HARD REJECT: Task could not be mapped to Mandala capabilities.
```
This forces the system back to boundary foundational bounds or manual escalation.

## Validation Status
Testing metrics confirmed the task was finalized with deterministic integrity. Task paths mapped cleanly. No intelligence layer was queried for structural navigation.

- [x] Mandala DB Populated
- [x] Tasks DB Graph Initialized
- [x] Engine / Mapper Installed
- [x] Convergence Core Wired
- [x] Vinayak Tiwari Testing Protocols Ready
