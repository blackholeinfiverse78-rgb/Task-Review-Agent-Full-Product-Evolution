"""
Operational Resilience Tests — Parikshak v3.0.0
Proves system survives degraded conditions.
All 15 resilience scenarios validated.
"""
import sys, os, json, tempfile, hashlib
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from replay_audit.atomic_persistence import (
    atomic_append, validate_log_segment,
    write_replay_checkpoint, load_checkpoint,
    recover_interrupted_write
)
from replay_audit.replay_engine import replay_engine
from task_selector.task_graph_engine import task_graph_engine
from evaluation_engine.rule_engine import rule_engine
from governance_layer.governance import (
    GovernanceRequest, OperatorRole, OverrideReason,
    constitutional_validator, IRREVERSIBLE_STATES
)

SEP = "-" * 60
results = []

def run_test(name, fn):
    print(f"\n{SEP}\nTEST: {name}")
    try:
        result = fn()
        status = result.get("status", "FAIL")
        print(f"  Detail: {result.get('detail', '')}")
        print(f"  -> {status}")
        results.append(status == "PASS")
        return status == "PASS"
    except Exception as e:
        print(f"  ERROR: {e}")
        results.append(False)
        return False


# TC-1: Interrupted write recovery
def tc1():
    with tempfile.TemporaryDirectory() as d:
        # Create orphaned .tmp file
        tmp = os.path.join(d, "test.jsonl.tmp")
        with open(tmp, "w") as f:
            f.write('{"partial": true}')
        recovered = recover_interrupted_write(os.path.join(d, "test.jsonl"))
        assert recovered, "Should have recovered orphaned tmp"
        assert not os.path.exists(tmp), "Tmp file should be removed"
    return {"status": "PASS", "detail": "orphaned .tmp removed"}

run_test("TC-1: Interrupted write recovery", tc1)


# TC-2: Atomic append + checksum validation
def tc2():
    with tempfile.TemporaryDirectory() as d:
        filepath = os.path.join(d, "test.jsonl")
        atomic_append(filepath, {"trace_id": "trace-test-001", "action": "test"})
        result = validate_log_segment(filepath)
        assert result["valid"], f"Log should be valid: {result}"
        assert result["entry_count"] == 1
    return {"status": "PASS", "detail": f"entry_count=1 valid=True"}

run_test("TC-2: Atomic append + checksum validation", tc2)


# TC-3: Corrupt log detection
def tc3():
    with tempfile.TemporaryDirectory() as d:
        filepath = os.path.join(d, "corrupt.jsonl")
        with open(filepath, "w") as f:
            f.write('{"valid": true, "_checksum": "wronghash"}\n')
            f.write('not valid json\n')
        result = validate_log_segment(filepath)
        assert not result["valid"], "Should detect corruption"
        assert len(result["corrupt_lines"]) > 0
    return {"status": "PASS", "detail": f"corrupt_lines={result['corrupt_lines']}"}

run_test("TC-3: Corrupt log detection", tc3)


# TC-4: Replay checkpoint write + load + hash validation
def tc4():
    ckpt_id = write_replay_checkpoint("trace-resilience-001", {
        "evaluation_result": "PASS",
        "selected_task_id": "T-GOV-002"
    })
    loaded = load_checkpoint(ckpt_id)
    assert loaded["state"]["evaluation_result"] == "PASS"
    assert loaded["state"]["selected_task_id"] == "T-GOV-002"
    return {"status": "PASS", "detail": f"checkpoint_id={ckpt_id}"}

run_test("TC-4: Replay checkpoint write + load + hash validation", tc4)


# TC-5: Tampered checkpoint detection
def tc5():
    ckpt_id = write_replay_checkpoint("trace-tamper-001", {"evaluation_result": "PASS"})
    ckpt_path = os.path.join("storage/checkpoints", f"{ckpt_id}.json")
    # Tamper with the file
    with open(ckpt_path, "r") as f:
        data = json.load(f)
    data["state"]["evaluation_result"] = "FAIL"  # tamper
    with open(ckpt_path, "w") as f:
        json.dump(data, f)
    try:
        load_checkpoint(ckpt_id)
        return {"status": "FAIL", "detail": "Should have detected tampering"}
    except ValueError as e:
        assert "hash mismatch" in str(e)
        return {"status": "PASS", "detail": "Tampering detected loudly"}

run_test("TC-5: Tampered checkpoint detection", tc5)


# TC-6: Partial recovery from damaged log
def tc6():
    with tempfile.TemporaryDirectory() as d:
        filepath = os.path.join(d, "damaged.jsonl")
        with open(filepath, "w") as f:
            f.write('{"trace_id": "t1", "action": "approve"}\n')
            f.write('CORRUPTED LINE\n')
            f.write('{"trace_id": "t2", "action": "reject"}\n')
        result = replay_engine.partial_recovery(filepath)
        assert result["recovered"]
        assert result["recoverable_entries"] == 2
        assert len(result["corrupt_lines"]) == 1
    return {"status": "PASS", "detail": f"recovered=2 corrupt=1"}

run_test("TC-6: Partial recovery from damaged log", tc6)


# TC-7: Replay divergence detection
def tc7():
    original = {"evaluation_result": "PASS", "failure_type": None, "selected_task_id": "T-GOV-002", "source": "task_graph"}
    diverged = {"evaluation_result": "FAIL", "failure_type": "incomplete", "selected_task_id": "T-GOV-F01", "source": "task_graph"}
    try:
        replay_engine.detect_divergence(original, diverged)
        return {"status": "FAIL", "detail": "Should have detected divergence"}
    except ValueError as e:
        assert "REPLAY_DIVERGENCE" in str(e)
        return {"status": "PASS", "detail": "Divergence detected loudly"}

run_test("TC-7: Replay divergence detection", tc7)


# TC-8: Same input = same output (determinism)
def tc8():
    signals = {
        "repository_available": True,
        "repository_signals": {
            "structure": {"total_files": 10},
            "quality": {"readme_score": 3, "documentation_density": 0.4},
            "components": {"tests": ["tests/test.py"], "docs": ["docs/README.md"], "routes": [], "services": [], "models": []},
            "architecture": {"layer_count": 3, "modular": True, "has_layers": True},
            "metadata": {"name": "parikshak-system"}
        },
        "expected_vs_delivered_evidence": {"delivery_ratio": 0.9, "expected_count": 5, "delivered_count": 4},
        "missing_features": [],
        "description_signals": {"word_count": 120, "structure_quality": 0.6},
        "title_signals": {"technical_keywords": ["fastapi"]},
        "failure_indicators": []
    }
    r1 = rule_engine.evaluate(signals)
    r2 = rule_engine.evaluate(signals)
    assert r1 == r2, "Non-deterministic output"
    return {"status": "PASS", "detail": f"result={r1['evaluation_result']} x2 identical"}

run_test("TC-8: Same input = same output (determinism)", tc8)


# TC-9: Missing trace_id -> hard reject
def tc9():
    try:
        from task_selector.niyantran_connection import NiyantranTask
        NiyantranTask.from_dict({"task_title": "test", "task_description": "test", "trace_id": ""})
        return {"status": "FAIL", "detail": "Should have rejected"}
    except ValueError as e:
        assert "NIYANTRAN_HARD_REJECT" in str(e)
        return {"status": "PASS", "detail": "Missing trace_id rejected loudly"}

run_test("TC-9: Missing trace_id -> hard reject", tc9)


# TC-10: Unknown task_id -> graph hard reject
def tc10():
    try:
        task_graph_engine.traverse("INVALID_TASK_XYZ", "PASS", None)
        return {"status": "FAIL", "detail": "Should have rejected"}
    except ValueError as e:
        assert "GRAPH_HARD_REJECT" in str(e)
        return {"status": "PASS", "detail": "Unknown task_id rejected loudly"}

run_test("TC-10: Unknown task_id -> graph hard reject", tc10)


# TC-11: Governance — unauthorized role rejected
def tc11():
    req = GovernanceRequest(
        trace_id="trace-gov-001",
        submission_id="sub-001",
        operator_id="op-001",
        operator_role=OperatorRole.REVIEW_OPERATOR,  # cannot modify
        action="modify",
        reason_taxonomy=OverrideReason.REQUIREMENT_CORRECTION
    )
    try:
        constitutional_validator.validate(req, "PENDING_REVIEW")
        return {"status": "FAIL", "detail": "Should have rejected"}
    except ValueError as e:
        assert "GOVERNANCE_REJECT" in str(e)
        return {"status": "PASS", "detail": "Unauthorized role rejected"}

run_test("TC-11: Governance — unauthorized role rejected", tc11)


# TC-12: Governance — modify without dual approval rejected
def tc12():
    req = GovernanceRequest(
        trace_id="trace-gov-002",
        submission_id="sub-002",
        operator_id="op-002",
        operator_role=OperatorRole.SENIOR_REVIEW_OPERATOR,
        action="modify",
        reason_taxonomy=OverrideReason.SAFETY_BLOCK,
        authorized_by=None  # missing
    )
    try:
        constitutional_validator.validate(req, "PENDING_REVIEW")
        return {"status": "FAIL", "detail": "Should have rejected"}
    except ValueError as e:
        assert "dual approval" in str(e)
        return {"status": "PASS", "detail": "Missing dual approval rejected"}

run_test("TC-12: Governance — modify without dual approval rejected", tc12)


# TC-13: Governance — irreversible state rejected
def tc13():
    req = GovernanceRequest(
        trace_id="trace-gov-003",
        submission_id="sub-003",
        operator_id="op-003",
        operator_role=OperatorRole.REVIEW_OPERATOR,
        action="approve",
        reason_taxonomy=OverrideReason.REQUIREMENT_CORRECTION
    )
    try:
        constitutional_validator.validate(req, "APPROVED")  # already approved
        return {"status": "FAIL", "detail": "Should have rejected"}
    except ValueError as e:
        assert "irreversible state" in str(e)
        return {"status": "PASS", "detail": "Irreversible state rejected"}

run_test("TC-13: Governance — irreversible state rejected", tc13)


# TC-14: No task outside DB returned
def tc14():
    all_valid = True
    violations = []
    for ft in ["schema_violation", "incomplete", "incorrect_logic", "integration_fail"]:
        g = task_graph_engine.traverse("T-GOV-001", "FAIL", ft)
        tid = g["selected_task_id"]
        if not task_graph_engine.validate_task_id(tid):
            all_valid = False
            violations.append(f"{ft}->{tid}")
    g_pass = task_graph_engine.traverse("T-GOV-001", "PASS", None)
    if not task_graph_engine.validate_task_id(g_pass["selected_task_id"]):
        all_valid = False
    return {"status": "PASS" if all_valid else "FAIL", "detail": f"violations={violations}"}

run_test("TC-14: No task outside DB returned", tc14)


# TC-15: Forensic report generation
def tc15():
    report = replay_engine.generate_forensic_report("trace-forensic-test")
    assert "trace_id" in report
    assert "events_found" in report
    assert "report_ts" in report
    return {"status": "PASS", "detail": f"report generated events={report['events_found']}"}

run_test("TC-15: Forensic report generation", tc15)


# Summary
print(f"\n{SEP}")
passed = sum(results)
total  = len(results)
print(f"RESULTS: {passed}/{total} PASSED")
print(f"\n-> {'SYSTEM OPERATIONALLY RESILIENT' if passed == total else 'RESILIENCE GAPS DETECTED'}")
