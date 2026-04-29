"""
Parikshak Assignment Engine — delegates to Rule Engine.
Single entry point. Returns evaluation_result + failure_type only.
No scoring. No weights. No fallback.
"""
from typing import Dict, Any
import logging

from .rule_engine import rule_engine

logger = logging.getLogger("assignment_engine")


class AssignmentEngine:

    def __init__(self):
        self.authority_level = "CANONICAL_PRIMARY"

    def evaluate_and_assign(
        self,
        task_title: str,
        task_description: str,
        supporting_signals: Dict[str, Any]
    ) -> Dict[str, Any]:
        logger.info(f"[ASSIGNMENT ENGINE] Evaluating: {task_title[:60]}")

        result = rule_engine.evaluate(supporting_signals)
        result["canonical_authority"] = True
        result["evaluation_basis"]    = "parikshak_rule_engine"

        logger.info(
            f"[ASSIGNMENT ENGINE] {result['evaluation_result']} | "
            f"failure_type={result['failure_type']}"
        )
        return result


# Global instance
assignment_engine = AssignmentEngine()
