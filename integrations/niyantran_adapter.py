import json
from canonical_db.db import CanonicalDB

class NiyantranAdapter:
    def __init__(self, db_path: str = "storage/canonical_db.sqlite"):
        self.db_path = db_path

    def consume_events(self) -> list:
        """Reads immutable events from Canonical DB (No direct DB mutation allowed)."""
        db = CanonicalDB(self.db_path)
        try:
            events = db.get_all_events()
            # Filter assignment_history events for Niyantran
            return [e for e in events if e["event_type"] == "assignment_history"]
        finally:
            db.close()
