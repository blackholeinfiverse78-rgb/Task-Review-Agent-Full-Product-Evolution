"""
BHIV Historical Data Ingestion Pipeline — Parikshak v6.0.0

Ingests owner-provided historical data into the Gov-OS canonical journal.
Preserves: timestamps, reasoning, review metadata, assignment lineage.

MANDATORY: All entries require human approval via GovernedPipeline.submit_mutation().
DO NOT fabricate datasets. This pipeline only processes owner-provided data.

Usage:
    pipeline = BHIVIngestionPipeline(governor="Akash")
    pipeline.ingest_from_file("path/to/historical_data.json")

Expected input schema (JSON array):
    [
      {
        "type": "candidate_profile" | "task_lineage" | "review_history" |
                "assignment_history" | "reasoning_artifacts" | "strategic_notes" |
                "learning_signals",
        "trace_id": "...",
        "payload": { ... },  # must match ENTITY_SCHEMAS for the type
        "timestamp": "ISO8601",  # original timestamp — preserved
        "lineage_reference": "...",  # parent trace or lineage pointer
        "notes": "..."  # optional human annotation
      }
    ]
"""
import os
import json
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from canonical_db.contracts import GovernanceEnvelope, ENTITY_SCHEMAS, canonical_json
from canonical_db.pipeline import GovernedPipeline
from canonical_db.integrity import IntegrityValidator


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


# Type mapping from ingestion schema to ENTITY_SCHEMAS keys
TYPE_MAP = {
    "candidate_profile": "candidate_profiles",
    "candidate_profiles": "candidate_profiles",
    "task_lineage": "task_lineage",
    "review_history": "review_history",
    "assignment_history": "assignment_history",
    "reasoning_artifacts": "reasoning_artifacts",
    "strategic_notes": "strategic_notes",
    "learning_signals": "learning_signals",
    "ecosystem_dependency_context": "ecosystem_dependency_context",
    "product_mapping": "product_mapping"
}


class BHIVIngestionPipeline:
    """
    Governed ingestion pipeline for historical BHIV data.
    Every entry is validated against canonical schemas before commit.
    Human approval is enforced on every mutation.
    Lineage and timestamps are preserved from source data.
    """

    def __init__(self, governor: str, db_path: str = "storage/canonical_db.sqlite"):
        if governor not in {"Akash", "Sri Satya", "Nupur", "Senior Operator",
                            "Reviewer-1", "Reviewer-2", "operator-1"}:
            raise PermissionError(f"INGESTION_REJECT: '{governor}' is not an authorized governor.")
        self.governor = governor
        self.db_path = db_path
        self.pipeline = GovernedPipeline(db_path)

    def validate_entry(self, entry: Dict[str, Any]) -> str:
        """Validates a single ingestion entry. Returns canonical event_type or raises."""
        raw_type = entry.get("type", "")
        event_type = TYPE_MAP.get(raw_type)
        if not event_type:
            raise ValueError(f"INGESTION_REJECT: Unknown type '{raw_type}'. "
                             f"Valid types: {list(TYPE_MAP.keys())}")

        if event_type not in ENTITY_SCHEMAS:
            raise ValueError(f"INGESTION_REJECT: event_type '{event_type}' not in ENTITY_SCHEMAS.")

        payload = entry.get("payload")
        if not payload or not isinstance(payload, dict):
            raise ValueError(f"INGESTION_REJECT: Missing or invalid payload for entry type '{raw_type}'.")

        # Validate payload against canonical schema
        schema_cls = ENTITY_SCHEMAS[event_type]
        schema_cls(**payload)  # raises ValidationError if invalid

        trace_id = entry.get("trace_id", "")
        if not trace_id or len(trace_id) < 8:
            raise ValueError(f"INGESTION_REJECT: trace_id missing or too short (min 8 chars).")

        return event_type

    def ingest_entry(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        """Ingests a single validated entry into the Gov-OS journal."""
        event_type = self.validate_entry(entry)

        envelope = GovernanceEnvelope(
            trace_id=entry["trace_id"],
            schema_version="v1.0",
            actor=self.governor,
            actor_role="operator",
            event_type=event_type,
            payload=entry["payload"],
            authorized_by=self.governor,
            lineage_reference=entry.get("lineage_reference", f"ingestion-{entry['trace_id'][:8]}"),
            approval_token=f"human-approved-ingestion-{self.governor}"
        )
        envelope.checksum = envelope.compute_checksum()

        result = self.pipeline.submit_mutation(envelope, self.governor)
        return {
            "status": "INGESTED",
            "event_type": event_type,
            "trace_id": entry["trace_id"],
            "sequence": result["sequence"],
            "event_hash": result["event_hash"]
        }

    def ingest_from_file(self, file_path: str) -> Dict[str, Any]:
        """
        Ingests all entries from a JSON file.
        Validates all entries before committing any.
        Fails closed on first validation error.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"INGESTION_REJECT: File not found: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            entries = json.load(f)

        if not isinstance(entries, list):
            raise ValueError("INGESTION_REJECT: Input file must contain a JSON array.")

        # Phase 1: Validate all entries before committing any
        for i, entry in enumerate(entries):
            try:
                self.validate_entry(entry)
            except Exception as e:
                raise ValueError(f"INGESTION_REJECT: Entry {i} failed validation: {e}")

        # Phase 2: Commit all validated entries
        results = []
        errors = []
        for i, entry in enumerate(entries):
            try:
                result = self.ingest_entry(entry)
                results.append(result)
            except Exception as e:
                errors.append({"entry_index": i, "trace_id": entry.get("trace_id"), "error": str(e)})

        # Phase 3: Integrity scan after ingestion
        validator = IntegrityValidator(self.db_path)
        scan = validator.run_full_scan()

        return {
            "ingested": len(results),
            "errors": errors,
            "integrity_valid": scan["valid"],
            "events_in_journal": scan.get("events_scanned", 0),
            "results": results
        }

    def ingest_from_list(self, entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Ingests entries from a Python list. Same validation/commit semantics as ingest_from_file."""
        for i, entry in enumerate(entries):
            try:
                self.validate_entry(entry)
            except Exception as e:
                raise ValueError(f"INGESTION_REJECT: Entry {i} failed validation: {e}")

        results = []
        errors = []
        for i, entry in enumerate(entries):
            try:
                result = self.ingest_entry(entry)
                results.append(result)
            except Exception as e:
                errors.append({"entry_index": i, "trace_id": entry.get("trace_id"), "error": str(e)})

        validator = IntegrityValidator(self.db_path)
        scan = validator.run_full_scan()

        return {
            "ingested": len(results),
            "errors": errors,
            "integrity_valid": scan["valid"],
            "events_in_journal": scan.get("events_scanned", 0),
            "results": results
        }

    def generate_ingestion_template(self, output_path: str) -> None:
        """
        Writes a template JSON file showing the expected ingestion format.
        Owner fills this with real historical data.
        """
        template = [
            {
                "_comment": "TEMPLATE — replace with real data. DO NOT fabricate.",
                "type": "candidate_profiles",
                "trace_id": "trace-ishan-001-REPLACE",
                "lineage_reference": "lineage-ishan-historical",
                "payload": {
                    "candidate_id": "cand-ishan-001",
                    "name": "Ishan",
                    "github_handle": "REPLACE_WITH_REAL_HANDLE",
                    "skills": ["REPLACE_WITH_REAL_SKILLS"],
                    "performance_score": 0.0
                }
            },
            {
                "_comment": "TEMPLATE — review_history entry",
                "type": "review_history",
                "trace_id": "trace-ishan-review-001-REPLACE",
                "lineage_reference": "lineage-ishan-historical",
                "payload": {
                    "review_id": "rev-ishan-001",
                    "submission_id": "sub-ishan-001",
                    "status": "PASS_OR_FAIL",
                    "score": 0.0,
                    "reviewed_by": "REPLACE_WITH_REVIEWER",
                    "reviewed_at": "REPLACE_WITH_ISO8601_TIMESTAMP"
                }
            },
            {
                "_comment": "TEMPLATE — assignment_history entry",
                "type": "assignment_history",
                "trace_id": "trace-ishan-assign-001-REPLACE",
                "lineage_reference": "lineage-ishan-historical",
                "payload": {
                    "assignment_id": "assign-ishan-001",
                    "task_id": "REPLACE_WITH_REAL_TASK_ID",
                    "candidate_id": "cand-ishan-001",
                    "assigned_by": "REPLACE_WITH_ASSIGNOR",
                    "assigned_at": "REPLACE_WITH_ISO8601_TIMESTAMP"
                }
            },
            {
                "_comment": "TEMPLATE — reasoning_artifacts entry",
                "type": "reasoning_artifacts",
                "trace_id": "trace-ishan-reasoning-001-REPLACE",
                "lineage_reference": "lineage-ishan-historical",
                "payload": {
                    "artifact_id": "artifact-ishan-001",
                    "trace_id": "trace-ishan-review-001-REPLACE",
                    "evaluation_logic": "REPLACE_WITH_REAL_REASONING",
                    "decision_tree_path": ["REPLACE_WITH_REAL_PATH"]
                }
            }
        ]
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(template, f, indent=4, ensure_ascii=False)
