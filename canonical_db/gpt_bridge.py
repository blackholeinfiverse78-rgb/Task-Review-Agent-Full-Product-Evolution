import json
import hashlib
from typing import Dict, Any
from canonical_db.db import CanonicalDB
from canonical_db.contracts import GovernanceEnvelope, ENTITY_SCHEMAS

SYSTEM_SECRET_KEY = "PARIKSHAK_OS_SECURE_BRIDGE_KEY"

# ── GPT Bridge Boundary Contract ─────────────────────────────────────────────
# ALLOWED:
#   - export_state_for_gpt()       : read-only signed state export
#   - prepare_import_envelope()    : schema-validate + wrap in envelope, NO DB write
#
# BLOCKED (raises immediately):
#   - Any direct DB write
#   - Any approval or assignment authority
#   - Any mutation of AUTHORIZED_GOVERNORS
#   - Any replay or rollback execution
#   - Any snapshot creation or restore
#
# SYNCHRONIZATION OWNERSHIP:
#   - GPT receives a signed read-only snapshot of current state
#   - GPT may propose scaffolds via prepare_import_envelope()
#   - All proposed scaffolds return status=AWAITING_HUMAN_APPROVAL
#   - Human operator is the sole authority to submit the envelope to GovernedPipeline
#
# REPLAY IMPLICATIONS:
#   - GPT exports do NOT create journal events
#   - GPT scaffolds do NOT create journal events
#   - Only human-approved GovernedPipeline.submit_mutation() creates journal events
#
# BACKUP INTERACTION:
#   - GPT bridge has no access to BackupManager
#   - GPT bridge cannot trigger snapshots or restores
# ─────────────────────────────────────────────────────────────────────────────

class GPTBridge:
    def __init__(self, db_path: str = "storage/canonical_db.sqlite"):
        self.db_path = db_path

    def export_state_for_gpt(self) -> Dict[str, Any]:
        """
        Read-only signed state export.
        Opens DB, reconstructs state, closes DB, returns signed payload.
        NO write path exists in this method.
        """
        db = CanonicalDB(self.db_path)
        try:
            state = db.reconstruct_state()
            last_event = db.get_last_event()
        finally:
            db.close()

        state_str = json.dumps(state, sort_keys=True)
        head_hash = last_event["event_hash"] if last_event else "0" * 64

        sig_input = f"{state_str}|{head_hash}|{SYSTEM_SECRET_KEY}"
        signature = hashlib.sha256(sig_input.encode("utf-8")).hexdigest()

        return {
            "version": "v1.0",
            "exported_at": last_event["timestamp"] if last_event else "0",
            "head_hash": head_hash,
            "state": state,
            "system_signature": signature,
            "bridge_mode": "READ_ONLY",
            "write_authority": "NONE",
            "approval_authority": "NONE"
        }

    def prepare_import_envelope(
        self, gpt_scaffold: Dict[str, Any], event_type: str, trace_id: str, actor: str
    ) -> Dict[str, Any]:
        """
        Validates GPT scaffold against canonical schema and wraps in GovernanceEnvelope.
        DOES NOT write to DB. Returns AWAITING_HUMAN_APPROVAL status only.
        Human operator must explicitly call GovernedPipeline.submit_mutation() to commit.
        """
        if event_type not in ENTITY_SCHEMAS:
            raise ValueError(f"GOVERNANCE_REJECT: Unknown event type '{event_type}'")

        schema_cls = ENTITY_SCHEMAS[event_type]
        schema_cls(**gpt_scaffold)

        envelope = GovernanceEnvelope(
            trace_id=trace_id,
            schema_version="v1.0",
            actor=actor,
            actor_role="gpt_agent",
            event_type=event_type,
            payload=gpt_scaffold,
            lineage_reference="gpt-scaffold-reference",
            approval_token="pending-human-verification",
            parent_event_hash="0" * 64
        )
        envelope.payload_checksum = envelope.compute_checksum()

        envelope_data = envelope.model_dump()
        from canonical_db.contracts import canonical_json
        env_str = canonical_json(envelope_data)
        import_sig = hashlib.sha256(f"{env_str}|{SYSTEM_SECRET_KEY}".encode("utf-8")).hexdigest()

        return {
            "envelope": envelope_data,
            "bridge_validation": "PASSED",
            "import_signature": import_sig,
            "status": "AWAITING_HUMAN_APPROVAL",
            "write_authority": "NONE — human operator must call GovernedPipeline.submit_mutation()"
        }
