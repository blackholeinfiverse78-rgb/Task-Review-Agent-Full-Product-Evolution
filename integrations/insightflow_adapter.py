import json
from canonical_db.db import CanonicalDB

class InsightflowAdapter:
    def __init__(self, db_path: str = "storage/canonical_db.sqlite"):
        self.db_path = db_path

    def consume_events(self) -> list:
        """Reads immutable events from Canonical DB (No direct DB mutation allowed)."""
        db = CanonicalDB(self.db_path)
        try:
            events = db.get_all_events()
            # InsightFlow consumes all events for observability metrics
            return events
        finally:
            db.close()
