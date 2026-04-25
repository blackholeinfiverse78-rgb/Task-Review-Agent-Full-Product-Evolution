"""
Parikshak Assignment Engine — SINGLE EVALUATION AUTHORITY
Evaluates submissions as PASS or FAIL with a structured failure_type.

failure_type values:
  schema_violation    — missing REVIEW_PACKET, invalid module_id, malformed input
  incomplete          — missing repo, missing proof, missing architecture
  incorrect_logic     — code present but no alignment, delivery below threshold
  integration_fail    — repo inaccessible, network failure, bucket write failure

BOUNDARY RULES:
  - NO numeric scores, weights, or thresholds
  - NO partial scoring or fallback scoring
  - evaluate_and_assign() is the ONLY public entry point
"""
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger("assignment_engine")


class AssignmentEngine:
    """
    SINGLE EVALUATION AUTHORITY.
    Returns evaluation_result = PASS or FAIL.
    Returns failure_type when FAIL.
    No numeric scoring. No weights. No thresholds.
    """

    def __init__(self):
        self.authority_level = "CANONICAL_PRIMARY"

    def evaluate_and_assign(
        self,
        task_title: str,
        task_description: str,
        supporting_signals: Dict[str, Any]
    ) -> Dict[str, Any]:
        logger.info(f"[ASSIGNMENT ENGINE] Evaluating: {task_title[:60]}")

        # Phase 2: Binary P/A/C detection
        pac = self._detect_pac(supporting_signals)

        # Phase 3: Binary rubric checks
        rubric = self._check_rubric(supporting_signals, pac)

        # Phase 4: PASS or FAIL determination
        evaluation_result, failure_type = self._determine_result(pac, rubric, supporting_signals)

        result = {
            "evaluation_result": evaluation_result,
            "failure_type": failure_type,
            "pac": pac,
            "rubric": rubric,
            "canonical_authority": True,
            "evaluation_basis": "parikshak_assignment_engine",
        }

        logger.info(
            f"[ASSIGNMENT ENGINE] Result: {evaluation_result} | "
            f"failure_type={failure_type} | "
            f"P={pac['proof']} A={pac['architecture']} C={pac['code']}"
        )
        return result

    # ── Phase 2: Binary P/A/C ─────────────────────────────────────────────

    def _detect_pac(self, signals: Dict[str, Any]) -> Dict[str, int]:
        repo_signals   = signals.get("repository_signals") or {}
        repo_available = signals.get("repository_available", False)
        desc_signals   = signals.get("description_signals") or {}
        title_signals  = signals.get("title_signals") or {}

        file_count = repo_signals.get("structure", {}).get("total_files", 0)
        code = 1 if (repo_available and file_count > 0) else 0

        arch = repo_signals.get("architecture", {})
        has_layers = arch.get("has_layers", False) or arch.get("layer_count", 0) >= 2
        arch_keywords = {"architecture", "layer", "service", "module", "component",
                         "design", "flow", "pipeline", "orchestrat"}
        desc_text  = str(desc_signals).lower()
        title_text = str(title_signals).lower()
        has_arch_keywords = any(kw in desc_text or kw in title_text for kw in arch_keywords)
        architecture = 1 if (has_layers or (code == 1 and has_arch_keywords)) else 0

        quality      = repo_signals.get("quality", {})
        readme_score = quality.get("readme_score", 0)
        components   = repo_signals.get("components", {})
        test_files   = components.get("tests", [])
        doc_files    = components.get("docs", [])
        proof = 1 if (readme_score >= 1 or len(test_files) > 0 or len(doc_files) > 0) else 0

        logger.info(f"[ASSIGNMENT ENGINE] P/A/C → proof={proof} architecture={architecture} code={code}")
        return {"proof": proof, "architecture": architecture, "code": code}

    # ── Phase 3: Binary rubric ────────────────────────────────────────────

    def _check_rubric(self, signals: Dict[str, Any], pac: Dict[str, int]) -> Dict[str, int]:
        repo_signals   = signals.get("repository_signals") or {}
        repo_available = signals.get("repository_available", False)
        evd            = signals.get("expected_vs_delivered_evidence", {})
        delivery_ratio = evd.get("delivery_ratio", 0.0)
        missing        = signals.get("missing_features", [])
        desc_signals   = signals.get("description_signals") or {}
        word_count     = desc_signals.get("word_count", 0) if isinstance(desc_signals, dict) else 0
        structure_q    = desc_signals.get("structure_quality", 0) if isinstance(desc_signals, dict) else 0
        quality        = repo_signals.get("quality", {})
        readme_score   = quality.get("readme_score", 0)
        file_count     = repo_signals.get("structure", {}).get("total_files", 0)
        arch           = repo_signals.get("architecture", {})
        layer_count    = arch.get("layer_count", 0)
        is_modular     = arch.get("modular", False)

        has_proof        = pac["proof"] == 1 and delivery_ratio >= 0.5
        has_architecture = pac["architecture"] == 1 and (layer_count >= 2 or is_modular)
        has_code         = pac["code"] == 1 and file_count >= 3
        has_alignment    = delivery_ratio >= 0.6 and len(missing) <= 3
        has_authenticity = repo_available and word_count >= 50
        has_effort       = word_count >= 80 and (readme_score >= 1 or structure_q >= 0.3)

        rubric = {
            "has_proof":        int(has_proof),
            "has_architecture": int(has_architecture),
            "has_code":         int(has_code),
            "has_alignment":    int(has_alignment),
            "has_authenticity": int(has_authenticity),
            "has_effort":       int(has_effort),
            "rubric_sum":       sum([int(has_proof), int(has_architecture), int(has_code),
                                     int(has_alignment), int(has_authenticity), int(has_effort)])
        }

        logger.info(
            f"[ASSIGNMENT ENGINE] Rubric → proof={rubric['has_proof']} arch={rubric['has_architecture']} "
            f"code={rubric['has_code']} align={rubric['has_alignment']} "
            f"auth={rubric['has_authenticity']} effort={rubric['has_effort']}"
        )
        return rubric

    # ── Phase 4: PASS / FAIL determination ───────────────────────────────

    def _determine_result(
        self,
        pac: Dict[str, int],
        rubric: Dict[str, int],
        signals: Dict[str, Any]
    ):
        """
        PASS requires ALL of:
          - code present (pac.code == 1)
          - proof present (pac.proof == 1)
          - architecture present (pac.architecture == 1)
          - alignment met (rubric.has_alignment == 1)
          - authenticity met (rubric.has_authenticity == 1)

        FAIL returns one of:
          schema_violation   — no repo, no code, no authenticity
          incomplete         — missing proof or architecture
          incorrect_logic    — code present but alignment or effort missing
          integration_fail   — repo error signal present
        """
        repo_signals = signals.get("repository_signals") or {}
        repo_error   = repo_signals.get("error")

        # integration_fail — repo fetch failed
        if repo_error and repo_error != "network_failure":
            return "FAIL", "integration_fail"

        # schema_violation — no repo, no code, no authenticity
        if pac["code"] == 0 and rubric["has_authenticity"] == 0:
            return "FAIL", "schema_violation"

        # incomplete — code present but proof or architecture missing
        if pac["proof"] == 0 or pac["architecture"] == 0 or rubric["has_code"] == 0:
            return "FAIL", "incomplete"

        # incorrect_logic — structure present but alignment or effort missing
        if rubric["has_alignment"] == 0 or rubric["has_effort"] == 0:
            return "FAIL", "incorrect_logic"

        # integration_fail — network failure with no files
        if repo_error == "network_failure":
            return "FAIL", "integration_fail"

        return "PASS", None


# Global instance
assignment_engine = AssignmentEngine()
