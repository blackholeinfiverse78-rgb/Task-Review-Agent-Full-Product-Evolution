"""
Parikshak Rule Engine — STEP 2
Deterministic binary rule checks only.
Runs checks in order. First failure stops execution.
No scoring. No weights. No fallback.

Output:
  { "evaluation_result": "PASS" | "FAIL", "failure_type": "<type> | null" }

failure_type values:
  schema_violation  — missing repo, missing trace_id, invalid module_id
  incomplete        — no proof, no architecture, no code, < 3 files
  incorrect_logic   — code present but alignment or effort missing
  integration_fail  — repo fetch error, bucket write failure
"""
from typing import Dict, Any, Tuple, Optional
import logging

logger = logging.getLogger("rule_engine")

FAILURE_TYPES = {"schema_violation", "incomplete", "incorrect_logic", "integration_fail"}


class RuleEngine:
    """
    Deterministic rule resolver.
    Runs 4 checks in strict order. First failure → stop + return failure_type.
    Same input always produces same output.
    """

    def evaluate(self, signals: Dict[str, Any], rules: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Run all checks in order. Return PASS or FAIL with failure_type, along with pac and rubric dicts.

        Args:
            signals: supporting_signals dict from signal_engine
            rules: optional task-specific rules from DB

        Returns:
            { "evaluation_result": "PASS"|"FAIL", "failure_type": str|None, "pac": dict, "rubric": dict }
        """
        logger.info("[RULE ENGINE] Starting deterministic evaluation")
        
        # Use provided rules or fallback to defaults
        active_rules = rules or {
            "schema": {"min_word_count": 50, "require_repo": False},
            "completeness": {"min_files": 3, "require_proof": True, "require_arch": True},
            "logic": {"min_delivery_ratio": 0.6, "max_missing_features": 3, "min_word_count_for_effort": 80}
        }

        # Calculate pac and rubric upfront
        # 1. code_present
        repo_available = signals.get("repository_available", False)
        repo_signals   = signals.get("repository_signals") or {}
        structure      = repo_signals.get("structure", {})
        file_count     = structure.get("total_files", 0)
        code_present   = repo_available and file_count > 0

        # 2. proof_present
        quality        = repo_signals.get("quality", {})
        readme_val     = quality.get("readme_val", 0)
        components     = repo_signals.get("components", {})
        test_files     = components.get("tests", [])
        doc_files      = components.get("docs", [])
        proof_present  = readme_val >= 1 or len(test_files) > 0 or len(doc_files) > 0

        # 3. arch_present
        arch           = repo_signals.get("architecture", {})
        layer_count    = arch.get("layer_count", 0)
        is_modular     = arch.get("modular", False)
        desc_signals   = signals.get("description_signals") or {}
        title_signals  = signals.get("title_signals") or {}
        arch_keywords  = {"architecture", "layer", "service", "module", "component",
                          "design", "flow", "pipeline", "orchestrat"}
        desc_text      = str(desc_signals).lower()
        title_text     = str(title_signals).lower()
        has_arch_kw    = any(kw in desc_text or kw in title_text for kw in arch_keywords)
        arch_present   = layer_count >= 2 or is_modular or (code_present and has_arch_kw)

        pac = {
            "code": 1 if code_present else 0,
            "architecture": 1 if arch_present else 0,
            "proof": 1 if proof_present else 0
        }

        # 4. rubric alignment
        logic_rules    = active_rules.get("logic", {})
        min_ratio      = logic_rules.get("min_delivery_ratio", 0.6)
        max_missing    = logic_rules.get("max_missing_features", 3)
        min_effort_w   = logic_rules.get("min_word_count_for_effort", 80)

        evd            = signals.get("expected_vs_delivered_evidence", {})
        delivery_ratio = evd.get("delivery_ratio", 0.0)
        missing        = signals.get("missing_features", [])
        desc_word_count = desc_signals.get("word_count", 0) if isinstance(desc_signals, dict) else 0

        alignment = delivery_ratio >= min_ratio and len(missing) <= max_missing
        effort    = desc_word_count >= min_effort_w or readme_val >= 1
        
        comp_rules     = active_rules.get("completeness", {})
        min_files      = comp_rules.get("min_files", 3)
        has_code_count = file_count >= min_files

        rubric = {
            "has_alignment": 1 if alignment else 0,
            "has_effort": 1 if effort else 0,
            "has_code": 1 if has_code_count else 0
        }

        for check_fn in (
            self._check_schema,
            self._check_completeness,
            self._check_logic,
            self._check_integration,
        ):
            # Pass rules to each check
            failure_type = check_fn(signals, active_rules)
            if failure_type is not None:
                logger.info(f"[RULE ENGINE] FAIL — {failure_type}")
                return {
                    "evaluation_result": "FAIL",
                    "failure_type": failure_type,
                    "pac": pac,
                    "rubric": rubric
                }

        logger.info("[RULE ENGINE] PASS — all checks passed")
        return {
            "evaluation_result": "PASS",
            "failure_type": None,
            "pac": pac,
            "rubric": rubric
        }

    # ── Check 1: Schema ───────────────────────────────────────────────────

    def _check_schema(self, signals: Dict[str, Any], rules: Dict[str, Any]) -> Optional[str]:
        """
        FAIL if:
        - no repository provided AND word_count < rules['schema']['min_word_count']
        """
        schema_rules   = rules.get("schema", {})
        min_words      = schema_rules.get("min_word_count", 50)
        require_repo   = schema_rules.get("require_repo", False)
        
        repo_available = signals.get("repository_available", False)
        desc           = signals.get("description_signals") or {}
        word_count     = desc.get("word_count", 0) if isinstance(desc, dict) else 0

        if require_repo and not repo_available:
            logger.info("[RULE ENGINE] schema_violation: repository required but missing")
            return "schema_violation"

        if not repo_available and word_count < min_words:
            logger.info(f"[RULE ENGINE] schema_violation: no repo + description < {min_words} words")
            return "schema_violation"

        return None

    # ── Check 2: Completeness ─────────────────────────────────────────────

    def _check_completeness(self, signals: Dict[str, Any], rules: Dict[str, Any]) -> Optional[str]:
        """
        FAIL if:
        - code not present (no repo or 0 files)
        - proof not present (no README, no tests, no docs)
        - architecture not present (no layers, no arch keywords)
        - file count < rules['completeness']['min_files']
        """
        comp_rules     = rules.get("completeness", {})
        min_files      = comp_rules.get("min_files", 3)
        require_proof  = comp_rules.get("require_proof", True)
        require_arch   = comp_rules.get("require_arch", True)

        repo_signals   = signals.get("repository_signals") or {}
        repo_available = signals.get("repository_available", False)
        structure      = repo_signals.get("structure", {})
        file_count     = structure.get("total_files", 0)
        quality        = repo_signals.get("quality", {})
        readme_val   = quality.get("readme_val", 0)
        components     = repo_signals.get("components", {})
        test_files     = components.get("tests", [])
        doc_files      = components.get("docs", [])
        arch           = repo_signals.get("architecture", {})
        layer_count    = arch.get("layer_count", 0)
        is_modular     = arch.get("modular", False)
        desc_signals   = signals.get("description_signals") or {}
        title_signals  = signals.get("title_signals") or {}
        arch_keywords  = {"architecture", "layer", "service", "module", "component",
                          "design", "flow", "pipeline", "orchestrat"}
        desc_text      = str(desc_signals).lower()
        title_text     = str(title_signals).lower()
        has_arch_kw    = any(kw in desc_text or kw in title_text for kw in arch_keywords)

        code_present  = repo_available and file_count > 0
        proof_present = readme_val >= 1 or len(test_files) > 0 or len(doc_files) > 0
        arch_present  = layer_count >= 2 or is_modular or (code_present and has_arch_kw)

        if not code_present:
            logger.info("[RULE ENGINE] incomplete: no code present")
            return "incomplete"
        if require_proof and not proof_present:
            logger.info("[RULE ENGINE] incomplete: no proof present")
            return "incomplete"
        if require_arch and not arch_present:
            logger.info("[RULE ENGINE] incomplete: no architecture present")
            return "incomplete"
        if file_count < min_files:
            logger.info(f"[RULE ENGINE] incomplete: file_count < {min_files}")
            return "incomplete"

        return None

    # ── Check 3: Logic ────────────────────────────────────────────────────

    def _check_logic(self, signals: Dict[str, Any], rules: Dict[str, Any]) -> Optional[str]:
        """
        FAIL if:
        - delivery_ratio < min_delivery_ratio OR missing_features > max_missing_features
        - word_count < min_word_count_for_effort AND readme_val < 1
        """
        logic_rules    = rules.get("logic", {})
        min_ratio      = logic_rules.get("min_delivery_ratio", 0.6)
        max_missing    = logic_rules.get("max_missing_features", 3)
        min_effort_w   = logic_rules.get("min_word_count_for_effort", 80)

        evd            = signals.get("expected_vs_delivered_evidence", {})
        delivery_ratio = evd.get("delivery_ratio", 0.0)
        missing        = signals.get("missing_features", [])
        desc_signals   = signals.get("description_signals") or {}
        word_count     = desc_signals.get("word_count", 0) if isinstance(desc_signals, dict) else 0
        repo_signals   = signals.get("repository_signals") or {}
        quality        = repo_signals.get("quality", {})
        readme_val     = quality.get("readme_val", 0)

        alignment = delivery_ratio >= min_ratio and len(missing) <= max_missing
        effort    = word_count >= min_effort_w or readme_val >= 1

        if not alignment:
            logger.info(
                f"[RULE ENGINE] incorrect_logic: delivery_ratio={delivery_ratio:.2f} "
                f"missing={len(missing)}"
            )
            return "incorrect_logic"
        if not effort:
            logger.info(
                f"[RULE ENGINE] incorrect_logic: word_count={word_count} readme_val={readme_val}"
            )
            return "incorrect_logic"

        return None

    # ── Check 4: Integration ──────────────────────────────────────────────

    def _check_integration(self, signals: Dict[str, Any], rules: Dict[str, Any]) -> Optional[str]:
        """
        FAIL if:
        - repository_signals has error field (not network_failure)
        - repository_available=True but structure is empty
        """
        repo_signals   = signals.get("repository_signals") or {}
        repo_available = signals.get("repository_available", False)
        repo_error     = repo_signals.get("error")

        if repo_error and repo_error != "network_failure":
            logger.info(f"[RULE ENGINE] integration_fail: repo error={repo_error}")
            return "integration_fail"

        if repo_available and not repo_signals.get("metadata", {}).get("name"):
            logger.info("[RULE ENGINE] integration_fail: repo_available but metadata missing")
            return "integration_fail"

        return None


# Global instance
rule_engine = RuleEngine()
