"""
Parikshak Task Graph Engine — STEP 4
Deterministic graph traversal. No scoring. No fallback.

Routing:
  evaluation_result == "PASS"  → next_tasks[0]
  evaluation_result == "FAIL"  → failure_tasks[failure_type][0]

If mapping missing → HARD REJECT (raises ValueError)
"""
import json
import os
from typing import Dict, Any
import logging

logger = logging.getLogger("task_graph_engine")

_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "db", "niyantran_tasks.json")

REQUIRED_TASK_FIELDS = {
    "task_id", "dharma", "completion_signals",
    "failure_type", "prerequisites", "next_tasks", "failure_tasks", "constraints",
    "mandala_mapping"
}

VALID_FAILURE_TYPES = {"schema_violation", "incomplete", "incorrect_logic", "integration_fail"}


class TaskGraphEngine:

    def __init__(self, db_path: str = _DB_PATH):
        self._db_path = db_path
        self._tasks: Dict[str, Dict[str, Any]] = {}
        self._load()

    def _load(self) -> None:
        try:
            with open(self._db_path, "r", encoding="utf-8") as f:
                raw = json.load(f)
        except Exception as e:
            raise RuntimeError(f"TASK_DB_LOAD_FAILURE: Cannot load task DB — {e}")

        tasks = {}
        for task in raw:
            task_id = task.get("task_id")
            if not task_id:
                raise ValueError("TASK_DB_INVALID: task missing task_id field")

            missing = REQUIRED_TASK_FIELDS - set(task.keys())
            if missing:
                raise ValueError(
                    f"TASK_DB_INVALID: task '{task_id}' missing required fields: {missing}"
                )

            failure_tasks = task.get("failure_tasks", {})
            if not isinstance(failure_tasks, dict):
                raise ValueError(
                    f"TASK_DB_INVALID: task '{task_id}' failure_tasks must be a dict "
                    f"keyed by failure_type"
                )

            tasks[task_id] = task

        self._tasks = tasks
        logger.info(f"[TASK GRAPH ENGINE] Loaded {len(self._tasks)} tasks")

    def traverse(
        self,
        current_task_id: str,
        evaluation_result: str,
        failure_type: str = None
    ) -> Dict[str, Any]:
        """
        Deterministic traversal. No scoring. No fallback.

        Args:
            current_task_id:   task just evaluated
            evaluation_result: "PASS" or "FAIL"
            failure_type:      one of VALID_FAILURE_TYPES, or None if PASS

        Returns:
            { selected_task_id, selection_reason, source }

        Raises:
            ValueError on any undefined case
        """
        if evaluation_result not in ("PASS", "FAIL"):
            raise ValueError(
                f"GRAPH_HARD_REJECT: evaluation_result must be PASS or FAIL, "
                f"got '{evaluation_result}'"
            )

        task = self._tasks.get(current_task_id)
        if not task:
            raise ValueError(
                f"GRAPH_HARD_REJECT: task_id '{current_task_id}' not in task DB. "
                f"No fallback permitted."
            )

        if evaluation_result == "PASS":
            candidates = task.get("next_tasks", [])
            if not candidates:
                selected = "TERMINAL_STATE"
                reason = "PASS → next_tasks empty (TERMINAL_STATE)"
            else:
                selected = candidates[0]
                reason = f"PASS → next_tasks[0] = {selected}"

        else:  # FAIL
            if failure_type not in VALID_FAILURE_TYPES:
                raise ValueError(
                    f"GRAPH_HARD_REJECT: failure_type '{failure_type}' is not valid. "
                    f"Must be one of {VALID_FAILURE_TYPES}."
                )
            failure_map = task.get("failure_tasks", {})
            if failure_type not in failure_map:
                raise ValueError(
                    f"GRAPH_HARD_REJECT: task '{current_task_id}' has no failure_tasks "
                    f"mapping for failure_type '{failure_type}'."
                )
            candidates = failure_map[failure_type]
            if not candidates:
                raise ValueError(
                    f"GRAPH_HARD_REJECT: task '{current_task_id}' failure_tasks['{failure_type}'] "
                    f"is empty."
                )
            selected = candidates[0]
            reason = f"FAIL({failure_type}) → failure_tasks['{failure_type}'][0] = {selected}"

        if selected not in self._tasks and selected not in ("COMPLETED", "TERMINAL_STATE"):
            raise ValueError(
                f"GRAPH_HARD_REJECT: selected task_id '{selected}' not in task DB."
            )

        logger.info(f"[TASK GRAPH ENGINE] {current_task_id} → {selected} | {reason}")

        return {
            "selected_task_id": selected,
            "selection_reason": reason,
            "source":           "task_graph"
        }

    def get_task(self, task_id: str) -> Dict[str, Any]:
        if task_id not in self._tasks:
            raise ValueError(
                f"GRAPH_HARD_REJECT: task_id '{task_id}' not in task DB."
            )
        return self._tasks[task_id]

    def validate_task_id(self, task_id: str) -> bool:
        return task_id in self._tasks


# Global instance
task_graph_engine = TaskGraphEngine()
