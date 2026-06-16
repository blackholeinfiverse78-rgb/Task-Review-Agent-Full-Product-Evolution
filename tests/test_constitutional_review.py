"""
Unit tests for the Constitutional Review Engine.
"""
import os
import shutil
import pytest
from trace_reconstruction_validator import TraceReconstructionValidator
from artifact_validation_engine import ArtifactValidationEngine
from constitutional_readiness_engine import ConstitutionalReadinessEngine
from scripts.run_constitutional_review_tests import create_base_files, TRACES_DIR

@pytest.fixture(scope="module", autouse=True)
def setup_test_traces():
    # Setup test trace files
    os.makedirs(TRACES_DIR, exist_ok=True)
    yield
    # Cleanup after tests
    if os.path.exists(TRACES_DIR):
        shutil.rmtree(TRACES_DIR)

def test_ready_verdict():
    create_base_files("test-trace-ready")
    engine = ConstitutionalReadinessEngine(TRACES_DIR)
    res = engine.evaluate_readiness("test-trace-ready")
    assert res["verdict"] == "READY"
    assert res["reconstructable"] is True
    assert res["valid"] is True
    assert len(res["reasons"]) == 0

def test_needs_review_verdict():
    create_base_files("test-trace-needs-review", {
        "handover_bundle.json": None, # Missing optional
    })
    engine = ConstitutionalReadinessEngine(TRACES_DIR)
    res = engine.evaluate_readiness("test-trace-needs-review")
    assert res["verdict"] == "NEEDS_REVIEW"
    assert res["reconstructable"] is True
    assert len(res["reasons"]) > 0

def test_rejected_reconstruction():
    create_base_files("test-trace-missing-critical", {
        "evidence_bundle.json": None, # Missing critical
    })
    engine = ConstitutionalReadinessEngine(TRACES_DIR)
    res = engine.evaluate_readiness("test-trace-missing-critical")
    assert res["verdict"] == "REJECTED"
    assert res["reconstructable"] is False

def test_rejected_governance():
    create_base_files("test-trace-rejected-gov", {
        "validation_decision.json": {
            "decision": "REJECTED",
            "signed_by": "Akash"
        }
    })
    engine = ConstitutionalReadinessEngine(TRACES_DIR)
    res = engine.evaluate_readiness("test-trace-rejected-gov")
    assert res["verdict"] == "REJECTED"
    assert res["valid"] is False
