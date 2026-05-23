import os
from typing import Dict, Any, Optional
from canonical_db.contracts import GovernanceEnvelope
from canonical_db.db import CanonicalDB
from canonical_db.backup import BackupManager
from canonical_db.integrity import IntegrityValidator
from observability.observability import observability

# List of authorized human actors who can sign/approve governance actions
AUTHORIZED_GOVERNORS = {
    "Akash",
    "Sri Satya",
    "Nupur",
    "Senior Operator",
    "Reviewer-1",
    "Reviewer-2",
    "operator-1"
}

class GovernedPipeline:
    def __init__(self, db_path: str = "storage/canonical_db.sqlite"):
        self.db_path = db_path
        self.backup_mgr = BackupManager(self.db_path)

    def submit_mutation(self, envelope: GovernanceEnvelope, executor_actor: str) -> Dict[str, Any]:
        """
        Executes the Governed Data Entry Pipeline:
        Structured Entry -> Schema Validation -> Integrity Validation -> Human Approval -> DB Commit -> Snapshot -> Observability
        """
        # 1. Structured Entry & Schema Validation
        # (Inside validate_payload, it performs schema validation & payload checksum checks)
        envelope.validate_payload()

        # 2. Human Approval Check
        from canonical_db.contracts import AutonomousReleaseBlocked
        if not envelope.authorized_by:
            raise PermissionError("GOVERNANCE_REJECT: Mutation requires explicit human approval sign-off.")
        
        if envelope.authorized_by not in AUTHORIZED_GOVERNORS:
            if envelope.authorized_by == "AI_Orchestrator_Agent" or envelope.event_type == "assignment_history":
                raise AutonomousReleaseBlocked(f"AutonomousReleaseBlocked: Actor '{envelope.authorized_by}' is not authorized to sign-off on governance events.")
            raise PermissionError(
                f"GOVERNANCE_REJECT: Actor '{envelope.authorized_by}' is not authorized to sign-off on governance events."
            )

        if envelope.event_type == "assignment_history":
            approval_state = "HUMAN_APPROVED" if envelope.authorized_by in AUTHORIZED_GOVERNORS else "PENDING"
            if approval_state != "HUMAN_APPROVED":
                raise AutonomousReleaseBlocked("AutonomousReleaseBlocked: Autonomous release is blocked.")

        # 3. Integrity Validation (on existing database before writing new event)
        validator = IntegrityValidator(self.db_path)
        scan = validator.run_full_scan()
        if not scan["valid"]:
            raise ValueError(f"DATABASE_CORRUPT: Cannot write to database with failed integrity: {scan['reason']}")

        # 4. DB Commit (Append to transaction log)
        db = CanonicalDB(self.db_path)
        try:
            event_row = db.append_event(envelope, executor_actor)
            seq = event_row["sequence"]
            head_hash = event_row["event_hash"]
        finally:
            db.close()

        # 5. Snapshot (Create snapshot backups automatically)
        snapshot_manifest = self.backup_mgr.create_snapshot(seq, head_hash)

        # 6. Emit Observability Event
        obs_payload = {
            "event": "governed_mutation_committed",
            "sequence": seq,
            "event_id": event_row["event_id"],
            "trace_id": envelope.trace_id,
            "event_type": envelope.event_type,
            "actor": executor_actor,
            "authorized_by": envelope.authorized_by,
            "snapshot_manifest": snapshot_manifest,
            "event_hash": head_hash
        }
        
        # Log to system observability
        observability.log_observability_event("info", f"Governed DB Mutation: {envelope.event_type} sequence {seq} committed.", obs_payload)

        return {
            "status": "SUCCESS",
            "sequence": seq,
            "event_id": event_row["event_id"],
            "event_hash": head_hash,
            "snapshot": snapshot_manifest
        }
