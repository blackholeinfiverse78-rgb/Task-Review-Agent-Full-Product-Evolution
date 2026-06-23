import uuid
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from db.db_config import SessionLocal
from db.models import AssignmentModel, Builder, ReviewModel

logger = logging.getLogger("assignment_generator")

CRITICAL_DIMENSIONS = {"Runtime", "Replayability", "Governance", "Security", "Human Approval"}

DIMENSION_TASK_MAPPINGS = {
    "Runtime": {
        "title": "Resolve Runtime Environment Issues and Complete Handover",
        "objective": "Ensure runtime trace matches trace_id and handover status is COMPLETE.",
        "focus_area": "Runtime",
        "category": "Runtime",
        "difficulty": "intermediate",
        "est_ai_effort": "2h",
        "learning_resources": ["TANTRA Lifecycle and Handover Specs", "Ecosystem Integration Guide"],
        "acceptance_criteria": "Handover status is COMPLETE and trace files are verified.",
        "review_checklist": ["Match trace_id across payloads", "Check handover_status in JSON"]
    },
    "Observability": {
        "title": "Initialize OpenTelemetry and Activate Metrics",
        "objective": "Configure OpenTelemetry SDK, initialize tracing span context, and activate performance metrics reporting.",
        "focus_area": "Observability",
        "category": "Observability",
        "difficulty": "intermediate",
        "est_ai_effort": "3h",
        "learning_resources": ["OpenTelemetry Python SDK Guide", "TANTRA Telemetry Standards"],
        "acceptance_criteria": "otel_initialized is true, metrics_active is true, and spans are logged.",
        "review_checklist": ["Check otel_initialized status", "Verify telemetry collection endpoint integration"]
    },
    "Replayability": {
        "title": "Fix Replay Discrepancies and Ensure Determinism",
        "objective": "Identify and resolve sources of non-determinism (e.g. random variables, time dependencies) during execution replay.",
        "focus_area": "Replayability",
        "category": "Replayability",
        "difficulty": "advanced",
        "est_ai_effort": "6h",
        "learning_resources": ["Deterministic Execution Principles", "Replay Integrity Specs (docs/REPLAY_INTEGRITY.md)"],
        "acceptance_criteria": "Replay verification status is VERIFIED, replay_status is SUCCESS.",
        "review_checklist": ["Run replay comparison check", "Fix timestamp drift or random seeds"]
    },
    "Governance": {
        "title": "Establish Valid Authority Signatures in Governance Records",
        "objective": "Verify authority signatures in governance_record.json and resolve any constitutional blockages.",
        "focus_area": "Governance",
        "category": "Governance",
        "difficulty": "advanced",
        "est_ai_effort": "4h",
        "learning_resources": ["BHIV Governance Doctrine", "Constitutional Compliance Guide"],
        "acceptance_criteria": "valid_authority is true, decision is APPROVED, and violations_count is 0.",
        "review_checklist": ["Verify governance keys in json", "Inspect constitutional_history.json for violations"]
    },
    "Provenance": {
        "title": "Verify Code Provenance and Lineage Chain integrity",
        "objective": "Resolve drift or gaps in the lineage registration and lineage chain trace.",
        "focus_area": "Provenance",
        "category": "Provenance",
        "difficulty": "intermediate",
        "est_ai_effort": "3h",
        "learning_resources": ["Lineage Verification Protocol", "Provenance Registration Docs"],
        "acceptance_criteria": "valid_chain is true and registered is true in lineage_registration.",
        "review_checklist": ["Validate parent/current hashes chain", "Verify registry registration status"]
    },
    "Security": {
        "title": "Resolve Security Vulnerabilities and Verify Signatures",
        "objective": "Identify and patch critical/high vulnerabilities in the repository, and ensure all releases are cryptographically signed.",
        "focus_area": "Security",
        "category": "Security",
        "difficulty": "advanced",
        "est_ai_effort": "4h",
        "learning_resources": ["TANTRA Security Doctrine (docs/SECURITY_AUDIT.md)", "Cryptographic Signing Best Practices"],
        "acceptance_criteria": "All critical/high vulnerabilities are resolved, signature validation is active.",
        "review_checklist": ["Verify signature_verified is true", "Ensure critical_vulnerabilities count is 0"]
    },
    "Versioning": {
        "title": "Resolve Schema Drift and Version Mismatch",
        "objective": "Verify blueprint schema registration and resolve differences between current schema and reference schemas.",
        "focus_area": "Versioning",
        "category": "Versioning",
        "difficulty": "beginner",
        "est_ai_effort": "2h",
        "learning_resources": ["Schema Versioning Policy", "Blueprint Drift Management"],
        "acceptance_criteria": "schema_drift is false and schema_version matches registration.",
        "review_checklist": ["Check schema_drift boolean", "Match schema_version to registration_reference"]
    },
    "Recovery": {
        "title": "Implement Rollover Recovery Anchors and Test Rollback",
        "objective": "Test recovery pipeline execution and register valid rollback anchors for transaction safety.",
        "focus_area": "Recovery",
        "category": "Recovery",
        "difficulty": "intermediate",
        "est_ai_effort": "4h",
        "learning_resources": ["Transaction Recovery Guide", "Rollback Anchor Configuration"],
        "acceptance_criteria": "recovery_status is SUCCESS and recovery_tested is true.",
        "review_checklist": ["Check rollback_anchors_count > 0", "Verify recovery execution status"]
    },
    "Human Approval": {
        "title": "Obtain Authorized Governor Approvals",
        "objective": "Get manual human review signature from authorized governor (Akash, Ansh, Saarthi_Governor).",
        "focus_area": "Governance",
        "category": "Human Approval",
        "difficulty": "beginner",
        "est_ai_effort": "1h",
        "learning_resources": ["Human-In-The-Loop Procedure (docs/DEMO_LOCK_PROCEDURE.md)"],
        "acceptance_criteria": "signed_by matches authorized governor list and decision is APPROVED.",
        "review_checklist": ["Verify governor signature", "Approve validation decision"]
    },
    "Layer Placement": {
        "title": "Resolve Ecosystem Layer Placement Compliance",
        "objective": "Validate system's boundary and layer placement against ecosystem definitions.",
        "focus_area": "Ecosystem Placement",
        "category": "Layer Placement",
        "difficulty": "beginner",
        "est_ai_effort": "2h",
        "learning_resources": ["Ecosystem Boundary Mapping Guide"],
        "acceptance_criteria": "Ecosystem placement status is PASS.",
        "review_checklist": ["Verify layer assignment validation report"]
    },
    "Dependency Integrity": {
        "title": "Verify External Dependency Compatibility",
        "objective": "Analyze external imports and packages for ecosystem compliance and licensing conflicts.",
        "focus_area": "Dependency Integrity",
        "category": "Dependency Integrity",
        "difficulty": "intermediate",
        "est_ai_effort": "3h",
        "learning_resources": ["Dependency Policy Docs"],
        "acceptance_criteria": "Ecosystem dependency status is PASS.",
        "review_checklist": ["Verify import validator report"]
    },
    "Ecosystem Participation": {
        "title": "Resolve Integration Role Registry Issues",
        "objective": "Align product participation role and scope with ecosystem requirements.",
        "focus_area": "Ecosystem Participation",
        "category": "Ecosystem Participation",
        "difficulty": "intermediate",
        "est_ai_effort": "3h",
        "learning_resources": ["Participation Agreement Protocol"],
        "acceptance_criteria": "Ecosystem participation status is PASS.",
        "review_checklist": ["Confirm participation registry registration"]
    }
}

class AutomaticAssignmentEngine:
    """
    Parses failed/warning dimensions from a certification report and generates prioritized,
    actionable assignments for builders dynamically.
    """
    def __init__(self):
        pass

    def generate_assignments(self, cert_report: Dict[str, Any], review_id: Optional[str] = None) -> List[Dict[str, Any]]:
        trace_id = cert_report.get("system_information", {}).get("trace_id", "unknown")
        dimensions = cert_report.get("dimensions", {})
        
        # Determine candidate owner
        db = SessionLocal()
        builder_id = "Default_Builder"
        if review_id:
            review_rec = db.query(ReviewModel).filter(ReviewModel.review_id == review_id).first()
            if review_rec and review_rec.candidate_name:
                builder_id = review_rec.candidate_name
        
        # Verify builder exists
        builder_obj = db.query(Builder).filter(Builder.id == builder_id).first()
        if not builder_obj:
            builder_obj = Builder(id=builder_id, name=builder_id)
            db.add(builder_obj)
            db.commit()

        assignments_created = []

        for dim, status in dimensions.items():
            if status in ("FAIL", "WARNING"):
                mapping = DIMENSION_TASK_MAPPINGS.get(dim)
                if not mapping:
                    continue

                # Determine Priority
                if dim in CRITICAL_DIMENSIONS and status == "FAIL":
                    priority = "Critical"
                elif status == "FAIL":
                    priority = "High"
                else:
                    priority = "Medium"

                assignment_id = f"assign-auto-{uuid.uuid4().hex[:12]}"
                
                db_assignment = AssignmentModel(
                    id=assignment_id,
                    builder_id=builder_id,
                    review_id=review_id,
                    next_task_id=f"NT-{dim.upper()[:3]}-{uuid.uuid4().hex[:6]}",
                    task_type="correction" if status == "FAIL" else "reinforcement",
                    title=mapping["title"],
                    objective=mapping["objective"],
                    focus_area=mapping["focus_area"],
                    difficulty=mapping["difficulty"],
                    reason=f"Auto-generated due to failed dimension: {dim} ({status})",
                    priority=priority,
                    category=mapping["category"],
                    est_ai_effort=mapping["est_ai_effort"],
                    learning_resources=json.dumps(mapping["learning_resources"]),
                    review_checklist=json.dumps(mapping["review_checklist"]),
                    status="assigned",
                    assigned_at=datetime.utcnow()
                )

                db.add(db_assignment)
                
                assignments_created.append({
                    "assignment_id": assignment_id,
                    "dimension": dim,
                    "status": status,
                    "title": mapping["title"],
                    "priority": priority,
                    "difficulty": mapping["difficulty"]
                })

        db.commit()
        db.close()
        
        logger.info(f"Auto-generated {len(assignments_created)} assignments for trace_id={trace_id}")
        return assignments_created

# Global Instance
automatic_assignment_engine = AutomaticAssignmentEngine()
