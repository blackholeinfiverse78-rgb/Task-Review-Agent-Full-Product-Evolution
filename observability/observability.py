import json
import os
from datetime import datetime
from typing import Dict, Any, List
from db.persistent_storage import FileLock

class SystemObserver:
    """
    Thread-safe and process-safe observability layer for the Deterministic Core.
    Tracks execution metrics, failure distributions, and trace history.
    """
    def __init__(self, log_dir: str = "storage/observability"):
        self.log_dir = log_dir
        self._metrics_file = os.path.join(log_dir, "metrics.json")
        self._lock_file = self._metrics_file + ".lock"
        self._lock = FileLock(self._lock_file)
        self._trace_log = os.path.join(log_dir, "trace_history.log")
        
        if not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
            
        self._initialize_metrics()

    def _initialize_metrics(self):
        with self._lock:
            if not os.path.exists(self._metrics_file):
                initial = {
                    "v": "1.0",
                    "total_executions": 0,
                    "pass_count": 0,
                    "fail_count": 0,
                    "failure_distribution": {
                        "schema_violation": 0,
                        "incomplete": 0,
                        "incorrect_logic": 0,
                        "integration_fail": 0
                    },
                    "hard_reject_count": 0,
                    "last_updated": datetime.now().isoformat()
                }
                with open(self._metrics_file, "w") as f:
                    json.dump(initial, f, indent=2)

    def log_execution(self, output: Dict[str, Any], is_hard_reject: bool = False):
        """Records a single execution event"""
        with self._lock:
            try:
                # 1. Update Metrics
                with open(self._metrics_file, "r") as f:
                    metrics = json.load(f)
                
                if is_hard_reject:
                    metrics["hard_reject_count"] += 1
                else:
                    metrics["total_executions"] += 1
                    if output.get("evaluation_result") == "PASS":
                        metrics["pass_count"] += 1
                    else:
                        metrics["fail_count"] += 1
                        ftype = output.get("failure_type", "unknown")
                        if ftype in metrics["failure_distribution"]:
                            metrics["failure_distribution"][ftype] += 1
                        else:
                            metrics["failure_distribution"]["other"] = metrics["failure_distribution"].get("other", 0) + 1

                metrics["last_updated"] = datetime.now().isoformat()
                
                with open(self._metrics_file, "w") as f:
                    json.dump(metrics, f, indent=2)

                # 2. Append to Trace Log (Read-only history)
                log_entry = {
                    "timestamp": datetime.now().isoformat(),
                    "trace_id": output.get("trace_id"),
                    "submission_id": output.get("submission_id"),
                    "result": output.get("evaluation_result"),
                    "failure": output.get("failure_type"),
                    "next_task": output.get("selected_task_id"),
                    "is_hard_reject": is_hard_reject
                }
                with open(self._trace_log, "a") as f:
                    f.write(json.dumps(log_entry) + "\n")
                    
            except Exception as e:
                # Observability failure should never crash the core
                print(f"[OBSERVABILITY ERROR] {e}")

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            with open(self._metrics_file, "r") as f:
                return json.load(f)

    def log_observability_event(self, level: str, message: str, payload: Dict[str, Any]):
        with self._lock:
            try:
                log_file = os.path.join(self.log_dir, "governance_events.jsonl")
                entry = {
                    "timestamp": datetime.now().isoformat(),
                    "level": level,
                    "message": message,
                    "payload": payload
                }
                with open(log_file, "a", encoding="utf-8") as f:
                    f.write(json.dumps(entry) + "\n")
            except Exception as e:
                print(f"[OBSERVABILITY ERROR] {e}")

# Global observer instance
observer = SystemObserver()
observability = observer
