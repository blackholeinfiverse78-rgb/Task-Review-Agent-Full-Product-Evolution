"""
Human-in-Loop Service - Confidence-based Escalation
Implements confidence calculation and triggers escalation if < 0.98
Provides override capability for human reviewers
Escalation cases are persisted to disk — survives restarts
"""
from typing import Dict, Any, Optional, List
import logging
import json
import os
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger("human_in_loop")


class EscalationReason(str, Enum):
    LOW_CONFIDENCE = "low_confidence"
    CONFLICTING_SIGNALS = "conflicting_signals"
    EDGE_CASE = "edge_case"
    MANUAL_REVIEW_REQUESTED = "manual_review_requested"
    QUALITY_CONCERN = "quality_concern"


class EscalationStatus(str, Enum):
    PENDING = "pending"
    IN_REVIEW = "in_review"
    RESOLVED = "resolved"
    OVERRIDDEN = "overridden"


@dataclass
class ConfidenceMetrics:
    base_confidence: float
    quality_adjustment: float
    pac_adjustment: float
    evidence_adjustment: float
    consistency_adjustment: float
    final_confidence: float
    proof_consistency: float
    signal_alignment: float
    decision_clarity: float
    evidence_strength: float
    requires_escalation: bool
    escalation_reasons: List[str]


@dataclass
class EscalationCase:
    case_id: str
    trace_id: str
    timestamp: str
    reason: str           # plain string — JSON-serialisable
    confidence: float
    original_evaluation: Dict[str, Any]
    original_decision: Dict[str, Any]
    escalation_context: Dict[str, Any]
    status: str           # plain string — JSON-serialisable
    assigned_reviewer: Optional[str] = None
    review_notes: Optional[str] = None
    human_override: Optional[Dict[str, Any]] = None
    resolved_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class HumanInLoopService:
    """
    Human-in-loop service for confidence-based escalation.
    Escalation cases are persisted to disk so restarts do not lose pending reviews.
    """

    def __init__(self, confidence_threshold: float = 0.98,
                 storage_path: str = "storage/escalations"):
        self.confidence_threshold = confidence_threshold
        self.storage_path = storage_path
        os.makedirs(self.storage_path, exist_ok=True)
        self.escalation_cases: Dict[str, EscalationCase] = self._load_all_cases()

    # ── Persistence ──────────────────────────────────────────────────────

    def _case_path(self, case_id: str) -> str:
        return os.path.join(self.storage_path, f"{case_id}.json")

    def _save_case(self, case: EscalationCase) -> None:
        try:
            with open(self._case_path(case.case_id), "w", encoding="utf-8") as f:
                json.dump(case.to_dict(), f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"[HUMAN-IN-LOOP] Failed to persist case {case.case_id}: {e}")

    def _load_all_cases(self) -> Dict[str, EscalationCase]:
        cases: Dict[str, EscalationCase] = {}
        if not os.path.isdir(self.storage_path):
            return cases
        for fname in os.listdir(self.storage_path):
            if not fname.endswith(".json"):
                continue
            try:
                with open(os.path.join(self.storage_path, fname), "r", encoding="utf-8") as f:
                    data = json.load(f)
                cases[data["case_id"]] = EscalationCase(**data)
            except Exception as e:
                logger.warning(f"[HUMAN-IN-LOOP] Could not load {fname}: {e}")
        logger.info(f"[HUMAN-IN-LOOP] Loaded {len(cases)} persisted escalation cases")
        return cases

    # ── Confidence calculation ────────────────────────────────────────────

    def calculate_confidence(
        self,
        evaluation_result: Dict[str, Any],
        decision_result: Dict[str, Any],
        supporting_signals: Dict[str, Any]
    ) -> ConfidenceMetrics:
        """
        Phase 3 — Hardened confidence formula (deterministic, no heuristics):

          confidence = (proof + architecture + code + rubric_completeness) / total

          Where:
            proof               = pac.proof          (0 or 1)
            architecture        = pac.architecture   (0 or 1)
            code                = pac.code           (0 or 1)
            rubric_completeness = rubric_sum / 6     (0.0–1.0, 6 binary criteria)
            total               = 4  (three binary + one normalised)

          Result is in [0.0, 1.0]. Threshold = 0.98.
          Requires_escalation = confidence < 0.98
        """
        logger.info("[HUMAN-IN-LOOP] Calculating Phase 3 hardened confidence")

        # Extract PAC from evaluation result (set by assignment engine)
        pac = evaluation_result.get("pac", {})
        proof        = float(pac.get("proof",        0))
        architecture = float(pac.get("architecture", 0))
        code         = float(pac.get("code",         0))

        # rubric_completeness: fraction of 6 binary rubric criteria that are 1
        rubric = evaluation_result.get("rubric", {})
        rubric_sum = (
            rubric.get("has_proof",        0) +
            rubric.get("has_architecture", 0) +
            rubric.get("has_code",         0) +
            rubric.get("has_alignment",    0) +
            rubric.get("has_authenticity", 0) +
            rubric.get("has_effort",       0)
        )
        rubric_completeness = rubric_sum / 6.0  # normalised 0–1

        # Exact formula — total = 4 components
        total = 4.0
        raw_confidence = (proof + architecture + code + rubric_completeness) / total
        final_confidence = round(min(1.0, max(0.0, raw_confidence)), 4)

        requires_escalation = final_confidence < self.confidence_threshold
        escalation_reasons  = []
        if requires_escalation:
            escalation_reasons.append("low_confidence")
        if proof == 0:
            escalation_reasons.append("no_proof")
        if architecture == 0:
            escalation_reasons.append("no_architecture")
        if code == 0:
            escalation_reasons.append("no_code")
        if rubric_completeness < 0.5:
            escalation_reasons.append("low_rubric_completeness")

        # ConfidenceMetrics fields — fill legacy fields with formula components
        metrics = ConfidenceMetrics(
            base_confidence=raw_confidence,
            quality_adjustment=0.0,          # not used in hardened formula
            pac_adjustment=0.0,              # not used in hardened formula
            evidence_adjustment=0.0,         # not used in hardened formula
            consistency_adjustment=0.0,      # not used in hardened formula
            final_confidence=final_confidence,
            proof_consistency=proof,
            signal_alignment=architecture,
            decision_clarity=code,
            evidence_strength=rubric_completeness,
            requires_escalation=requires_escalation,
            escalation_reasons=escalation_reasons
        )

        logger.info(
            f"[HUMAN-IN-LOOP] Confidence: proof={proof} arch={architecture} "
            f"code={code} rubric={rubric_completeness:.3f} "
            f"→ ({proof}+{architecture}+{code}+{rubric_completeness:.3f})/4 "
            f"= {final_confidence:.4f} (threshold={self.confidence_threshold})"
        )
        if requires_escalation:
            logger.warning(f"[HUMAN-IN-LOOP] Escalation: {', '.join(escalation_reasons)}")

        return metrics

    def process_with_human_loop(
        self,
        evaluation_result: Dict[str, Any],
        decision_result: Dict[str, Any],
        supporting_signals: Dict[str, Any],
        trace_id: str
    ) -> Dict[str, Any]:
        confidence_metrics = self.calculate_confidence(
            evaluation_result, decision_result, supporting_signals
        )

        if confidence_metrics.requires_escalation:
            escalation_case = self._create_escalation_case(
                evaluation_result, decision_result, supporting_signals,
                confidence_metrics, trace_id
            )
            logger.info(f"[HUMAN-IN-LOOP] Escalation case created: {escalation_case.case_id}")
            return {
                **evaluation_result,
                "confidence_metrics": confidence_metrics.__dict__,
                "escalation_required": True,
                "escalation_case_id": escalation_case.case_id,
                "human_review_pending": True
            }

        return {
            **evaluation_result,
            "confidence_metrics": confidence_metrics.__dict__,
            "escalation_required": False,
            "human_review_pending": False
        }

    def apply_human_override(
        self,
        case_id: str,
        reviewer: str,
        override_decision: Dict[str, Any],
        review_notes: str
    ) -> Dict[str, Any]:
        if case_id not in self.escalation_cases:
            raise ValueError(f"Escalation case {case_id} not found")

        case = self.escalation_cases[case_id]
        case.status = EscalationStatus.OVERRIDDEN.value
        case.assigned_reviewer = reviewer
        case.review_notes = review_notes
        case.human_override = override_decision
        case.resolved_at = datetime.now().isoformat()
        self._save_case(case)

        logger.info(f"[HUMAN-IN-LOOP] Override applied by {reviewer} for case {case_id}")
        return {
            **case.original_evaluation,
            **override_decision,
            "human_override_applied": True,
            "human_reviewer": reviewer,
            "human_review_notes": review_notes,
            "original_confidence": case.confidence,
            "override_confidence": 1.0,
            "escalation_resolved": True
        }

    def get_pending_escalations(self) -> List[Dict[str, Any]]:
        return [
            {
                "case_id":   c.case_id,
                "trace_id":  c.trace_id,
                "timestamp": c.timestamp,
                "confidence": c.confidence,
                "reasons":   c.escalation_context.get("escalation_reasons", []),
                "evaluation_result": c.original_evaluation.get("evaluation_result", "FAIL"),
                "failure_type":      c.original_evaluation.get("failure_type"),
                "decision":          c.original_decision.get("decision", "REJECTED")
            }
            for c in self.escalation_cases.values()
            if c.status == EscalationStatus.PENDING.value
        ]

    def resolve_escalation_by_trace(self, trace_id: str, reviewer: str, decision: str, notes: str = "") -> None:
        for case in self.escalation_cases.values():
            if case.trace_id == trace_id and case.status == EscalationStatus.PENDING.value:
                case.status = EscalationStatus.RESOLVED.value
                case.assigned_reviewer = reviewer
                case.review_notes = notes
                case.human_override = {"decision": decision}
                case.resolved_at = datetime.now().isoformat()
                self._save_case(case)
                logger.info(f"[HUMAN-IN-LOOP] Auto-resolved escalation case {case.case_id} via governance action {decision}")

    # ── Private helpers ───────────────────────────────────────────────────

    def _create_escalation_case(
        self,
        evaluation_result: Dict[str, Any],
        decision_result: Dict[str, Any],
        supporting_signals: Dict[str, Any],
        confidence_metrics: ConfidenceMetrics,
        trace_id: str
    ) -> EscalationCase:
        case_id = f"esc-{datetime.now().strftime('%Y%m%d%H%M%S')}-{trace_id[:8]}"
        case = EscalationCase(
            case_id=case_id,
            trace_id=trace_id,
            timestamp=datetime.now().isoformat(),
            reason=EscalationReason.LOW_CONFIDENCE.value,
            confidence=confidence_metrics.final_confidence,
            original_evaluation=evaluation_result,
            original_decision=decision_result,
            escalation_context={
                "confidence_metrics": confidence_metrics.__dict__,
                "supporting_signals_summary": {
                    "repository_available": supporting_signals.get("repository_available", False),
                    "feature_match_ratio": supporting_signals.get("feature_match_ratio", 0),
                    "delivery_ratio": supporting_signals.get("expected_vs_delivered_evidence", {}).get("delivery_ratio", 0),
                    "quality_grade": decision_result.get("quality_rubric", {}).get("quality_grade", "D")
                },
                "escalation_reasons": confidence_metrics.escalation_reasons
            },
            status=EscalationStatus.PENDING.value
        )
        self.escalation_cases[case_id] = case
        self._save_case(case)
        return case

# Global instance
human_in_loop = HumanInLoopService()
