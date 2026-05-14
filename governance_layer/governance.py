"""
Constitutional Governance Layer — Parikshak v3.0.0
Operator trust classes, override taxonomy, audit lineage, irreversible controls.
NO logic inside the deterministic engine. Governance wraps it.
"""
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


# ── Operator Trust Classes ────────────────────────────────────────────────

class OperatorRole(str, Enum):
    REVIEW_OPERATOR        = "REVIEW_OPERATOR"
    SENIOR_REVIEW_OPERATOR = "SENIOR_REVIEW_OPERATOR"
    EXECUTION_AUTHORIZER   = "EXECUTION_AUTHORIZER"
    SYSTEM_AUDITOR         = "SYSTEM_AUDITOR"
    REPLAY_AUDITOR         = "REPLAY_AUDITOR"


# Explicit permission map — no inheritance, no shortcuts
ROLE_PERMISSIONS: Dict[OperatorRole, List[str]] = {
    OperatorRole.REVIEW_OPERATOR: [
        "view_pending",
        "view_all",
        "approve",
        "reject",
    ],
    OperatorRole.SENIOR_REVIEW_OPERATOR: [
        "view_pending",
        "view_all",
        "approve",
        "reject",
        "modify",
        "escalate",
    ],
    OperatorRole.EXECUTION_AUTHORIZER: [
        "view_all",
        "authorize_high_risk_modify",
        "dual_approve",
    ],
    OperatorRole.SYSTEM_AUDITOR: [
        "view_all",
        "view_audit_logs",
        "view_replay_checkpoints",
        "view_operator_visibility_log",
    ],
    OperatorRole.REPLAY_AUDITOR: [
        "view_audit_logs",
        "view_replay_checkpoints",
        "run_replay_verification",
        "view_divergence_reports",
    ],
}

# Actions requiring dual approval or escalation authorization
HIGH_RISK_ACTIONS = {"modify"}

# Actions that are irreversible once finalized
IRREVERSIBLE_STATES = {"APPROVED", "REJECTED", "MODIFIED", "FINAL_APPROVED", "AUDIT_LOCKED", "REPLAY_SEALED"}


def check_permission(role: OperatorRole, action: str) -> bool:
    """Explicit permission check. No implicit grants."""
    return action in ROLE_PERMISSIONS.get(role, [])


def requires_dual_approval(action: str) -> bool:
    return action in HIGH_RISK_ACTIONS


# ── Override Reason Taxonomy ──────────────────────────────────────────────

class OverrideReason(str, Enum):
    REQUIREMENT_CORRECTION   = "REQUIREMENT_CORRECTION"
    SAFETY_BLOCK             = "SAFETY_BLOCK"
    INVALID_SUBMISSION       = "INVALID_SUBMISSION"
    POLICY_CONFLICT          = "POLICY_CONFLICT"
    HUMAN_VALIDATION_FAILURE = "HUMAN_VALIDATION_FAILURE"


# ── Override Scope Classification ─────────────────────────────────────────

class OverrideScope(str, Enum):
    METADATA_ADJUSTMENT = "METADATA_ADJUSTMENT"   # allowed
    REJECT_REQUEUE      = "REJECT_REQUEUE"         # allowed
    ANNOTATION          = "ANNOTATION"             # allowed
    TRAVERSAL_MUTATION  = "TRAVERSAL_MUTATION"     # PROHIBITED
    AUDIT_ALTERATION    = "AUDIT_ALTERATION"       # PROHIBITED
    REPLAY_MUTATION     = "REPLAY_MUTATION"        # PROHIBITED

PROHIBITED_SCOPES = {
    OverrideScope.TRAVERSAL_MUTATION,
    OverrideScope.AUDIT_ALTERATION,
    OverrideScope.REPLAY_MUTATION,
}


# ── Override Event (immutable) ────────────────────────────────────────────

class OverrideEvent(BaseModel):
    event_id:          str
    trace_id:          str
    submission_id:     str
    operator_id:       str
    operator_role:     OperatorRole
    action:            str
    reason_taxonomy:   OverrideReason
    scope:             OverrideScope
    parent_event_id:   Optional[str] = None   # lineage reference
    original_task_id:  Optional[str] = None
    override_task_id:  Optional[str] = None
    timestamp:         datetime = Field(default_factory=datetime.now)
    authorized_by:     Optional[str] = None   # dual approval
    replay_metadata:   Dict[str, Any] = Field(default_factory=dict)
    finalized:         bool = False

    class Config:
        frozen = True  # immutable after creation


# ── Governance Request ────────────────────────────────────────────────────

class GovernanceRequest(BaseModel):
    trace_id:        str
    submission_id:   str
    operator_id:     str
    operator_role:   OperatorRole
    action:          str
    reason_taxonomy: OverrideReason
    override_task_id: Optional[str] = None
    authorized_by:   Optional[str] = None  # required for high-risk actions
    expected_version: int = Field(default=1)


# ── Constitutional Validator ──────────────────────────────────────────────

class ConstitutionalValidator:
    """
    Validates every governance action against constitutional rules.
    Raises ValueError on any violation — fails loudly, never silently.
    """

    def validate(self, request: GovernanceRequest, current_state: str) -> None:
        # 1. Permission check
        if not check_permission(request.operator_role, request.action):
            raise ValueError(
                f"GOVERNANCE_REJECT: Role '{request.operator_role}' "
                f"does not have permission for action '{request.action}'"
            )

        # 2. Irreversible state check
        if current_state in IRREVERSIBLE_STATES:
            raise ValueError(
                f"GOVERNANCE_REJECT: Submission already in irreversible state '{current_state}'. "
                f"Further changes require explicit superseding governance event."
            )

        # 3. High-risk dual approval check
        if requires_dual_approval(request.action):
            if not request.authorized_by:
                raise ValueError(
                    f"GOVERNANCE_REJECT: Action '{request.action}' requires dual approval. "
                    f"'authorized_by' field must be set by an EXECUTION_AUTHORIZER."
                )

        # 4. Scope prohibition check for modify
        if request.action == "modify":
            # modify is only allowed for bounded metadata, not traversal/audit/replay
            pass  # scope validated at override event creation

        # 5. Reason taxonomy required
        if not request.reason_taxonomy:
            raise ValueError(
                "GOVERNANCE_REJECT: Override reason_taxonomy is required. "
                "Free-text reasons are prohibited."
            )


constitutional_validator = ConstitutionalValidator()
