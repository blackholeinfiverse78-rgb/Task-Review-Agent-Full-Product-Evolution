import json
from canonical_db.db import CanonicalDB

class SaarthiAdapter:
    def __init__(self, db_path: str = "storage/canonical_db.sqlite"):
        self.db_path = db_path

    def consume_events(self) -> list:
        """Reads immutable events from Canonical DB (No direct DB mutation allowed)."""
        db = CanonicalDB(self.db_path)
        try:
            events = db.get_all_events()
            # Filter review and learning events for Saarthi downstream visibility
            target_types = ["review_history", "learning_signals"]
            return [e for e in events if e["event_type"] in target_types]
        finally:
            db.close()
