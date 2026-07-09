from typing import Dict, Any, Optional
import logging

from evaluation_engine.review_packet_parser import review_packet_parser
from evaluation_engine.validator import validator as registry_validator, ValidationStatus
from evaluation_engine.signal_engine import signal_engine as signal_collector
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
        pdf_text: str = "",
        task_id: Optional[str] = None
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

        # Step 2.5: Domain context (static)
        supporting_signals["domain"] = "universal"
        supporting_signals["domain_expected_features"] = []
        supporting_signals["domain_min_files"] = 3

        # Step 3: Rule Engine evaluation
        evaluation = assignment_engine.evaluate_and_assign(
            task_title=task_title,
            task_description=task_description,
            supporting_signals=supporting_signals,
            task_id=task_id
        )

        failure_type = evaluation.get("failure_type")
        missing_features = supporting_signals.get("missing_features", [])
        
        improvement_hints = []
        if failure_type == "schema_violation":
            improvement_hints.extend([
                "Ensure task title is at least 5 words and description is detailed (> 50 words).",
                "Verify the repository link is present and valid if required."
            ])
        elif failure_type == "incomplete":
            improvement_hints.extend([
                "Provide a README.md file documenting the project setup.",
                "Include unit tests under a tests/ folder (e.g. test_api.py).",
                "Add structured documentation or architectural comments.",
                "Ensure the repository has at least 3 implementation files."
            ])
        elif failure_type == "incorrect_logic":
            improvement_hints.extend([
                "Improve test coverage and code complexity alignment.",
                "Satisfy at least 60% of the expected task features."
            ])
            for f in missing_features:
                improvement_hints.append(f"Implement missing feature: {f}")
        elif failure_type == "integration_fail":
            improvement_hints.extend([
                "Verify repository metadata (e.g. check that metadata name is present).",
                "Verify downstream integration points and API registration."
            ])
        else:
            improvement_hints.append("Ecosystem requirements are fully met. Ready for production.")

        return {
            "evaluation_result": evaluation["evaluation_result"],
            "failure_type": failure_type,
            "reason": evaluation.get("reason", ""),
            "pac": evaluation.get("pac", {}),
            "rubric": evaluation.get("rubric", {}),
            "canonical_authority": evaluation.get("canonical_authority", False),
            "missing_features": missing_features,
            "improvement_hints": improvement_hints
        }

evaluation_orchestrator = EvaluationOrchestrator()
