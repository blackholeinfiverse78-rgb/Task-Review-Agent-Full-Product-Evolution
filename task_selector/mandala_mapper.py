import json
import os
import logging
from typing import Dict, Any

logger = logging.getLogger("mandala_mapper")

class MandalaMapper:
    def __init__(self):
        self.db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "db", "niyantran_tasks.json")
        self._load_db()

    def _load_db(self):
        try:
            with open(self.db_path, "r", encoding="utf-8") as f:
                tasks = json.load(f)
            self.task_map = {task["task_id"]: task for task in tasks}
        except Exception as e:
            logger.error(f"Failed to load task DB for mandala mapping: {e}")
            self.task_map = {}

    def map_task_to_context(self, task_id: str) -> Dict[str, Any]:
        """
        Map task to BHIV product context using EXACT DB lookups.
        No keyword guessing allowed.
        """
        if task_id not in self.task_map:
            raise ValueError(
                f"MANDALA_HARD_REJECT: Task ID '{task_id}' not found in DB. "
                "Mapping is DB-driven only."
            )

        task = self.task_map[task_id]
        
        mapping = task.get("mandala_mapping", {})
        return {
            "product": mapping.get("product"),
            "layer": mapping.get("layer"),
            "subsystem": mapping.get("subsystem"),
            "capability": mapping.get("capability"),
            "mapping_source": "db_exact_match"
        }

mandala_mapper = MandalaMapper()
