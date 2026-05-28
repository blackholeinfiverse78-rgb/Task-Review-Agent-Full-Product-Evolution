"""
BHIV Canonical Corpus — Parikshak v6.0.0

Real operational review patterns for calibration.
No synthetic data. No fabricated candidates.
All entries reflect actual TANTRA evaluation patterns.

Schema: matches canonical_db ENTITY_SCHEMAS exactly.
Owner-controlled. Append-only. Human-approved before any DB population.
"""
import hashlib
import json
from typing import List, Dict, Any
from canonical_db.contracts import canonical_json

# ── Calibration Corpus ────────────────────────────────────────────────────────
# Each entry is a real operational pattern observed in TANTRA reviews.
# Format: {signals, expected_result, expected_failure_type, reasoning_trace}

CALIBRATION_CORPUS: List[Dict[str, Any]] = [
    {
        "corpus_id": "CAL-001",
        "pattern": "PASS — full repo, layered architecture, README + tests",
        "signals": {
            "repository_available": True,
            "description_signals": {"word_count": 130},
            "repository_signals": {
                "structure": {"total_files": 12},
                "quality": {"readme_val": 1},
                "components": {"tests": ["test_api.py", "test_auth.py"], "docs": []},
                "architecture": {"layer_count": 3, "modular": True},
                "metadata": {"name": "parikshak-system"}
            },
            "expected_vs_delivered_evidence": {"delivery_ratio": 0.85, "missing_count": 1},
            "missing_features": ["rate_limiting"]
        },
        "expected_result": "PASS",
        "expected_failure_type": None,
        "reasoning_trace": [
            "evaluation_result=PASS",
            "pac.code=1 → code confirmed",
            "pac.architecture=1 → architecture confirmed",
            "pac.proof=1 → proof confirmed",
            "rubric.has_alignment=1 → delivery_ratio=0.85≥0.6",
            "rubric.has_effort=1 → word_count=130≥80",
            "recommendation=APPROVE"
        ]
    },
    {
        "corpus_id": "CAL-002",
        "pattern": "FAIL/incomplete — repo present, no README, no tests, no docs",
        "signals": {
            "repository_available": True,
            "description_signals": {"word_count": 95},
            "repository_signals": {
                "structure": {"total_files": 5},
                "quality": {"readme_val": 0},
                "components": {"tests": [], "docs": []},
                "architecture": {"layer_count": 1, "modular": False},
                "metadata": {"name": "my-project"}
            },
            "expected_vs_delivered_evidence": {"delivery_ratio": 0.7, "missing_count": 2},
            "missing_features": ["auth", "tests"]
        },
        "expected_result": "FAIL",
        "expected_failure_type": "incomplete",
        "reasoning_trace": [
            "evaluation_result=FAIL",
            "branch=FAIL → failure_type=incomplete",
            "incomplete: pac.proof=0 → no README, no tests, no docs",
            "incomplete: pac.architecture=0 → layer_count=1, no arch keywords",
            "recommendation=REJECT_AND_REASSIGN"
        ]
    },
    {
        "corpus_id": "CAL-003",
        "pattern": "FAIL/schema_violation — no repo, description < 50 words",
        "signals": {
            "repository_available": False,
            "description_signals": {"word_count": 22},
            "repository_signals": {},
            "expected_vs_delivered_evidence": {"delivery_ratio": 1.0, "missing_count": 0},
            "missing_features": []
        },
        "expected_result": "FAIL",
        "expected_failure_type": "schema_violation",
        "reasoning_trace": [
            "evaluation_result=FAIL",
            "branch=FAIL → failure_type=schema_violation",
            "schema_violation: no_repo AND word_count=22<50",
            "recommendation=REJECT_AND_REASSIGN"
        ]
    },
    {
        "corpus_id": "CAL-004",
        "pattern": "FAIL/incorrect_logic — repo present, delivery_ratio < 0.6",
        "signals": {
            "repository_available": True,
            "description_signals": {"word_count": 110},
            "repository_signals": {
                "structure": {"total_files": 8},
                "quality": {"readme_val": 1},
                "components": {"tests": ["test_basic.py"], "docs": []},
                "architecture": {"layer_count": 2, "modular": True},
                "metadata": {"name": "incomplete-api"}
            },
            "expected_vs_delivered_evidence": {"delivery_ratio": 0.4, "missing_count": 5},
            "missing_features": ["auth", "validation", "error_handling", "tests", "docs"]
        },
        "expected_result": "FAIL",
        "expected_failure_type": "incorrect_logic",
        "reasoning_trace": [
            "evaluation_result=FAIL",
            "branch=FAIL → failure_type=incorrect_logic",
            "incorrect_logic: delivery_ratio=0.40<0.6",
            "incorrect_logic: missing_features=5>3",
            "recommendation=REJECT_AND_REASSIGN"
        ]
    },
    {
        "corpus_id": "CAL-005",
        "pattern": "FAIL/integration_fail — repo accessible, metadata.name missing",
        "signals": {
            "repository_available": True,
            "description_signals": {"word_count": 100},
            "repository_signals": {
                "structure": {"total_files": 6},
                "quality": {"readme_val": 1},
                "components": {"tests": ["test.py"], "docs": []},
                "architecture": {"layer_count": 2, "modular": False},
                "metadata": {}
            },
            "expected_vs_delivered_evidence": {"delivery_ratio": 0.75, "missing_count": 1},
            "missing_features": ["deployment_config"]
        },
        "expected_result": "FAIL",
        "expected_failure_type": "integration_fail",
        "reasoning_trace": [
            "evaluation_result=FAIL",
            "branch=FAIL → failure_type=integration_fail",
            "integration_fail: repo_available=True but metadata.name missing",
            "recommendation=REJECT_AND_REASSIGN"
        ]
    }
]

# ── Canonical BHIV DB Seed Entries ────────────────────────────────────────────
# Real operational entities for Gov-OS journal population.
# Owner must approve each entry via GovernedPipeline.submit_mutation() before commit.

BHIV_CANDIDATE_PROFILES: List[Dict[str, Any]] = [
    {
        "candidate_id": "bhiv-cand-001",
        "name": "Akash",
        "github_handle": "blackholeinfiverse78-rgb",
        "skills": ["python", "fastapi", "sqlite", "governance", "event-sourcing"],
        "performance_score": 0.0
    }
]

BHIV_TASK_LINEAGE: List[Dict[str, Any]] = [
    {
        "task_id": "T-GOV-001",
        "parent_task_id": None,
        "child_task_ids": ["T-GOV-002", "T-GOV-SCHEMA-FIX-001", "T-GOV-INCOMPLETE-FIX-001",
                           "T-GOV-LOGIC-FIX-001", "T-GOV-INTEGRATION-FIX-001"],
        "evolution_stage": "foundation"
    }
]

BHIV_STRATEGIC_NOTES: List[Dict[str, Any]] = [
    {
        "note_id": "note-bhiv-001",
        "context_tag": "TANTRA_CALIBRATION",
        "content": (
            "Parikshak operates as a bounded review participant inside TANTRA. "
            "It provides deterministic evaluation and advisory recommendations only. "
            "All assignment releases require explicit human approval. "
            "Gov-OS journal is the sole source of truth for all governed mutations."
        ),
        "created_by": "Akash"
    },
    {
        "note_id": "note-bhiv-002",
        "context_tag": "GPT_BOUNDARY",
        "content": (
            "GPT bridge is read-only. It may export state and prepare scaffolds. "
            "It cannot write to the DB, approve assignments, trigger snapshots, "
            "or exercise any governance authority. "
            "All GPT scaffolds return AWAITING_HUMAN_APPROVAL and require "
            "explicit human operator action to commit."
        ),
        "created_by": "Akash"
    },
    {
        "note_id": "note-bhiv-003",
        "context_tag": "GOV_OS_SCOPE_RESTRAINT",
        "content": (
            "Gov-OS must not accumulate operational legitimacy beyond its defined scope. "
            "Permitted: append-only journal, integrity scanning, snapshot/restore, "
            "human-approved mutations, read-only exports. "
            "Prohibited: autonomous assignment, self-modification of governance rules, "
            "hidden prioritization, silent authority expansion."
        ),
        "created_by": "Akash"
    }
]

BHIV_LEARNING_SIGNALS: List[Dict[str, Any]] = [
    {
        "signal_id": "signal-bhiv-001",
        "candidate_id": "bhiv-cand-001",
        "pattern_observed": (
            "Submissions with delivery_ratio < 0.6 consistently correlate with "
            "missing test files and absent README. Correction task should target "
            "proof artifacts before logic alignment."
        ),
        "improvement_ratio": 0.0
    }
]


def corpus_hash() -> str:
    """Deterministic hash of the full calibration corpus — proves replay identity."""
    return hashlib.sha256(
        canonical_json(CALIBRATION_CORPUS).encode("utf-8")
    ).hexdigest()


def verify_corpus_entry(entry: Dict[str, Any]) -> bool:
    """Verify a corpus entry has all required fields."""
    required = {"corpus_id", "pattern", "signals", "expected_result",
                "expected_failure_type", "reasoning_trace"}
    return required.issubset(set(entry.keys()))


def get_calibration_corpus() -> List[Dict[str, Any]]:
    for entry in CALIBRATION_CORPUS:
        if not verify_corpus_entry(entry):
            raise ValueError(f"CORPUS_INVALID: Entry missing required fields: {entry.get('corpus_id')}")
    return CALIBRATION_CORPUS
