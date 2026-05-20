"""
Parikshak Task Selector — Phase 5
Unified deterministic task selection combining:
  1. Graph Engine    — traverses task_database.json graph edges
  2. Mandala Mapper  — maps task context to BHIV product
  3. Task Selection  — falls back to Niyantran graph if task_id unknown

Output:
  {
    "task_id":          str,
    "selection_reason": str,
    "source":           "task_graph"
  }

BOUNDARY RULES:
  - NO task generation
  - Same input ALWAYS produces same task_id
  - Graph DB is the primary source; Niyantran graph is fallback
"""
from typing import Dict, Any, Optional
import logging

from .graph_engine import graph_engine
from .mandala_mapper import mandala_mapper
from .task_selection_engine import task_selection_engine

logger = logging.getLogger("task_selector")


class TaskSelector:
    """
    Unified deterministic task selector.

    Priority:
      1. If current_task_id is in task_database → use graph_engine traversal
      2. Else → use task_selection_engine (Niyantran graph by score/decision/difficulty)

    Mandala context enriches the selection_reason in both paths.
    """

    SOURCE = "task_graph"

    def select(
        self,
        score_10: float,
        decision: str,
        task_title: str = "",
        task_description: str = "",
        current_task_id: Optional[str] = None,
        current_difficulty: str = "beginner",
    ) -> Dict[str, Any]:
        """
        Select next task deterministically.

        Args:
            score_10:           Evaluation score 0–10
            decision:           "APPROVED" or "REJECTED"
            task_title:         Submitted task title (for Mandala mapping)
            task_description:   Submitted task description (for Mandala mapping)
            current_task_id:    task_id just evaluated (None if first submission)
            current_difficulty: Current difficulty level

        Returns:
            {task_id, title, task_type, difficulty, objective, dharma,
             product, layer, selection_reason, source, ...}
        """
        # Step 1: Map context via Mandala
        context = mandala_mapper.map_task_to_context(task_title, task_description)
        product = context.get("product", "niyantran")
        layer   = context.get("layer", "governance")

        logger.info(
            f"[TASK SELECTOR] score={score_10} decision={decision} "
            f"current_task={current_task_id} product={product}"
        )

        # Step 2: Try graph traversal if current_task_id is known
        if current_task_id and graph_engine.validate_task_id(current_task_id):
            result = graph_engine.traverse(current_task_id, score_10, decision)
            result["source"] = self.SOURCE
            result["mandala_context"] = {
                "product": product,
                "layer": layer,
                "mapping_confidence": context.get("mapping_confidence", 0),
                "mapping_source": context.get("mapping_source", ""),
            }
            logger.info(
                f"[TASK SELECTOR] graph_engine path: {current_task_id} -> {result['next_task_id']}"
            )
            return self._normalise(result)

        # Step 3: Fallback to Niyantran task_selection_engine
        result = task_selection_engine.select_next_task(
            score_10=score_10,
            decision=decision,
            current_difficulty=current_difficulty,
            product_context={
                "product": product,
                "layer": layer,
                "allowed_next_tasks": context.get("allowed_next_tasks", []),
            }
        )
        result["source"] = self.SOURCE
        result["mandala_context"] = {
            "product": product,
            "layer": layer,
            "mapping_confidence": context.get("mapping_confidence", 0),
            "mapping_source": context.get("mapping_source", ""),
        }

        # Enrich with full task data from DB if available
        db_task = graph_engine.get_task(result["next_task_id"])
        if db_task:
            result["objective"]          = db_task.get("description", "")
            result["dharma"]             = db_task.get("dharma", "")
            result["completion_signals"] = db_task.get("completion_signals", [])
            result["subsystem"]          = db_task.get("subsystem", "")
            result["capability"]         = db_task.get("capability", "")

        logger.info(
            f"[TASK SELECTOR] niyantran_graph path: -> {result['next_task_id']}"
        )
        return self._normalise(result)

    def _normalise(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure output always has the required contract fields."""
        return {
            "task_id":          result.get("next_task_id", "NT-COR-B-001"),
            "title":            result.get("title", "Foundational Implementation Correction"),
            "task_type":        result.get("task_type", "correction"),
            "difficulty":       result.get("difficulty", "beginner"),
            "objective":        result.get("objective", "Complete the assigned task"),
            "dharma":           result.get("dharma", ""),
            "product":          result.get("product", result.get("mandala_context", {}).get("product", "niyantran")),
            "layer":            result.get("layer", result.get("mandala_context", {}).get("layer", "governance")),
            "subsystem":        result.get("subsystem", ""),
            "capability":       result.get("capability", ""),
            "completion_signals": result.get("completion_signals", []),
            "selection_reason": result.get("selection_reason", ""),
            "source":           self.SOURCE,
            "mandala_context":  result.get("mandala_context", {}),
            "branch":           result.get("branch", ""),
            "context_source":   result.get("context_source", ""),
        }


# Global instance
task_selector = TaskSelector()
