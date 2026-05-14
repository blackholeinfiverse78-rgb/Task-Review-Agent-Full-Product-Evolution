"""
Parikshak Assignment Engine — delegates to Rule Engine.
Single entry point. Returns evaluation_result + failure_type only.
No scoring. No weights. No fallback.
"""
from typing import Dict, Any
import logging

from evaluation_engine.rule_engine import rule_engine

logger = logging.getLogger("assignment_engine")


class AssignmentEngine:

    def __init__(self):
        self.authority_level = "CANONICAL_PRIMARY"

    def evaluate_and_assign(
        self,
        task_title: str,
        task_description: str,
        supporting_signals: Dict[str, Any],
        task_id: Optional[str] = None
    ) -> Dict[str, Any]:
        logger.info(f"[ASSIGNMENT ENGINE] Evaluating: {task_title[:60]}")

        # Phase 2: DB as SINGLE SOURCE OF TRUTH
        rules = None
        if task_id:
            try:
                from task_selector.task_graph_engine import task_graph_engine
                task_data = task_graph_engine.get_task(task_id)
                if task_data:
                    rules = task_data.get("evaluation_rules")
                    logger.info(f"[ASSIGNMENT ENGINE] Loaded rules from DB for {task_id}")
            except Exception as e:
                logger.error(f"[ASSIGNMENT ENGINE] Error loading rules for {task_id}: {e}")

        result = rule_engine.evaluate(supporting_signals, rules=rules)
        result["canonical_authority"] = True
        result["evaluation_basis"]    = "parikshak_rule_engine"

        logger.info(
            f"[ASSIGNMENT ENGINE] {result['evaluation_result']} | "
            f"failure_type={result['failure_type']}"
        )
        return result


# Global instance
assignment_engine = AssignmentEngine()
