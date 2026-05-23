import json
from canonical_db.db import CanonicalDB

class BucketAdapter:
    def __init__(self, db_path: str = "storage/canonical_db.sqlite"):
        self.db_path = db_path

    def consume_events(self) -> list:
        """Reads immutable events from Canonical DB (No direct DB mutation allowed)."""
        db = CanonicalDB(self.db_path)
        try:
            events = db.get_all_events()
            # Filter review_history events for Bucket evaluation logging
            return [e for e in events if e["event_type"] == "review_history"]
        finally:
            db.close()
