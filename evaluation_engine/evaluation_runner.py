"""
Parikshak Evaluation Engine — Runner (Sri Satya)
=================================================
Single entry point for the evaluation layer.

Flow:
  1. Receive 7-field pipeline output from upstream (Ishan)
  2. Emit submission observability event
  3. Validate against 7-field contract
  4. Emit evaluation observability event
  5. Return validated 7-field output to pipeline

This layer does NOT own:
  - Traversal authority
  - Governance approval or routing
  - Assignment release
  - Workflow orchestration
"""
import os
from typing import Dict, Any, List
from evaluation_engine.event_store import EventStore
from evaluation_engine.eval_observability import ObservabilityEmitter
from evaluation_engine.contract_monitor import ContractMonitor

_DEFAULT_STATE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "storage", "evaluation_state"
)


class EvaluationRunner:
    """
    Pure deterministic evaluation runner.
    Takes 7-field pipeline output, validates contract,
    ensures observability, and returns unmodified output.
    """

    def __init__(self, state_dir: str = None):
        state_dir = state_dir or _DEFAULT_STATE_DIR
        self._store = EventStore(state_dir)
        self._emitter = ObservabilityEmitter(self._store)
        self._monitor = ContractMonitor(self._emitter)

    def evaluate(self, pipeline_output: Dict[str, Any],
                 graph_traversal_trace: List[str] = None) -> Dict[str, Any]:
        """
        Evaluate a 7-field pipeline output.

        1. Emits submission event
        2. Validates 7-field contract
        3. Emits evaluation event
        4. Returns the validated output unmodified

        Raises: ValueError if contract is violated.
        """
        trace_id = pipeline_output.get("trace_id", "UNKNOWN")
        submission_id = pipeline_output.get("submission_id", "UNKNOWN")

        self._emitter.emit_submission(trace_id, submission_id)

        violations = self._monitor.validate(pipeline_output, trace_id)
        if violations:
            raise ValueError(f"HARD FAIL: Contract violations detected: {violations}")

        self._emitter.emit_evaluation(
            trace_id=trace_id,
            result=pipeline_output["evaluation_result"],
            task_id=pipeline_output["selected_task_id"],
            failure_type=pipeline_output.get("failure_type"),
        )

        return pipeline_output

    def get_all_observability_events(self) -> List[Dict[str, Any]]:
        return self._emitter.get_all_events()

    def reset(self) -> None:
        """Reset all state. For testing only."""
        self._store.reset()


# Global instance — uses default storage path
evaluation_runner = EvaluationRunner()
