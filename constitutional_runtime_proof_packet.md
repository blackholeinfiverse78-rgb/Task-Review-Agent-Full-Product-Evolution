# Constitutional Review Runtime Proof Packet

This proof packet demonstrates the runtime execution of the **Constitutional Review Engine** verifying trace readiness.

---

## 1. Trace ID Integration Verification

The engine was run against trace IDs in three distinct states: `READY`, `NEEDS_REVIEW`, and `REJECTED`.

### A. Successful Case (READY)
*   **Trace ID**: `trace-ready-case`
*   **Verdict**: `READY`
*   **Reconstructable**: `True`
*   **Valid**: `True`
*   **Reconstruction Confidence**: `1.0`

#### Verification Output Report:
```json
{
    "trace_id": "trace-ready-case",
    "verdict": "READY",
    "reconstructable": true,
    "valid": true,
    "reasons": [],
    "reconstruction_report": {
        "trace_id": "trace-ready-case",
        "reconstructable": true,
        "missing_artifacts": [],
        "confidence": 1.0,
        "reconstruction_path": {
            "Execution": true,
            "Evidence": true,
            "Governance": true,
            "Consumption": true,
            "Actions": true,
            "Lineage": true,
            "Replay": true,
            "Convergence": true,
            "Final Status": true
        }
    },
    "validation_report": {
        "trace_id": "trace-ready-case",
        "valid": true,
        "layers": {
            "evidence": {
                "valid": true,
                "errors": [],
                "warnings": []
            },
            "governance": {
                "valid": true,
                "errors": [],
                "warnings": []
            },
            "replay": {
                "valid": true,
                "errors": [],
                "warnings": []
            },
            "convergence": {
                "valid": true,
                "errors": [],
                "warnings": []
            }
        },
        "errors": []
    },
    "timestamp": "2026-07-03T08:06:53.889721Z"
}
```

---

### B. Borderline Case (NEEDS_REVIEW)
*   **Trace ID**: `trace-needs-review-case`
*   **Verdict**: `NEEDS_REVIEW`
*   **Reconstructable**: `True`
*   **Valid**: `True`
*   **Reconstruction Confidence**: `0.9`

#### Verification Output Report:
```json
{
    "trace_id": "trace-needs-review-case",
    "verdict": "NEEDS_REVIEW",
    "reconstructable": true,
    "valid": true,
    "reasons": [
        "Missing optional artifacts: ['handover_bundle.json']"
    ],
    "reconstruction_report": {
        "trace_id": "trace-needs-review-case",
        "reconstructable": true,
        "missing_artifacts": [
            "handover_bundle.json"
        ],
        "confidence": 0.9,
        "reconstruction_path": {
            "Execution": true,
            "Evidence": true,
            "Governance": true,
            "Consumption": false,
            "Actions": true,
            "Lineage": true,
            "Replay": true,
            "Convergence": true,
            "Final Status": true
        }
    },
    "validation_report": {
        "trace_id": "trace-needs-review-case",
        "valid": true,
        "layers": {
            "evidence": {
                "valid": true,
                "errors": [],
                "warnings": []
            },
            "governance": {
                "valid": true,
                "errors": [],
                "warnings": []
            },
            "replay": {
                "valid": true,
                "errors": [],
                "warnings": []
            },
            "convergence": {
                "valid": true,
                "errors": [],
                "warnings": []
            }
        },
        "errors": []
    },
    "timestamp": "2026-07-03T08:06:53.921778Z"
}
```

---

### C. Rejected Case (REJECTED)
*   **Trace ID**: `trace-rejected-replay-case`
*   **Verdict**: `REJECTED`
*   **Reconstructable**: `True`
*   **Valid**: `False`

#### Verification Output Report:
```json
{
    "trace_id": "trace-rejected-replay-case",
    "verdict": "REJECTED",
    "reconstructable": true,
    "valid": false,
    "reasons": [
        "Replay logs contain error markers: ['[ERROR]']",
        "Integrity validation failed in one or more layers.",
        "Replay status indicates FAILURE."
    ],
    "reconstruction_report": {
        "trace_id": "trace-rejected-replay-case",
        "reconstructable": true,
        "missing_artifacts": [],
        "confidence": 1.0,
        "reconstruction_path": {
            "Execution": true,
            "Evidence": true,
            "Governance": true,
            "Consumption": true,
            "Actions": true,
            "Lineage": true,
            "Replay": true,
            "Convergence": true,
            "Final Status": true
        }
    },
    "validation_report": {
        "trace_id": "trace-rejected-replay-case",
        "valid": false,
        "layers": {
            "evidence": {
                "valid": true,
                "errors": [],
                "warnings": []
            },
            "governance": {
                "valid": true,
                "errors": [],
                "warnings": []
            },
            "replay": {
                "valid": false,
                "errors": [
                    "Replay status indicates FAILURE."
                ],
                "warnings": [
                    "Replay logs contain error markers: ['[ERROR]']"
                ]
            },
            "convergence": {
                "valid": true,
                "errors": [],
                "warnings": []
            }
        },
        "errors": [
            "Replay status indicates FAILURE."
        ]
    },
    "timestamp": "2026-07-03T08:06:53.933889Z"
}
```

---

## 2. Reviewer Independence Proof
Using only the `trace_id` at runtime, the engine is fully capable of:
1. Locating the exact storage directories.
2. Checking presence and integrity of Pratham evidence, Ansh governance signatures, and TANTRA convergence registries.
3. Rendering a final verdict without relying on developer assertions.
