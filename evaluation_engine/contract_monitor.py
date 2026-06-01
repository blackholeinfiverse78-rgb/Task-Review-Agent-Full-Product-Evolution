"""
Parikshak Operational Governance — Contract Monitor
=====================================================
Monitors pipeline outputs for 7-field contract violations.
Reports all violations via observability emitter — never silently passes.

7-field contract (Sri Satya evaluation layer boundary):
    trace_id, submission_id, evaluation_result, failure_type,
    selected_task_id, selection_reason, source

Note: schema_version is Ishan's pipeline field and is stripped
before the output reaches EvaluationRunner.
"""
from typing import Dict, Any, List
from evaluation_engine.eval_observability import ObservabilityEmitter

REQUIRED_FIELDS = {
    "trace_id", "submission_id", "evaluation_result",
    "failure_type", "selected_task_id", "selection_reason", "source",
}
VALID_EVAL_RESULTS = {"PASS", "FAIL"}
VALID_FAILURE_TYPES = {"schema_violation", "incomplete", "incorrect_logic", "integration_fail", None}
REQUIRED_SOURCE = "task_graph"


class ContractMonitor:
    """
    Validates pipeline outputs against the 7-field contract.
    Reports all violations via observability emitter.
    """

    def __init__(self, emitter: ObservabilityEmitter):
        self._emitter = emitter

    def validate(self, output: Dict[str, Any], trace_id: str = None) -> List[str]:
        """
        Validate a pipeline output against the 7-field contract.
        Returns list of violations (empty = valid).
        Each violation is emitted as a CRITICAL observability event.
        """
        t_id = trace_id or output.get("trace_id", "UNKNOWN")
        violations = []

        missing = REQUIRED_FIELDS - set(output.keys())
        if missing:
            violations.append(f"Missing fields: {missing}")

        extra = set(output.keys()) - REQUIRED_FIELDS
        if extra:
            violations.append(f"Unexpected fields: {extra}")

        eval_result = output.get("evaluation_result")
        if eval_result not in VALID_EVAL_RESULTS:
            violations.append(f"Invalid evaluation_result: {eval_result}")

        ft = output.get("failure_type")
        if ft not in VALID_FAILURE_TYPES:
            violations.append(f"Invalid failure_type: {ft}")

        if eval_result == "PASS" and ft is not None:
            violations.append("PASS result but failure_type is not null")

        if eval_result == "FAIL" and ft is None:
            violations.append("FAIL result but failure_type is null")

        if output.get("source") != REQUIRED_SOURCE:
            violations.append(f"Invalid source: {output.get('source')}")

        for v in violations:
            self._emitter.emit_contract_violation(t_id, v)

        return violations
