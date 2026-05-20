"""
Parikshak Graph Engine + Task Selector — Determinism Tests (Phase 7)
5 deterministic scenarios:
  TC-1: Same input → same task_id (3 runs)
  TC-2: Pass case → correct next_tasks branch
  TC-3: Fail case → correct failure_tasks branch
  TC-4: Unknown task_id → deterministic fallback
  TC-5: Mandala context enriches selection correctly
  TC-6: Full chain traversal (3 hops)
  TC-7: task_selector unified output contract

Run: python tests/test_graph_engine.py
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from task_selector.graph_engine import graph_engine
from task_selector.task_selector import task_selector
from task_selector.mandala_mapper import mandala_mapper


# ── TC-1: Same input → same task_id (3 runs) ─────────────────────────────

def test_tc1_determinism_3_runs():
    """Same (task_id, score, decision) must return same next_task_id × 3."""
    results = [
        graph_engine.traverse("NT-COR-B-001", 7.5, "APPROVED")
        for _ in range(3)
    ]
    ids = [r["next_task_id"] for r in results]
    assert len(set(ids)) == 1, f"Not deterministic: {ids}"
    assert ids[0] == "NT-REI-B-001", f"Wrong next task: {ids[0]}"
    print(f"[TC-1 PASS] 3 runs identical: {ids[0]}")


# ── TC-2: Pass case → next_tasks branch ──────────────────────────────────

def test_tc2_pass_branch():
    """score >= 6 must follow next_tasks branch."""
    cases = [
        ("NT-COR-B-001", 7.0, "APPROVED",  "NT-REI-B-001"),
        ("NT-REI-B-001", 8.0, "APPROVED",  "NT-REI-B-002"),
        ("NT-REI-B-002", 6.5, "APPROVED",  "NT-ADV-B-001"),
        ("NT-ADV-B-001", 9.0, "APPROVED",  "NT-ADV-B-002"),
        ("NT-ADV-B-002", 7.0, "APPROVED",  "NT-ADV-B-003"),
    ]
    for task_id, score, decision, expected_next in cases:
        result = graph_engine.traverse(task_id, score, decision)
        assert result["next_task_id"] == expected_next, \
            f"{task_id} pass -> expected {expected_next}, got {result['next_task_id']}"
        assert result["branch"] == "pass"
        assert result["source"] == "task_graph"
    print(f"[TC-2 PASS] All {len(cases)} pass branches correct")


# ── TC-3: Fail case → failure_tasks branch ───────────────────────────────

def test_tc3_fail_branch():
    """score < 6 must follow failure_tasks branch."""
    cases = [
        ("NT-REI-B-001", 3.0, "REJECTED",  "NT-COR-B-001"),
        ("NT-ADV-B-001", 2.0, "REJECTED",  "NT-REI-B-002"),
        ("NT-ADV-I-001", 4.5, "REJECTED",  "NT-REI-I-001"),
        ("NT-ADV-A-001", 1.0, "REJECTED",  "NT-REI-A-001"),
        ("GK-ADV-I-001", 3.5, "REJECTED",  "GK-REI-B-001"),
    ]
    for task_id, score, decision, expected_next in cases:
        result = graph_engine.traverse(task_id, score, decision)
        assert result["next_task_id"] == expected_next, \
            f"{task_id} fail -> expected {expected_next}, got {result['next_task_id']}"
        assert result["branch"] == "fail"
    print(f"[TC-3 PASS] All {len(cases)} fail branches correct")


# ── TC-4: Unknown task_id → deterministic fallback ───────────────────────

def test_tc4_unknown_task_fallback():
    """Unknown task_id must return deterministic fallback, not crash."""
    # Pass case → NT-ADV-B-001
    r_pass = graph_engine.traverse("UNKNOWN-TASK-999", 8.0, "APPROVED")
    assert r_pass["next_task_id"] == "NT-ADV-B-001"
    assert r_pass["source"] == "task_graph"

    # Borderline fail → NT-REI-B-001
    r_borderline = graph_engine.traverse("UNKNOWN-TASK-999", 4.5, "REJECTED")
    assert r_borderline["next_task_id"] == "NT-REI-B-001"

    # Hard fail → NT-COR-B-001
    r_fail = graph_engine.traverse("UNKNOWN-TASK-999", 1.0, "REJECTED")
    assert r_fail["next_task_id"] == "NT-COR-B-001"

    # All 3 deterministic across 3 runs
    runs = [graph_engine.traverse("UNKNOWN-TASK-999", 8.0, "APPROVED") for _ in range(3)]
    assert len(set(r["next_task_id"] for r in runs)) == 1

    print(f"[TC-4 PASS] Unknown task fallback: pass={r_pass['next_task_id']} borderline={r_borderline['next_task_id']} fail={r_fail['next_task_id']}")


# ── TC-5: Mandala context enriches selection ─────────────────────────────

def test_tc5_mandala_context():
    """Mandala mapper must correctly identify product and enrich task_selector output."""
    cases = [
        ("ROS2 Navigation Pipeline", "Implement ROS2 robot navigation with lidar sensor", "robotics"),
        ("Solidity Smart Contract", "Build Ethereum DeFi token staking with blockchain ledger", "blockchain"),
        ("Parikshak Evaluation Engine", "Build deterministic scoring rubric with PAC detection", "parikshak"),
        ("Gurukul Learning Module", "Build curriculum with lesson delivery and student assessment", "gurukul"),
    ]
    for title, desc, expected_product in cases:
        ctx = mandala_mapper.map_task_to_context(title, desc)
        assert ctx["product"] == expected_product, \
            f"'{title}' -> expected {expected_product}, got {ctx['product']}"

        # task_selector must include mandala_context
        result = task_selector.select(7.0, "APPROVED", title, desc)
        assert result["mandala_context"]["product"] == expected_product
        assert result["source"] == "task_graph"

    print(f"[TC-5 PASS] Mandala context correct for {len(cases)} cases")


# ── TC-6: Full chain traversal (3 hops) ──────────────────────────────────

def test_tc6_chain_traversal():
    """Traverse 3 hops from NT-COR-B-001 on pass path."""
    hop1 = graph_engine.traverse("NT-COR-B-001", 7.0, "APPROVED")
    assert hop1["next_task_id"] == "NT-REI-B-001"

    hop2 = graph_engine.traverse(hop1["next_task_id"], 7.0, "APPROVED")
    assert hop2["next_task_id"] == "NT-REI-B-002"

    hop3 = graph_engine.traverse(hop2["next_task_id"], 7.0, "APPROVED")
    assert hop3["next_task_id"] == "NT-ADV-B-001"

    print(f"[TC-6 PASS] Chain: NT-COR-B-001 -> {hop1['next_task_id']} -> {hop2['next_task_id']} -> {hop3['next_task_id']}")


# ── TC-7: task_selector output contract ──────────────────────────────────

def test_tc7_selector_output_contract():
    """task_selector must always return all required contract fields."""
    required = ["task_id", "title", "task_type", "difficulty", "objective",
                "dharma", "product", "layer", "selection_reason", "source"]

    cases = [
        (8.0, "APPROVED", "JWT Auth API", "Build JWT auth REST API"),
        (2.0, "REJECTED", "My App", "I built something"),
        (5.0, "REJECTED", "REST API", "Build REST API with auth"),
    ]
    for score, decision, title, desc in cases:
        result = task_selector.select(score, decision, title, desc)
        for field in required:
            assert field in result and result[field] is not None, \
                f"Missing field '{field}' for ({score}, {decision})"
        assert result["source"] == "task_graph"
        assert result["difficulty"] in ("beginner", "intermediate", "advanced")

    print(f"[TC-7 PASS] Output contract verified for {len(cases)} cases")


# ── TC-8: Graph DB stats ──────────────────────────────────────────────────

def test_tc8_graph_db_stats():
    """Task database must have >= 25 tasks across >= 4 products."""
    stats = graph_engine.get_stats()
    assert stats["total_tasks"] >= 25, f"Expected >= 25 tasks, got {stats['total_tasks']}"
    assert len(stats["by_product"]) >= 4, f"Expected >= 4 products, got {len(stats['by_product'])}"
    print(f"[TC-8 PASS] DB stats: {stats['total_tasks']} tasks across {list(stats['by_product'].keys())}")


# ── Runner ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    tests = [
        test_tc1_determinism_3_runs,
        test_tc2_pass_branch,
        test_tc3_fail_branch,
        test_tc4_unknown_task_fallback,
        test_tc5_mandala_context,
        test_tc6_chain_traversal,
        test_tc7_selector_output_contract,
        test_tc8_graph_db_stats,
    ]
    passed = failed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except Exception as e:
            print(f"[FAIL] {t.__name__}: {e}")
            failed += 1
    print(f"\n{'='*60}")
    print(f"GRAPH ENGINE PROOF: {passed}/{len(tests)} passed, {failed} failed")
    if failed == 0:
        print("ALL TESTS PASSED — GRAPH IS DETERMINISTIC")
    print("=" * 60)
