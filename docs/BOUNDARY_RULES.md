# Parikshak — Boundary Rules (Locked)

**Version**: 2.0.0 | **Status**: Governance-Locked | **Last Updated**: 2026

This document is the authoritative record of all architectural boundaries enforced in Parikshak.
It documents what was removed, what was locked, and what is enforced at runtime.

---

## 1. Scoring Authority Lock

| Rule | Enforcement | File |
|------|-------------|------|
| Assignment Engine = ONLY scoring authority | No other service may produce a score | `assignment_engine.py` |
| No parallel scoring paths | Single sequential pipeline only | `final_convergence.py` |
| Signal Engine = SUPPORTING ONLY | `can_determine_score = False` enforced | `signal_engine.py` |
| No heuristic shortcuts | All scoring is binary (0/1) rubric + exact formula | `assignment_engine.py` |

**What was removed:**
- `evaluation_engine.py` — parallel evaluation authority (deleted)
- `scoring_engine.py` — parallel scoring system (deleted)
- `assignment_authority.py` — duplicate authority (deleted)
- `_generate_next_task()` from `assignment_engine.py` — task generation removed from scoring engine

---

## 2. No Learning / No Adaptive Logic

| Rule | Enforcement |
|------|-------------|
| No RL hooks | No reinforcement learning imports or callbacks anywhere |
| No adaptive scoring | Scoring weights are compile-time constants, never updated at runtime |
| No model training | No ML model loading, training, or inference |
| No feedback loops | Bucket logs are write-only from evaluation perspective |

**Verification:** `grep -r "sklearn\|torch\|tensorflow\|keras\|rl\|reinforce\|adaptive" app/` returns zero results.

---

## 3. Confidence Formula (Hardened — Phase 3)

The confidence formula is **deterministic, auditable, and reproducible**:

```
confidence = (proof + architecture + code + rubric_completeness) / 4

Where:
  proof               = pac.proof          ∈ {0, 1}
  architecture        = pac.architecture   ∈ {0, 1}
  code                = pac.code           ∈ {0, 1}
  rubric_completeness = rubric_sum / 6     ∈ [0.0, 1.0]
  rubric_sum          = Q_proof + Q_architecture + Q_code
                      + alignment_score + authenticity_score + effort_score

Result: confidence ∈ [0.0, 1.0]
Threshold: 0.98
Action: confidence < 0.98 → escalation case created + persisted to disk
```

**What was removed:**
- `_calculate_quality_adjustment()` — heuristic grade-based adjustment
- `_calculate_pac_adjustment()` — heuristic PAC keyword bonus
- `_calculate_evidence_adjustment()` — heuristic delivery ratio bonus
- `_calculate_consistency_adjustment()` — heuristic score/signal alignment
- `_calculate_signal_alignment()` — heuristic signal matching
- `_identify_escalation_reasons()` — heuristic reason detection

All replaced by the single deterministic formula above.

---

## 4. Trace Discipline (Phase 5)

| Rule | Enforcement | File |
|------|-------------|------|
| `trace_id` must come from Niyantran | `NiyantranTask.from_dict()` raises `ValueError` if missing | `niyantran_connection.py` |
| Missing `trace_id` → REJECT | Min length = 8 chars enforced | `niyantran_connection.py` |
| Overwrite attempt → REJECT | `trace_id` passed directly to bucket, never regenerated | `niyantran_connection.py` |
| Bucket always uses Niyantran `trace_id` | `bucket_integration.log_evaluation(..., trace_id=trace_id)` | `niyantran_connection.py` |

```python
# Enforcement code (niyantran_connection.py):
trace_id = data.get("trace_id", "").strip()
if not trace_id or len(trace_id) < 8:
    raise ValueError("trace_id missing or too short — must come from Niyantran")
```

---

## 5. Bucket Access Control (Phase 5)

```
allowed_reads = [
    "same_task_history",   → get_evaluation_logs() + get_evaluation_by_trace_id()
    "escalation_cases"     → get_escalation_cases(candidate_id)
]

All other reads → reject_unauthorised_read(read_type) → BUCKET_READ_REJECTED
Write → ALWAYS happens, no exceptions
```

| Method | Allowed | Type |
|--------|---------|------|
| `log_evaluation()` | YES | Write (mandatory) |
| `get_evaluation_logs()` | YES | same_task_history |
| `get_evaluation_by_trace_id()` | YES | same_task_history |
| `get_escalation_cases(candidate_id)` | YES | escalation_cases |
| `get_bucket_stats()` | YES | aggregate read |
| Any other read | NO | `reject_unauthorised_read()` |

---

## 6. Task Selection (Phase 2)

| Rule | Enforcement |
|------|-------------|
| NO task generation | `task_selection_engine.py` only reads from `NIYANTRAN_TASK_GRAPH` |
| Selection only | `select_next_task()` returns first matching entry — no creation |
| Deterministic | Same `(score, decision, difficulty)` → same `next_task_id` always |
| Source tagged | Every result includes `source = "niyantran_task_graph"` |

**Graph structure:**
```
(decision_band, difficulty_band) → [task_id_1, task_id_2, ...]

decision_band:   approved | rejected_borderline | rejected_fail
difficulty_band: beginner | intermediate | advanced
```

**What was removed:**
- `_generate_next_task()` from `assignment_engine.py`
- Dynamic title generation (`f"Advanced {focus_area} Challenge"`)
- `datetime.now()` in next_task_id generation

---

## 7. REVIEW_PACKET Hard Gate (Phase 1 + Parser Hardening)

| Check | Enforcement |
|-------|-------------|
| File exists | Hard reject if missing |
| Sections as `##` headers | Regex `^#{1,3}\s+(.+)$` — paragraph text rejected |
| Section ordering | Must match spec order exactly |
| Section quality | Min word count + required sub-elements per section |
| JSON extraction | Fenced ` ```json ``` ` block only — no greedy regex |
| Output sample schema | Must contain `score`, `decision`, `trace_id` |
| Confidence signal | Returns `confidence` (0.0–1.0) + `validation_depth` |
| Parse only | Parser returns NO score, NO status, NO decision |

---

## 8. Failure Case Coverage

All failure cases are deterministic and structured:

| Failure | Trigger | Response |
|---------|---------|----------|
| Missing REVIEW_PACKET | File not found | `HARD_GATE_FAILURE`, score=0 |
| Malformed REVIEW_PACKET | Wrong headers / bad JSON | `HARD_GATE_FAILURE`, score=0 |
| Invalid registry | Unknown `module_id` | `REJECT`, score=0 |
| Missing `trace_id` | Not provided by Niyantran | `ValueError` raised, request rejected |
| No repository | `repository_available=False` | `code=0`, `proof_cap_4.0` applied |
| Empty repository | `file_count < 3` | `Q_code=0`, `code_cap_5.0` applied |
| Low delivery ratio | `delivery_ratio < 0.6` | `alignment=0`, `alignment_cap_6.0` applied |
| Score < 6 | Any REJECTED submission | Correction/reinforcement path via task graph |
| Confidence < 0.98 | Low PAC or rubric | Escalation case created + persisted |

---

## 9. What Was Explicitly NOT Introduced

- No RL / reinforcement learning
- No adaptive scoring weights
- No dynamic task generation
- No LLM calls in scoring pipeline
- No randomness (`random`, `uuid4` only for fallback trace_ids)
- No alternate scoring paths
- No Niyantran bypass
- No bucket write bypass
