"""
Parikshak Production Decision Engine — Phase 5
Operates on eval_res = PASS | FAIL from assignment engine.
No numeric scoring. No thresholds. No weights.
Generates: strengths, failures, root_cause, learning_feedback, next_direction.
"""
from typing import Dict, Any, List
import logging

logger = logging.getLogger("decision_engine")

FAILURE_TYPE_LABELS = {
    "schema_violation": "Schema or structural violation detected",
    "incomplete":       "Submission is incomplete — missing proof, architecture, or code",
    "incorrect_logic":  "Implementation present but requirements not aligned",
    "integration_fail": "Repository or integration failure — cannot verify implementation",
}


class ProductionDecisionEngine:

    def make_decision(
        self,
        evaluation_result: Dict[str, Any],
        supporting_signals: Dict[str, Any],
        packet_data: Any = None
    ) -> Dict[str, Any]:
        logger.info("[DECISION ENGINE] Making Phase 5 decision")

        result      = evaluation_result.get("evaluation_result", "FAIL")
        failure_type = evaluation_result.get("failure_type")
        rubric      = evaluation_result.get("rubric", {})
        pac         = evaluation_result.get("pac", {})

        decision     = "APPROVED" if result == "PASS" else "REJECTED"
        task_type    = "advancement" if result == "PASS" else self._task_type_from_failure(failure_type)
        narrative    = self._generate_narrative(result, failure_type, rubric, pac, supporting_signals)

        output = {
            "evaluation_result": result,
            "failure_type":      failure_type,
            "decision":          decision,
            "task_type":         task_type,
            "strengths":         narrative["strengths"],
            "failures":          narrative["failures"],
            "root_cause":        narrative["root_cause"],
            "learning_feedback": narrative["learning_feedback"],
            "next_direction":    narrative["next_direction"],
            "decision_metadata": {
                "engine":  "parikshak_decision_engine",
                "version": "3.0",
                "phase":   5,
                "numeric_scoring": False
            }
        }

        logger.info(f"[DECISION ENGINE] Decision: {decision} | failure_type={failure_type}")
        return output

    def _task_type_from_failure(self, failure_type: str) -> str:
        return {
            "schema_violation": "correction",
            "incomplete":       "correction",
            "incorrect_logic":  "reinforcement",
            "integration_fail": "correction",
        }.get(failure_type or "", "correction")

    def _generate_narrative(
        self,
        result: str,
        failure_type: str,
        rubric: Dict[str, int],
        pac: Dict[str, int],
        signals: Dict[str, Any]
    ) -> Dict[str, Any]:
        strengths         = []
        failures          = []
        root_cause        = ""
        learning_feedback = []
        next_direction    = ""

        # Strengths
        if pac.get("code") == 1:
            strengths.append("Implementation is present and accessible via repository")
        if pac.get("architecture") == 1:
            strengths.append("Architecture signals detected — layered or modular structure present")
        if pac.get("proof") == 1:
            strengths.append("Proof of work present — README, tests, or documentation found")
        if rubric.get("has_alignment") == 1:
            strengths.append("Requirements alignment is strong — delivery ratio above threshold")
        if rubric.get("has_effort") == 1:
            strengths.append("Effort is evident — structured description and documentation present")
        if not strengths:
            strengths.append("Submission received and processed")

        # Failures and root cause
        if failure_type == "schema_violation":
            failures.append("No accessible GitHub repository provided")
            failures.append("Submission does not meet structural requirements")
            root_cause = "Submission missing required structural elements — repository and description depth required"
            learning_feedback.append("Provide a valid GitHub repository URL with implementation files")
            learning_feedback.append("Ensure description is at least 50 words with technical detail")
            next_direction = "Restart with fundamentals — ensure repository, architecture, and proof are all present"

        elif failure_type == "incomplete":
            if pac.get("proof") == 0:
                failures.append("No proof of working output — missing README, tests, or documentation")
            if pac.get("architecture") == 0:
                failures.append("No architecture signals — flat or unstructured repository")
            if rubric.get("has_code") == 0:
                failures.append("Repository has fewer than 3 files — insufficient implementation scope")
            root_cause = "Submission is structurally incomplete — proof, architecture, or code missing"
            learning_feedback.append("Add a README with setup instructions and sample output")
            learning_feedback.append("Organise code into layers: api/, service/, model/ or equivalent")
            learning_feedback.append("Include at least one test file demonstrating working functionality")
            next_direction = "Restart with fundamentals — ensure repository, architecture, and proof are all present"

        elif failure_type == "incorrect_logic":
            missing = signals.get("missing_features", [])
            evd     = signals.get("expected_vs_delivered_evidence", {})
            ratio   = evd.get("delivery_ratio", 0.0)
            if rubric.get("has_alignment") == 0:
                failures.append(f"Low requirement alignment — delivery ratio {ratio:.0%}, {len(missing)} features missing")
            if rubric.get("has_effort") == 0:
                failures.append("Description too short or lacks structure — effort not demonstrated")
            if missing:
                failures.append(f"Missing features: {', '.join(missing[:5])}")
            root_cause = "Implementation present but does not satisfy stated requirements"
            learning_feedback.append("Re-read the task requirements and map each requirement to a file or function")
            if missing:
                learning_feedback.append(f"Implement missing features: {', '.join(missing[:3])}")
            learning_feedback.append("Expand description to 80+ words with architecture and implementation detail")
            next_direction = "Reinforce current task — address missing features and add proof of correctness"

        elif failure_type == "integration_fail":
            failures.append("Repository could not be accessed or returned an error")
            root_cause = "Integration failure — repository inaccessible, cannot verify implementation"
            learning_feedback.append("Ensure the GitHub repository URL is correct and publicly accessible")
            learning_feedback.append("Verify the repository is not empty and contains implementation files")
            next_direction = "Fix repository access and resubmit"

        else:
            # PASS
            root_cause     = "All core criteria met — submission approved"
            learning_feedback.append("Maintain current quality and expand test coverage for next task")
            next_direction = "Advance to next complexity level — focus on performance, scalability, or new domain"

        return {
            "strengths":         strengths,
            "failures":          failures,
            "root_cause":        root_cause,
            "learning_feedback": learning_feedback,
            "next_direction":    next_direction,
        }


# Global instance
production_decision_engine = ProductionDecisionEngine()
