# Assignment Contract (Routing Contract)

- **Version**: 1.0.0
- **Status**: FROZEN / CORE-LOCKED
- **Ownership Boundary**: Owned by `task_selector/task_selection_engine.py`.

---

## 1. Purpose
Defines the boundary and interface specifications for next-task selection. Based on the evaluation outcome of a submission, the system deterministically traverses the task graph to select a follow-up task (advancement, reinforcement, or correction). No tasks are dynamically created; only defined tasks from the frozen database registry are selected.

---

## 2. Inputs
Inputs are generated internally by the evaluation engine or provided programmatically to the assignment engine:

| Field | Type | Required | Constraints | Description |
| :--- | :--- | :--- | :--- | :--- |
| `score_10` | Float | Yes | `0.0` to `10.0` | Ingestion score mapping |
| `decision` | String | Yes | `"APPROVED"` or `"REJECTED"` | Evaluator decision output |
| `current_difficulty`| String | No | Default: `"beginner"` | Difficulty of current task (beginner, intermediate, advanced) |
| `product_context` | Dict | No | Default: `None` | Optional Mandala Mapper product/layer context |

### product_context Object Structure
```json
{
  "product": "Niyantran",
  "layer": "API Gateway",
  "allowed_next_tasks": ["NT-ADV-I-001", "NT-ADV-I-002"]
}
```

---

## 3. Outputs
Returns the deterministic assignment object:

| Field | Type | Description |
| :--- | :--- | :--- |
| `next_task_id` | String | Deterministic follow-up task identifier |
| `title` | String | Human-readable title of assigned task |
| `task_type` | String | `"advancement"` \| `"reinforcement"` \| `"correction"` |
| `difficulty` | String | Target difficulty level |
| `selection_reason` | String | Explainable trace of rule matching |
| `source` | String | Static value: `"niyantran_task_graph"` |
| `product` | String | Inherited from `product_context` or `"unknown"` |
| `layer` | String | Inherited from `product_context` or `"unknown"` |
| `context_source` | String | `"product_context"` \| `"graph_fallback"` \| `"graph_only"` |

### Sample Output Payload
```json
{
  "next_task_id": "NT-ADV-I-001",
  "title": "Advanced Microservices Implementation",
  "task_type": "advancement",
  "difficulty": "advanced",
  "selection_reason": "score=9.5/10 -> approved | difficulty=intermediate | graph_key=('approved', 'intermediate') | product=Niyantran layer=API Gateway context_match=NT-ADV-I-001",
  "source": "niyantran_task_graph",
  "decision_band": "approved",
  "difficulty_band": "intermediate",
  "product": "Niyantran",
  "layer": "API Gateway",
  "context_source": "product_context"
}
```

---

## 4. Failure States
All graph lookup errors fall back to safe defaults rather than crashing the system.

### 4.1 Missing/Invalid Key Fallback
If the combination of `(decision_band, difficulty_band)` is not mapped in `NIYANTRAN_TASK_GRAPH`, it defaults to the correction path:
- **Fallback Selection Key**: `("rejected_fail", "beginner")`
- **Assigned Task**: `NT-COR-B-001` (Foundational Implementation Correction)
- **Selection Reason**: `"Fallback selection — no graph entry for (decision_band, difficulty_band)"`

---

## 5. Versioning Rules
- **Schema Key**: Implicit in registry. Bumping difficulty mapping or adding bands requires minor version increments.
- **Compatibility**: If a new difficulty band (e.g., `"expert"`) is introduced, older engines normalise it to `"advanced"` to preserve compatibility.

---

## 6. Compatibility Rules
- If a consumer sends a custom `task_id` override that does not exist in `TASK_METADATA`, the system returns a validation failure (`validate_task_id(task_id)` is `False`).

---

## 7. Ownership Boundary
- **Parikshak Boundary**: Maps scores and decisions to fixed bands and selects pre-defined tasks.
- **Consumer Boundary**: External products must accept the returned task ID and register task metadata in their own UI flows.
