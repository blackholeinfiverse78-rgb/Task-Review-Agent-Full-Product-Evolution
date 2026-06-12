# Escalation Contract (Human-in-Loop Escalation Contract)

- **Version**: 1.0.0
- **Status**: FROZEN / CORE-LOCKED
- **Ownership Boundary**: Owned by `task_selector/human_in_loop.py`.

---

## 1. Purpose
Enforces the safety bounds for automated grading. If the system's confidence in a submission is low (confidence score `< 0.98`), it halts autonomous releases, raises an escalation case, and stages the record as `PENDING_REVIEW` in `storage/escalations` until an authorized human governor signs off on an override or confirmation.

---

## 2. Hardened Confidence Formula
The confidence calculation is purely deterministic and derived from physical evidence:

$$\text{confidence} = \frac{\text{proof} + \text{architecture} + \text{code} + \text{rubric\_completeness}}{4}$$

Where:
- $\text{proof} = \text{pac.proof} \in \{0, 1\}$
- $\text{architecture} = \text{pac.architecture} \in \{0, 1\}$
- $\text{code} = \text{pac.code} \in \{0, 1\}$
- $\text{rubric\_completeness} = \frac{\text{rubric\_sum}}{6} \in [0.0, 1.0]$
- $\text{rubric\_sum} = Q_{\text{proof}} + Q_{\text{architecture}} + Q_{\text{code}} + \text{has\_alignment} + \text{has\_authenticity} + \text{has\_effort}$ (each element $\in \{0, 1\}$)

---

## 3. Inputs
The escalation service consumes the evaluator pipeline outputs:

| Field | Location | Type | Range / Constraints | Description |
| :--- | :--- | :--- | :--- | :--- |
| `pac.proof` | `evaluation_result` | Integer | $\{0, 1\}$ | Presence of README/tests |
| `pac.architecture` | `evaluation_result` | Integer | $\{0, 1\}$ | Presence of modular directories |
| `pac.code` | `evaluation_result` | Integer | $\{0, 1\}$ | Presence of actual source files |
| `rubric` fields | `evaluation_result` | Integers | $\{0, 1\}$ | Six structural binary checkers |
| `trace_id` | Metadata | String | Min 8 chars | Monotonic trace ID |

---

## 4. Outputs
Returns the calculated metrics and stages an escalation case if thresholds are violated.

### 4.1 ConfidenceMetrics Output
```json
{
  "base_confidence": 0.5833,
  "final_confidence": 0.5833,
  "proof_consistency": 0.0,
  "signal_alignment": 1.0,
  "decision_clarity": 1.0,
  "evidence_strength": 0.3333,
  "requires_escalation": true,
  "escalation_reasons": ["low_confidence", "no_proof", "low_rubric_completeness"]
}
```

### 4.2 Escalation Case In-Memory & On-Disk Representation
If `requires_escalation` is `true`, an escalation case file is persisted at `storage/escalations/{case_id}.json`:
```json
{
  "case_id": "esc-20260612140000-tracea3f2c1d4",
  "trace_id": "trace-a3f2c1d48b9e4f2a",
  "timestamp": "2026-06-12T08:30:00Z",
  "reason": "low_confidence",
  "confidence": 0.5833,
  "original_evaluation": { ... },
  "original_decision": { ... },
  "status": "pending",
  "assigned_reviewer": null,
  "review_notes": null,
  "human_override": null,
  "resolved_at": null
}
```

---

## 5. Failure States & Boundaries
- **System Restarts**: Escalations are persisted immediately to disk. On reboot, all `pending` cases are reloaded into memory, ensuring zero review loss.
- **Trigger Violation**: If an external caller attempts to mutate a case directly by writing to the `storage/escalations` directory, validation at runtime will fail if the structure does not match the strict schema.

---

## 6. Versioning Rules
- **Threshold Policy**: Bumping the confidence threshold (e.g. from `0.98` to `0.99`) requires minor release updates. Bumping the component weights requires major releases.

---

## 7. Ownership Boundary
- **Parikshak Ownership**: Computing confidence, generating the escalation ID, storing the case JSON, and preventing release propagation until status resolves.
- **Consumer Ownership**: Consumers cannot directly close, modify, or create escalation cases. They can only poll the pending queue or register callback webhooks to receive notification of resolutions.
