# PARIKSHAK HISTORICAL REPLAY FRAMEWORK (V1)

This framework defines the methodology and pipeline to evaluate Parikshak against historical human decisions. The goal is to run Parikshak's Common Core rule sets against real candidate submissions, comparing automated recommendations with historical ground truth outcomes to calibrate engine parameters.

---

## 1. Replay Architecture & Pipeline Flow

The replay pipeline utilizes the immutable event logs to reconstruct state and replay decisions.

```
+-------------------------------------------------------------+
|                Historical Calibration DB                    |
| (Raw Submissions, Task Descriptions, Historical Decisions) |
+------------------------------+------------------------------+
                               |
                               v
+------------------------------v------------------------------+
|                    Replay Engine Runner                     |
|                                                             |
|  1. Reconstruct db state to seq_id                          |
|  2. Crawl historical repository tree                        |
|  3. Run Ingest -> Signal Extraction -> Rule Engine          |
|  4. Generate predicted score, decision, & next_task_id      |
+------------------------------+------------------------------+
                               |
                               v
+------------------------------v------------------------------+
|                  Comparison & Scoring Unit                  |
|                                                             |
|  Compare: predicted vs. historical human decision            |
|  Classify: Correct / Partial / False Pos / False Neg         |
+------------------------------+------------------------------+
                               |
                               v
+------------------------------v------------------------------+
|                 Evaluation Metrics Report                   |
| (Accuracy, Recall, Precision, Confidence Calibration Curve) |
+-------------------------------------------------------------+
```

---

## 2. Replay Classification Metrics

The framework compares the **Parikshak Recommendation** ($P$) against the **Historical Human Decision** ($H$):

| Classification | Condition | Description | Severity / Action |
|---|---|---|---|
| **Correct Match** | $P.decision == H.decision$ AND $P.failure\_type == H.failure\_type$ | Parikshak outcome matches human decision and matches the exact failure reason. | **Ideal Outcome**. High weight. |
| **Partial Match** | $P.decision == H.decision$ AND $P.failure\_type \neq H.failure\_type$ | Decision matches (e.g. FAIL/FAIL), but reason differs (e.g. machine: `incomplete`, human: `incorrect_logic`). | **Minor Drift**. Needs rubric calibration. |
| **False Positive** (Dangerous) | $P.decision == PASS$ AND $H.decision == REJECT$ | Machine passes a submission that a human judge rejected. | **Critical Defect**. Risk of bad placement. |
| **False Negative** (Inefficient) | $P.decision == FAIL$ AND $H.decision == ACCEPT$ | Machine rejects a submission that a human judge approved. | **Moderate Defect**. Increases reviewer queue. |

### 2.1 Confidence Accuracy (Calibration Metrics)
Let $C \in [0, 1]$ be the computed machine confidence. The framework measures:
*   **Override Rate at Confidence Bands**: The ratio of human overrides in bins (e.g., $C \in [0.98, 1.0]$ vs. $C \in [0.8, 0.98]$).
*   **Expected Calibration Error (ECE)**: Measures the discrepancy between predicted confidence and historical match rates. We want confidence to align with likelihood of matching human decisions.

---

## 3. Replay Runner Implementation (Conceptual Python API)

```python
import dataclasses
from typing import Dict, Any, List

@dataclasses.dataclass
class ReplayResult:
    trace_id: str
    historical_decision: str
    historical_failure_type: str
    predicted_decision: str
    predicted_failure_type: str
    predicted_confidence: float
    match_category: str  # CORRECT, PARTIAL, FALSE_POSITIVE, FALSE_NEGATIVE

class ReplayValidationEngine:
    def __init__(self, rule_engine, db_connection):
        self.rule_engine = rule_engine
        self.db = db_connection

    def run_replay(self, start_time, end_time) -> List[ReplayResult]:
        # Fetch real historical data from calibration DB
        submissions = self.db.get_submissions_in_range(start_time, end_time)
        results = []

        for sub in submissions:
            # 1. Reconstruct repository signals
            signals = self.reconstruct_signals(sub)
            
            # 2. Execute Rule Engine
            eval_output = self.rule_engine.evaluate(signals)
            
            # 3. Compute Confidence
            confidence = self.calculate_confidence(eval_output, signals)
            
            # 4. Compare with Historical Ground Truth
            historical_decision = self.db.get_historical_decision(sub["submission_id"])
            predicted_decision = "APPROVED" if eval_output["evaluation_result"] == "PASS" else "REJECTED"
            
            predicted_fail_type = eval_output.get("failure_type")
            hist_fail_type = historical_decision.get("failure_type")
            hist_dec_val = historical_decision.get("decision") # APPROVED / REJECTED
            
            # Classification Logic
            if predicted_decision == hist_dec_val:
                if predicted_fail_type == hist_fail_type:
                    category = "CORRECT"
                else:
                    category = "PARTIAL"
            elif predicted_decision == "APPROVED" and hist_dec_val == "REJECTED":
                category = "FALSE_POSITIVE"
            else:
                category = "FALSE_NEGATIVE"
                
            results.append(ReplayResult(
                trace_id=sub["trace_id"],
                historical_decision=hist_dec_val,
                historical_failure_type=hist_fail_type,
                predicted_decision=predicted_decision,
                predicted_failure_type=predicted_fail_type,
                predicted_confidence=confidence,
                match_category=category
            ))
            
        return results

    def calculate_confidence(self, eval_output: Dict, signals: Dict) -> float:
        pac = eval_output.get("pac", {})
        rubric = eval_output.get("rubric", {})
        
        proof = pac.get("proof", 0)
        arch = pac.get("architecture", 0)
        code = pac.get("code", 0)
        
        rubric_sum = (
            rubric.get("has_alignment", 0) +
            rubric.get("has_effort", 0) +
            rubric.get("has_code", 0)
        )
        
        # Calculate rubric completeness scaled to [0.0, 1.0] (3 sub-elements here)
        rubric_completeness = rubric_sum / 3.0
        
        return (proof + arch + code + rubric_completeness) / 4.0
```

---

## 4. Replay Validation and Calibration Rules

1.  **State Isolation**: Replays must run in a read-only sandboxed database state. Replay runners are blocked from appending records to the production SQLite `events` ledger.
2.  **Calibration Iterations**: If the False Positive rate exceeds $1.0\%$, the Calibration Engine triggers a parameter adjustments phase to tighten rule conditions (e.g., increasing `min_delivery_ratio` to $0.7$).
3.  **Baseline Regressions Check**: Any change in rule configuration must undergo a full replay run over the historical baseline to ensure that a correction in one rule does not degrade performance elsewhere.
