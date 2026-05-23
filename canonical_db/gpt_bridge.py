import json
import hashlib
from typing import Dict, Any, Optional
from canonical_db.db import CanonicalDB
from canonical_db.contracts import GovernanceEnvelope, ENTITY_SCHEMAS

# Secret seed to simulate signing for export/import authenticity validation
SYSTEM_SECRET_KEY = "PARIKSHAK_OS_SECURE_BRIDGE_KEY"

class GPTBridge:
    def __init__(self, db_path: str = "storage/canonical_db.sqlite"):
        self.db_path = db_path

    def export_state_for_gpt(self) -> Dict[str, Any]:
        """
        Export-only bridge tool: dumps the current state of read models
        along with a system signature for security.
        """
        db = CanonicalDB(self.db_path)
        try:
            state = db.reconstruct_state()
            last_event = db.get_last_event()
        finally:
            db.close()

        state_str = json.dumps(state, sort_keys=True)
        head_hash = last_event["event_hash"] if last_event else "0"*64
        
        # Calculate signature
        sig_input = f"{state_str}|{head_hash}|{SYSTEM_SECRET_KEY}"
        signature = hashlib.sha256(sig_input.encode('utf-8')).hexdigest()

        return {
            "version": "v1.0",
            "exported_at": last_event["timestamp"] if last_event else "0",
            "head_hash": head_hash,
            "state": state,
            "system_signature": signature
        }

    def prepare_import_envelope(self, gpt_scaffold: Dict[str, Any], event_type: str, trace_id: str, actor: str) -> Dict[str, Any]:
        """
        Imports validation tool: parses GPT strategic scaffolding, validates schemas,
        and wraps it in a signed Governance Envelope.
        DOES NOT execute DB write. Human review and explicit approval are required.
        """
        if event_type not in ENTITY_SCHEMAS:
            raise ValueError(f"GOVERNANCE_REJECT: Unknown event type '{event_type}'")

        # Validate GPT raw scaffold against entity Pydantic schema
        schema_cls = ENTITY_SCHEMAS[event_type]
        # This will raise ValueError if invalid
        schema_cls(**gpt_scaffold)

        # Build Governance Envelope
        envelope = GovernanceEnvelope(
            trace_id=trace_id,
            schema_version="v1.0",
            actor=actor,
            actor_role="gpt_agent",
            event_type=event_type,
            payload=gpt_scaffold,
            lineage_reference="gpt-scaffold-reference",
            approval_token="pending-human-verification",
            parent_event_hash="0"*64
        )
        # Compute checksum of payload
        envelope.payload_checksum = envelope.compute_checksum()

        # Mark authenticity of import preparation
        envelope_data = envelope.dict()
        from canonical_db.contracts import canonical_json
        env_str = canonical_json(envelope_data)
        import_sig = hashlib.sha256(f"{env_str}|{SYSTEM_SECRET_KEY}".encode('utf-8')).hexdigest()

        return {
            "envelope": envelope_data,
            "bridge_validation": "PASSED",
            "import_signature": import_sig,
            "status": "AWAITING_HUMAN_APPROVAL"
        }
