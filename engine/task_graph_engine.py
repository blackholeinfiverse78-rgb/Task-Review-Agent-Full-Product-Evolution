import json
import os

class TaskGraphEngine:
    def __init__(self):
        self.db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'db', 'niyantran_tasks.json')
        self.tasks = self._load_tasks()

    def _load_tasks(self):
        with open(self.db_path, 'r') as f:
            tasks = json.load(f)
        return {t['task_id']: t for t in tasks}

    def resolve_next_task(self, current_task_id: str, score: float) -> str:
        """
        Deterministically resolve the next task based solely on score.
        score >= 6 -> next_tasks[0]
        score < 6 -> failure_tasks[0]
        """
        task = self.tasks.get(current_task_id)
        if not task:
            # Fallback to the first foundational task if not found
            return "T-GOV-001"
            
        if score >= 6:
            if task.get("next_tasks") and len(task["next_tasks"]) > 0:
                return task["next_tasks"][0]
            return "COMPLETED"
        else:
            if task.get("failure_tasks") and len(task["failure_tasks"]) > 0:
                return task["failure_tasks"][0]
            return "T-GOV-F00"
            
    def get_task(self, task_id: str) -> dict:
        return self.tasks.get(task_id, {})

task_graph_engine = TaskGraphEngine()
