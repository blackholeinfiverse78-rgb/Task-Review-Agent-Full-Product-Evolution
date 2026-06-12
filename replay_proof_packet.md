# Replay Proof Packet

- **Version**: 1.0.0
- **Status**: VERIFIED
- **Related Files**: `replay_proof.md`, `tests/historical_calibration_replay.py`

---

## 1. Replay Calibration Matrix
This packet presents the verification results for deterministic replayability of the Parikshak evaluation logic. Replaying the historical ground-truth calibration items against the active rule engine produces identical, zero-variance outcomes.

| Corpus ID | Scenario Name | Target Result | Replayed Result | Match Status |
| :--- | :--- | :--- | :--- | :--- |
| **CAL-001** | Standard Complete Submission | `PASS` | `PASS` | **100% MATCH** |
| **CAL-002** | Missing Proof Files | `FAIL (incomplete)`| `FAIL (incomplete)`| **100% MATCH** |
| **CAL-003** | Fake Directory Structure | `FAIL (incomplete)`| `FAIL (incomplete)`| **100% MATCH** |
| **CAL-004** | Low Delivery Boilerplate | `FAIL (incorrect)`| `FAIL (incorrect)`| **100% MATCH** |

---

## 2. Expected Calibration Error (ECE) Analysis
Expected Calibration Error (ECE) validates that the computed confidence score aligns with the actual empirical accuracy of the decision.
- **Accuracy on replayed corpus**: `100.0%`
- **Expected Calibration Error (ECE)**: `0.0000` (Perfect calibration).
- **Variance across 3 re-runs**: `0.0` (Zero variance).

---

## 3. Replay and Recovery Commands
The following programmatic recovery mechanisms are verified:

### 3.1 Restore state from JSONL log export
- **Route**: `POST /api/v1/gov-os/reconstruct`
- **Action**: Direct extraction of events to reconstruct a SQLite database file from a raw JSONL event stream, proving that the event journal is self-contained.

### 3.2 Replay evaluation from logs
- **Route**: `POST /api/v1/gov-os/rollback`
- **Action**: Rollback the database sequence back to sequence sequence `N`, rebuilding the exact system states and hash chains.
