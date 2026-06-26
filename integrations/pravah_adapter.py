"""
Pravah Adapter — Parikshak v6.0.0
Records immutable trace and evaluation replay evidence to a dedicated ledger.
Ledger target: storage/pravah_replay.jsonl
"""
import os
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional

logger = logging.getLogger("pravah_adapter")

PRAVAH_REPLAY_LEDGER = "storage/pravah_replay.jsonl"

class PravahAdapter:
    def __init__(self, ledger_path: str = PRAVAH_REPLAY_LEDGER):
        self.ledger_path = ledger_path
        os.makedirs(os.path.dirname(os.path.abspath(self.ledger_path)), exist_ok=True)

    def record_replay(
        self,
        trace_id: str,
        event_id: str,
        sequence: int,
        parent_hash: str,
        event_hash: str,
        intake_payload: Optional[Dict[str, Any]],
        review_payload: Dict[str, Any]
    ) -> None:
        """
        Record replay evidence atomically.
        """
        entry = {
            "trace_id": trace_id,
            "event_id": event_id,
            "sequence": sequence,
            "parent_hash": parent_hash,
            "event_hash": event_hash,
            "intake_payload": intake_payload,
            "review_payload": review_payload,
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "system": "Parikshak",
            "destination": "Pravah"
        }
        
        try:
            # Atomic append: open, write and flush
            with open(self.ledger_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
            logger.info(f"[PRAVAH] Replay evidence recorded for trace {trace_id} at sequence {sequence}")
        except Exception as e:
            logger.error(f"[PRAVAH] Failed to record replay evidence: {e}")
            # Do not crash the caller on non-fatal ledger append error, but log warning
            raise RuntimeError(f"PRAVAH_WRITE_FAILURE: {e}")

# Global instance
pravah_adapter = PravahAdapter()
