from typing import Dict, Any, Optional
import logging

from evaluation_engine.review_packet_parser import review_packet_parser
from evaluation_engine.validator import validator as registry_validator, ValidationStatus
from evaluation_engine.signal_engine import signal_engine as signal_collector
from evaluation_engine.domain_router import domain_router
from evaluation_engine.assignment_engine import assignment_engine

logger = logging.getLogger("evaluation_orchestrator")

class EvaluationOrchestrator:
    def evaluate_submission(
        self,
        task_title: str,
        task_description: str,
        repository_url: Optional[str] = None,
        module_id: str = "task-review-agent",
        schema_version: str = "v1.0",
        pdf_text: str = ""
    ) -> Dict[str, Any]:
        
        # Step 0: REVIEW_PACKET hard gate
        packet_result = review_packet_parser.enforce_packet_requirement(".")
        if not packet_result["valid"]:
            return {"evaluation_result": "FAIL", "failure_type": "schema_violation", "reason": f"REVIEW_PACKET hard gate: {packet_result['reason']}"}

        # Step 1: Registry validation
        registry_result = registry_validator.validate_complete(module_id, schema_version)
        if registry_result.status == ValidationStatus.INVALID:
            return {"evaluation_result": "FAIL", "failure_type": "schema_violation", "reason": f"Registry validation failed: {registry_result.reason}"}

        # Step 2: Signal collection
        supporting_signals = signal_collector.collect_supporting_signals(
            task_title=task_title,
            task_description=task_description,
            repository_url=repository_url,
            pdf_text=pdf_text
        )

        # Step 2.5: Domain routing
        try:
            supporting_signals = domain_router.enrich_signals(
                supporting_signals, task_title, task_description
            )
        except ValueError as e:
            return {"evaluation_result": "FAIL", "failure_type": "schema_violation", "reason": str(e)}

        # Step 3: Rule Engine evaluation
        evaluation = assignment_engine.evaluate_and_assign(
            task_title=task_title,
            task_description=task_description,
            supporting_signals=supporting_signals
        )

        return {
            "evaluation_result": evaluation["evaluation_result"],
            "failure_type": evaluation.get("failure_type"),
            "reason": evaluation.get("reason", "")
        }

evaluation_orchestrator = EvaluationOrchestrator()
