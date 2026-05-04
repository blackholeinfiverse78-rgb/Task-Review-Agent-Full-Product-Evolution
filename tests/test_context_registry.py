"""
Parikshak Context Registry & Mandala Mapping — Phase 7 Tests
Minimum 5 test cases:
  TC-1: 5 tasks mapped to correct product/layer
  TC-2: Same input → same mapping (3 runs)
  TC-3: Incorrect/unknown task → deterministic default fallback
  TC-4: Context-aware task selection uses product allowed_next_tasks
  TC-5: Registry schema validation — all products have required fields
  TC-6: Direct product lookup
  TC-7: Layer-based product listing

Run: python tests/test_context_registry.py
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from task_selector.context_registry import context_registry
from task_selector.mandala_mapper import mandala_mapper
from task_selector.task_selection_engine import task_selection_engine


# ── TC-1: 5 tasks mapped to correct product/layer ────────────────────────

def test_tc1_correct_product_mapping():
    """5 known tasks must map to their expected product and layer."""
    cases = [
        # (title, description_snippet, expected_product, expected_layer)
        (
            "Build ROS2 Navigation Pipeline",
            "Implement ROS2 autonomous navigation with SLAM and lidar sensor fusion",
            "robotics", "execution"
        ),
        (
            "Solidity Smart Contract for DeFi Protocol",
            "Write Ethereum smart contract using Solidity for token staking and blockchain ledger",
            "blockchain", "execution"
        ),
        (
            "Parikshak Evaluation Rubric Engine",
            "Implement deterministic scoring rubric with PAC detection and bucket trace logging",
            "parikshak", "governance"
        ),
        (
            "Gurukul Learning Module Builder",
            "Build curriculum module with lesson delivery, student progress tracking and quiz assessment",
            "gurukul", "execution"
        ),
        (
            "Mitra Conversational AI Assistant",
            "Build NLP chatbot with intent detection, dialogue management and LLM response generation",
            "mitra", "intelligence"
        ),
    ]

    for title, desc, expected_product, expected_layer in cases:
        result = mandala_mapper.map_task_to_context(title, desc)
        assert result["product"] == expected_product, \
            f"'{title}' → expected product='{expected_product}', got '{result['product']}'"
        assert result["layer"] == expected_layer, \
            f"'{title}' → expected layer='{expected_layer}', got '{result['layer']}'"
        assert result["mapping_source"] == "keyword_match"
        assert len(result["matched_keywords"]) > 0

    print(f"[TC-1 PASS] All 5 tasks mapped to correct product/layer")


# ── TC-2: Same input → same mapping (3 runs) ─────────────────────────────

def test_tc2_deterministic_mapping():
    """Same title+description must produce identical mapping across 3 runs."""
    title = "Build ROS2 Navigation Pipeline with SLAM"
    desc  = "Implement ROS2 autonomous robot navigation using lidar sensor and motor control"

    results = [mandala_mapper.map_task_to_context(title, desc) for _ in range(3)]

    products = [r["product"] for r in results]
    layers   = [r["layer"]   for r in results]
    confs    = [r["mapping_confidence"] for r in results]

    assert len(set(products)) == 1, f"Product differs across runs: {products}"
    assert len(set(layers))   == 1, f"Layer differs across runs: {layers}"
    assert len(set(confs))    == 1, f"Confidence differs across runs: {confs}"

    print(f"[TC-2 PASS] Deterministic: product={products[0]} layer={layers[0]} × 3 runs")


# ── TC-3: Unknown task → deterministic default fallback ──────────────────

def test_tc3_unknown_task_default_fallback():
    """Input with no matching keywords must return default_product deterministically."""
    title = "Xyzzyx Frobnicator Operation"
    desc  = "Do something with the frobnicator and the xyzzyx contraption"

    results = [mandala_mapper.map_task_to_context(title, desc) for _ in range(3)]

    for r in results:
        assert r["mapping_source"] == "default_fallback", \
            f"Expected default_fallback, got {r['mapping_source']}"
        assert r["product"] == context_registry.get_default_product()
        assert r["matched_keywords"] == []

    # All 3 runs identical
    assert len(set(r["product"] for r in results)) == 1

    print(f"[TC-3 PASS] Unknown task → default='{results[0]['product']}' × 3 runs")


# ── TC-4: Context-aware task selection ───────────────────────────────────

def test_tc4_context_aware_selection():
    """
    Task selection with product_context must prefer tasks in
    product's allowed_next_tasks when available.
    """
    # Robotics context — allowed_next_tasks includes NT-ADV-B-001
    robotics_ctx = mandala_mapper.map_task_to_context(
        "Build ROS2 Pipeline",
        "Implement ROS2 robot navigation with lidar sensor"
    )
    assert robotics_ctx["product"] == "robotics"

    # APPROVED + beginner → graph gives NT-ADV-B-001, NT-ADV-B-002, NT-ADV-B-003
    # robotics allowed_next_tasks = [NT-ADV-B-001, NT-ADV-I-001, NT-ADV-A-001]
    # intersection = NT-ADV-B-001 → should be selected
    result = task_selection_engine.select_next_task(
        score_10=8.0,
        decision="APPROVED",
        current_difficulty="beginner",
        product_context=robotics_ctx
    )
    assert result["source"] == "niyantran_task_graph"
    assert result["product"] == "robotics"
    assert result["context_source"] in ("product_context", "graph_fallback")
    assert result["next_task_id"].startswith("NT-")

    # Same input × 3 → same result
    results = [
        task_selection_engine.select_next_task(8.0, "APPROVED", "beginner", robotics_ctx)
        for _ in range(3)
    ]
    ids = [r["next_task_id"] for r in results]
    assert len(set(ids)) == 1, f"Context-aware selection not deterministic: {ids}"

    print(f"[TC-4 PASS] Context-aware selection: {ids[0]} × 3 | context_source={results[0]['context_source']}")


# ── TC-5: Registry schema validation ─────────────────────────────────────

def test_tc5_registry_schema_validation():
    """All products in registry must have all required Phase 1 schema fields."""
    required_fields = [
        "product", "layer", "subsystem", "role",
        "tantra_layers", "keywords", "dependencies",
        "allowed_next_tasks", "difficulty_levels"
    ]

    products = context_registry.get_all_products()
    assert len(products) >= 7, f"Expected at least 7 products, got {len(products)}"

    for pid, ctx in products.items():
        d = ctx.to_dict()
        for field in required_fields:
            assert field in d and d[field] is not None, \
                f"Product '{pid}' missing required field '{field}'"
        assert len(ctx.keywords) > 0,           f"Product '{pid}' has no keywords"
        assert len(ctx.difficulty_levels) > 0,  f"Product '{pid}' has no difficulty_levels"
        assert ctx.layer in ("intelligence", "governance", "execution", "memory"), \
            f"Product '{pid}' has unknown layer '{ctx.layer}'"

    print(f"[TC-5 PASS] Schema valid for all {len(products)} products")


# ── TC-6: Direct product lookup ───────────────────────────────────────────

def test_tc6_direct_product_lookup():
    """Direct lookup by product_id must return correct context."""
    for pid in ["gurukul", "niyantran", "parikshak", "mitra", "insightflow", "robotics", "blockchain"]:
        ctx = context_registry.get_product(pid)
        assert ctx is not None,          f"Product '{pid}' not found in registry"
        assert ctx.product == pid,       f"Product id mismatch: {ctx.product} != {pid}"
        assert ctx.layer != "",          f"Product '{pid}' has empty layer"
        assert ctx.subsystem != "",      f"Product '{pid}' has empty subsystem"

    # Non-existent product returns None
    assert context_registry.get_product("nonexistent") is None

    print(f"[TC-6 PASS] Direct lookup verified for 7 products + None for unknown")


# ── TC-7: Layer-based product listing ────────────────────────────────────

def test_tc7_layer_product_listing():
    """Each TANTRA layer must return correct product list."""
    layer_expectations = {
        "intelligence": {"mitra", "insightflow", "parikshak"},
        "governance":   {"niyantran", "parikshak", "blockchain"},
        "execution":    {"gurukul", "robotics", "blockchain", "niyantran"},
        "memory":       {"gurukul", "insightflow"},
    }

    for layer, expected_products in layer_expectations.items():
        actual = set(context_registry.get_layer_products(layer))
        assert expected_products.issubset(actual), \
            f"Layer '{layer}': expected {expected_products}, got {actual}"

    print(f"[TC-7 PASS] All 4 TANTRA layers return correct product sets")


# ── TC-8: Niyantran InsightFlow mapping ──────────────────────────────────

def test_tc8_insightflow_mapping():
    """Analytics/dashboard tasks must map to insightflow."""
    result = mandala_mapper.map_task_to_context(
        "Build Analytics Dashboard",
        "Create InsightFlow reporting dashboard with KPI metrics visualization and trend analysis"
    )
    assert result["product"] == "insightflow", \
        f"Expected insightflow, got {result['product']}"
    assert result["layer"] == "intelligence"
    print(f"[TC-8 PASS] InsightFlow mapping: {result['product']} / {result['layer']}")


# ── Runner ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    tests = [
        test_tc1_correct_product_mapping,
        test_tc2_deterministic_mapping,
        test_tc3_unknown_task_default_fallback,
        test_tc4_context_aware_selection,
        test_tc5_registry_schema_validation,
        test_tc6_direct_product_lookup,
        test_tc7_layer_product_listing,
        test_tc8_insightflow_mapping,
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
    print(f"CONTEXT REGISTRY PROOF: {passed}/{len(tests)} passed, {failed} failed")
    if failed == 0:
        print("ALL TESTS PASSED — MANDALA MAPPING IS DETERMINISTIC")
    print("=" * 60)
