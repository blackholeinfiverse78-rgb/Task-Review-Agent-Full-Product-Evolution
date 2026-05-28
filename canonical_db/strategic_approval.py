"""
Strategic Approval Engine — Parikshak v6.0.0

Produces evidence-driven StrategicRecommendation from real evaluation signals.
Every recommendation includes:
  - explicit reasoning trace (decision_tree_path)
  - evidence-grounded critique (not score-threshold branching)
  - contextual next-task justification
  - reasoning artifact payload for Gov-OS journal

DOES NOT execute DB write. Recommendation != Execution Authority.
Human operator is sole authority to act on any recommendation.
"""
import hashlib
import uuid
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from canonical_db.contracts import canonical_json


class StrategicRecommendation(BaseModel):
    artifact_id: str
    trace_id: str
    candidate_summary: str
    review_findings: str
    strengths: List[str]
    weaknesses: List[str]
    risk_signals: List[str]
    dependency_awareness: str
    ecosystem_context: str
    suggested_next_task: str
    next_task_justification: str
    suggested_corrections: List[str]
    strategic_notes: str
    human_approval_recommendation: str
    decision_tree_path: List[str]
    evaluation_logic: str
    status: str = "AWAITING_HUMAN_SIGN_OFF"
    execution_blocked: bool = True

    def to_reasoning_artifact_payload(self) -> Dict[str, Any]:
        """Returns a payload conforming to ReasoningArtifacts schema for Gov-OS journal."""
        return {
            "artifact_id": self.artifact_id,
            "trace_id": self.trace_id,
            "evaluation_logic": self.evaluation_logic,
            "decision_tree_path": self.decision_tree_path
        }

    def reasoning_hash(self) -> str:
        """Deterministic hash of the reasoning trace — proves replay identity."""
        payload = {
            "decision_tree_path": self.decision_tree_path,
            "evaluation_logic": self.evaluation_logic,
            "suggested_next_task": self.suggested_next_task,
            "human_approval_recommendation": self.human_approval_recommendation
        }
        return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


class StrategicApprovalEngine:

    @staticmethod
    def prepare_recommendation(
        candidate_name: str,
        trace_id: str,
        evaluation_result: str,
        failure_type: Optional[str],
        pac: Dict[str, Any],
        rubric: Dict[str, Any],
        signals: Dict[str, Any],
        dependency_context: str
    ) -> StrategicRecommendation:
        """
        Produces evidence-driven recommendation from real evaluation signals.
        Every branch is explicitly traced in decision_tree_path.
        No black-box judgment. No score-threshold branching.
        """
        decision_tree_path: List[str] = []
        strengths: List[str] = []
        weaknesses: List[str] = []
        risk_signals: List[str] = []
        suggested_corrections: List[str] = []

        # ── Step 1: Evaluation result branch ─────────────────────────────
        decision_tree_path.append(f"evaluation_result={evaluation_result}")

        if evaluation_result == "PASS":
            decision_tree_path.append("branch=PASS → check PAC completeness")

            if pac.get("code") == 1:
                strengths.append("Code implementation present and accessible.")
                decision_tree_path.append("pac.code=1 → code confirmed")
            if pac.get("architecture") == 1:
                strengths.append("Architectural structure detected (layers/modules/pipeline keywords).")
                decision_tree_path.append("pac.architecture=1 → architecture confirmed")
            if pac.get("proof") == 1:
                strengths.append("Proof artifacts present (README, tests, or docs).")
                decision_tree_path.append("pac.proof=1 → proof confirmed")

            if rubric.get("has_alignment") == 1:
                strengths.append("Delivery ratio meets minimum threshold (≥0.6).")
                decision_tree_path.append("rubric.has_alignment=1 → delivery aligned")
            if rubric.get("has_effort") == 1:
                strengths.append("Description effort meets minimum word count (≥80 words).")
                decision_tree_path.append("rubric.has_effort=1 → effort confirmed")

            suggested_next = "T-GOV-ADVANCED-001"
            next_justification = (
                "All PAC checks passed and rubric alignment confirmed. "
                "Candidate demonstrates architectural awareness and delivery discipline. "
                "Routing to advancement task."
            )
            rec = "APPROVE"
            decision_tree_path.append(f"recommendation=APPROVE → next_task={suggested_next}")

        else:
            # ── Step 2: FAIL — trace failure_type explicitly ──────────────
            decision_tree_path.append(f"branch=FAIL → failure_type={failure_type}")

            if failure_type == "schema_violation":
                weaknesses.append("No repository provided and description below 50 words.")
                risk_signals.append("Submission lacks minimum structural evidence.")
                suggested_corrections.append("Provide a GitHub repository URL or expand description to ≥50 words.")
                decision_tree_path.append("schema_violation: no_repo AND word_count<50")
                suggested_next = "T-GOV-SCHEMA-FIX-001"
                next_justification = "Schema gate failed. Candidate must provide minimum structural evidence before evaluation can proceed."

            elif failure_type == "incomplete":
                if pac.get("code") == 0:
                    weaknesses.append("No code implementation found in repository.")
                    suggested_corrections.append("Ensure repository contains source code files.")
                    decision_tree_path.append("incomplete: pac.code=0")
                if pac.get("proof") == 0:
                    weaknesses.append("No proof artifacts found (README, tests, or docs absent).")
                    suggested_corrections.append("Add README.md with architecture overview and test files.")
                    decision_tree_path.append("incomplete: pac.proof=0")
                if pac.get("architecture") == 0:
                    weaknesses.append("No architectural structure detected.")
                    suggested_corrections.append("Use architecture keywords (layer, service, module, pipeline) in title/description.")
                    decision_tree_path.append("incomplete: pac.architecture=0")
                risk_signals.append("Incomplete submission — missing one or more PAC components.")
                suggested_next = "T-GOV-INCOMPLETE-FIX-001"
                next_justification = "PAC completeness check failed. Candidate must address missing components before logic evaluation."

            elif failure_type == "incorrect_logic":
                evd = signals.get("expected_vs_delivered_evidence", {})
                delivery_ratio = evd.get("delivery_ratio", 0.0)
                missing_count = evd.get("missing_count", 0)
                word_count = signals.get("description_signals", {}).get("word_count", 0)

                if delivery_ratio < 0.6:
                    weaknesses.append(f"Delivery ratio {delivery_ratio:.2f} below minimum threshold of 0.6.")
                    suggested_corrections.append("Implement more of the stated requirements. Delivery ratio must reach ≥0.6.")
                    decision_tree_path.append(f"incorrect_logic: delivery_ratio={delivery_ratio:.2f}<0.6")
                if missing_count > 3:
                    weaknesses.append(f"{missing_count} features missing from implementation.")
                    suggested_corrections.append(f"Address the {missing_count} missing features identified in signal analysis.")
                    decision_tree_path.append(f"incorrect_logic: missing_features={missing_count}>3")
                if word_count < 80:
                    weaknesses.append(f"Description word count {word_count} below minimum effort threshold of 80.")
                    suggested_corrections.append("Expand task description to ≥80 words with technical detail.")
                    decision_tree_path.append(f"incorrect_logic: word_count={word_count}<80")

                risk_signals.append("Logic alignment failure — implementation does not match stated requirements.")
                suggested_next = "T-GOV-LOGIC-FIX-001"
                next_justification = "Logic check failed. Candidate must improve delivery ratio and description effort before passing."

            elif failure_type == "integration_fail":
                weaknesses.append("Repository accessible but metadata missing or error returned.")
                suggested_corrections.append("Verify repository is public and contains valid metadata (name, description).")
                risk_signals.append("Integration failure — repository signal incomplete.")
                decision_tree_path.append("integration_fail: repo_available=True but metadata.name missing")
                suggested_next = "T-GOV-INTEGRATION-FIX-001"
                next_justification = "Integration check failed. Repository must be accessible with complete metadata."

            else:
                weaknesses.append(f"Unknown failure type: {failure_type}")
                risk_signals.append("Unclassified failure — manual review required.")
                decision_tree_path.append(f"unknown_failure_type={failure_type}")
                suggested_next = "T-GOV-REMEDIAL-001"
                next_justification = "Unclassified failure. Routing to remedial task pending manual review."

            rec = "REJECT_AND_REASSIGN"
            decision_tree_path.append(f"recommendation=REJECT_AND_REASSIGN → next_task={suggested_next}")

        # ── Step 3: Build evaluation logic summary ────────────────────────
        evaluation_logic = (
            f"Candidate={candidate_name} | trace_id={trace_id} | "
            f"result={evaluation_result} | failure_type={failure_type} | "
            f"pac={pac} | rubric={rubric} | "
            f"decision_path=[{' → '.join(decision_tree_path)}]"
        )

        artifact_id = f"artifact-{uuid.uuid4().hex[:12]}"

        return StrategicRecommendation(
            artifact_id=artifact_id,
            trace_id=trace_id,
            candidate_summary=f"Candidate {candidate_name} | trace={trace_id} | result={evaluation_result}",
            review_findings=(
                f"Rule engine result: {evaluation_result}. "
                f"Failure type: {failure_type or 'none'}. "
                f"PAC: code={pac.get('code')}, architecture={pac.get('architecture')}, proof={pac.get('proof')}. "
                f"Rubric: alignment={rubric.get('has_alignment')}, effort={rubric.get('has_effort')}."
            ),
            strengths=strengths,
            weaknesses=weaknesses,
            risk_signals=risk_signals,
            dependency_awareness=f"Dependency context: {dependency_context}",
            ecosystem_context="Integrated within the blackholeinfiverse78-rgb / TANTRA ecosystem.",
            suggested_next_task=suggested_next,
            next_task_justification=next_justification,
            suggested_corrections=suggested_corrections,
            strategic_notes=(
                "All recommendations are advisory only. "
                "Human operator must explicitly approve before any assignment is released. "
                "Parikshak has no execution authority."
            ),
            human_approval_recommendation=rec,
            decision_tree_path=decision_tree_path,
            evaluation_logic=evaluation_logic
        )
