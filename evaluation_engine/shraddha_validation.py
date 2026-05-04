"""
Shraddha Validation Layer — FINAL CONTRACT GATE
Enforces PASS/FAIL output contract. No numeric scoring.
"""
from typing import Dict, Any, List
import logging
from datetime import datetime

logger = logging.getLogger("shraddha_validation")

VALID_RESULTS      = {"PASS", "FAIL"}
VALID_FAILURE_TYPES = {"schema_violation", "incomplete", "incorrect_logic", "integration_fail"}
REQUIRED_FIELDS    = ["submission_id", "evaluation_result", "failure_type"]


class ValidationGate:

    def validate_final_output(
        self,
        result: Dict[str, Any],
        source: str = "unknown"
    ) -> Dict[str, Any]:
        logger.info(f"[SHRADDHA] Validating output from: {source}")

        result = self._enforce_required_fields(result)
        result = self._enforce_result_enum(result)
        result = self._enforce_failure_type(result)
        result = self._strip_numeric_scores(result)
        result["validation_metadata"] = {
            "validated_by": "shraddha_validation_layer",
            "validated_at": datetime.now().isoformat(),
            "source": source
        }

        logger.info(f"[SHRADDHA] Validated — result={result.get('evaluation_result')} failure_type={result.get('failure_type')}")
        return result

    def _enforce_required_fields(self, result: Dict[str, Any]) -> Dict[str, Any]:
        if "submission_id" not in result:
            result["submission_id"] = "unknown"
        if "evaluation_result" not in result:
            result["evaluation_result"] = "FAIL"
        if "failure_type" not in result:
            result["failure_type"] = "schema_violation"
        return result

    def _enforce_result_enum(self, result: Dict[str, Any]) -> Dict[str, Any]:
        if result.get("evaluation_result") not in VALID_RESULTS:
            logger.warning(f"[SHRADDHA] Invalid evaluation_result: {result.get('evaluation_result')} → FAIL")
            result["evaluation_result"] = "FAIL"
            result["failure_type"] = "schema_violation"
        return result

    def _enforce_failure_type(self, result: Dict[str, Any]) -> Dict[str, Any]:
        if result["evaluation_result"] == "PASS":
            result["failure_type"] = None
        elif result.get("failure_type") not in VALID_FAILURE_TYPES:
            logger.warning(f"[SHRADDHA] Invalid failure_type: {result.get('failure_type')} → schema_violation")
            result["failure_type"] = "schema_violation"
        return result

    def _strip_numeric_scores(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Remove any residual numeric score fields."""
        for key in ["score", "score_10", "readiness_percent", "title_score",
                    "description_score", "repository_score", "raw_score"]:
            result.pop(key, None)
        return result


# Global instance
validation_gate = ValidationGate()
