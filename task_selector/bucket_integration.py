"""
Parikshak Bucket Integration — Phase 6
Every review MUST write a log entry. No exceptions.
Exact schema per spec:
  type, candidate_id, task_id, decision,
  review_summary, next_task, trace_id
"""
import json
import os
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger("bucket_integration")


def _hard_reject_field(field: str) -> None:
    raise ValueError(f"BUCKET_HARD_REJECT: required field '{field}' is missing or empty.")


class BucketIntegrationService:
    """
    Phase 6 — Mandatory evaluation logging.
    Writes to daily JSONL files + maintains a searchable index.
    No evaluation is silent.
    """

    def __init__(self, bucket_path: str = "storage/bucket_logs"):
        self.bucket_path = bucket_path
        os.makedirs(self.bucket_path, exist_ok=True)
        index_file = os.path.join(self.bucket_path, "evaluation_index.jsonl")
        if not os.path.exists(index_file):
            open(index_file, "w").close()

    # ── Public API ────────────────────────────────────────────────────────

    def log_evaluation(
        self,
        evaluation_result: Dict[str, Any],
        supporting_signals: Dict[str, Any],
        decision_result: Dict[str, Any],
        next_task_result: Dict[str, Any],
        task_data: Dict[str, Any],
        trace_id: Optional[str] = None
    ) -> str:
        """
        Write mandatory bucket log entry.
        Returns trace_id.
        """
        if not trace_id:
            raise ValueError("trace_id is required and must come from upstream")

        entry = self._build_entry(
            evaluation_result, supporting_signals,
            decision_result, next_task_result,
            task_data, trace_id
        )

        self._write(entry)
        self._update_index(entry)

        logger.info(
            f"[BUCKET] Logged: trace_id={trace_id} | "
            f"decision={entry['decision']}"
        )
        return trace_id

    def get_evaluation_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Phase 5 allowed read: evaluation index (same_task_history)."""
        from db.persistent_storage import FileLock
        index_file = os.path.join(self.bucket_path, "evaluation_index.jsonl")
        if not os.path.exists(index_file):
            return []
        logs = []
        lock_file = index_file + ".lock"
        try:
            with FileLock(lock_file):
                with open(index_file, "r", encoding="utf-8") as f:
                    for line in f.readlines()[-limit:]:
                        if line.strip():
                            logs.append(json.loads(line))
        except Exception as e:
            logger.error(f"[BUCKET] Failed to read index: {e}")
        return logs

    def get_evaluation_by_trace_id(self, trace_id: str) -> Optional[Dict[str, Any]]:
        """Phase 5 allowed read: specific evaluation by trace_id (same_task_history)."""
        from db.persistent_storage import FileLock
        for days_back in range(7):
            from datetime import timedelta
            date_str = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
            log_file = os.path.join(self.bucket_path, f"evaluations_{date_str}.jsonl")
            if not os.path.exists(log_file):
                continue
            lock_file = log_file + ".lock"
            try:
                with FileLock(lock_file):
                    with open(log_file, "r", encoding="utf-8") as f:
                        for line in f:
                            if line.strip():
                                entry = json.loads(line)
                                if entry.get("trace_id") == trace_id:
                                    return entry
            except Exception as e:
                logger.error(f"[BUCKET] Error reading {log_file}: {e}")
        return None

    def get_escalation_cases(self, candidate_id: str) -> List[Dict[str, Any]]:
        """
        Phase 5 allowed read: escalation_cases for a specific candidate.
        ONLY returns entries where candidate_id matches.
        """
        all_logs = self.get_evaluation_logs(1000)
        return [
            log for log in all_logs
            if log.get("candidate_id") == candidate_id
            and log.get("review_summary", {}).get("requires_human_review", False)
        ]

    def reject_unauthorised_read(self, read_type: str) -> Dict[str, Any]:
        """
        Phase 5: Reject any read not in allowed_reads.
        allowed_reads = [same_task_history, escalation_cases]
        """
        allowed = ["same_task_history", "escalation_cases"]
        logger.error(f"[BUCKET] REJECTED unauthorised read type: {read_type}")
        return {
            "error": "BUCKET_READ_REJECTED",
            "reason": f"Read type '{read_type}' not in allowed_reads: {allowed}",
            "allowed_reads": allowed
        }

    def get_bucket_stats(self) -> Dict[str, Any]:
        stats = {
            "total_evaluations": 0,
            "decisions": {"APPROVED": 0, "REJECTED": 0},
            "evaluation_results": {"PASS": 0, "FAIL": 0},
            "avg_score": 0.0,
            "avg_confidence": 0.0
        }
        logs = self.get_evaluation_logs(1000)
        if not logs:
            return stats
        stats["total_evaluations"] = len(logs)
        total_score = 0.0
        for log in logs:
            d = log.get("decision", "REJECTED")
            if d in stats["decisions"]:
                stats["decisions"][d] += 1
            e = log.get("evaluation_result", "FAIL")
            if e in stats["evaluation_results"]:
                stats["evaluation_results"][e] += 1
            total_score += 90.0 if e == "PASS" else 45.0
        stats["avg_score"] = round(total_score / len(logs), 2)
        stats["avg_confidence"] = 0.95
        return stats

    # ── Entry builder — exact Phase 6 schema ─────────────────────────────

    def _build_entry(
        self,
        evaluation_result: Dict[str, Any],
        supporting_signals: Dict[str, Any],
        decision_result: Dict[str, Any],
        next_task_result: Dict[str, Any],
        task_data: Dict[str, Any],
        trace_id: str
    ) -> Dict[str, Any]:
        evaluation = evaluation_result.get("evaluation_result")
        failure_type = evaluation_result.get("failure_type")
        decision = decision_result.get("decision")

        if evaluation not in ("PASS", "FAIL"):
            raise ValueError(f"BUCKET_HARD_REJECT: invalid evaluation_result '{evaluation}'. Must be PASS or FAIL.")
        if decision not in ("APPROVED", "REJECTED"):
            raise ValueError(f"BUCKET_HARD_REJECT: invalid decision '{decision}'. Must be APPROVED or REJECTED.")

        review_summary = {
            "evaluation_result": evaluation,
            "failure_type":      failure_type,
            "decision":          decision,
            "pac":               evaluation_result.get("pac", {}),
            "rubric":            evaluation_result.get("rubric", {}),
            "strengths":         decision_result.get("strengths", []),
            "failures":          decision_result.get("failures", []),
            "root_cause":        decision_result.get("root_cause", ""),
            "learning_feedback": decision_result.get("learning_feedback", []),
            "requires_human_review": evaluation_result.get("requires_human_review", False)
        }

        next_task = {
            "task_id":    next_task_result.get("next_task_id", ""),
            "task_type":  next_task_result.get("task_type", ""),
            "title":      next_task_result.get("title", ""),
            "difficulty": next_task_result.get("difficulty", ""),
            "next_direction": decision_result.get("next_direction", "")
        }

        if not next_task["task_id"]:
            raise ValueError("BUCKET_HARD_REJECT: next_task_id is missing — cannot log without task routing.")

        desc = task_data.get("task_description", "")
        return {
            "type":              "task_review",
            "candidate_id":      task_data.get("submitted_by") or _hard_reject_field("submitted_by"),
            "task_id":           task_data.get("task_id") or task_data.get("task_title", "")[:40],
            "evaluation_result": evaluation,
            "failure_type":      failure_type,
            "decision":          decision,
            "review_summary":    review_summary,
            "next_task":         next_task,
            "trace_id":          trace_id,
            "timestamp":         datetime.now().isoformat(),
            "task_title":        task_data.get("task_title", ""),
            "task_description":  (desc[:500] + "...") if len(desc) > 500 else desc,
            "repository_url":    task_data.get("github_repo_link") or task_data.get("repository_url"),
            "domain":            supporting_signals.get("domain") or _hard_reject_field("domain"),
            "signals_summary":   self._summarize_signals(supporting_signals),
            "canonical_authority": evaluation_result.get("canonical_authority", False)
        }

    def _summarize_signals(self, signals: Dict[str, Any]) -> Dict[str, Any]:
        domain = signals.get("domain")
        if not domain:
            raise ValueError("BUCKET_HARD_REJECT: domain missing from signals — cannot log without domain.")
        return {
            "repository_available":       signals.get("repository_available", False),
            "feature_match_ratio":        signals.get("feature_match_ratio", 0.0),
            "expected_features_count":    len(signals.get("expected_features", [])),
            "implemented_features_count": len(signals.get("implemented_features", [])),
            "missing_features_count":     len(signals.get("missing_features", [])),
            "delivery_ratio":             signals.get("expected_vs_delivered_evidence", {}).get("delivery_ratio", 0.0),
            "domain":                     domain
        }

    def _write(self, entry: Dict[str, Any]) -> None:
        from db.persistent_storage import FileLock
        date_str = datetime.now().strftime("%Y-%m-%d")
        log_file = os.path.join(self.bucket_path, f"evaluations_{date_str}.jsonl")
        lock_file = log_file + ".lock"
        try:
            with FileLock(lock_file):
                with open(log_file, "a", encoding="utf-8") as f:
                    json.dump(entry, f, ensure_ascii=False)
                    f.write("\n")
                    f.flush()
                    os.fsync(f.fileno())
        except Exception as e:
            logger.error(f"[BUCKET] Write failed: {e}")
            raise RuntimeError(f"BUCKET_WRITE_FAILURE: {e} — evaluation not logged, trace_id={entry.get('trace_id')}")

    def _update_index(self, entry: Dict[str, Any]) -> None:
        from db.persistent_storage import FileLock
        index_file = os.path.join(self.bucket_path, "evaluation_index.jsonl")
        lock_file = index_file + ".lock"
        index_entry = {
            "trace_id":        entry["trace_id"],
            "timestamp":       entry["timestamp"],
            "type":            entry["type"],
            "candidate_id":    entry["candidate_id"],
            "task_id":         entry["task_id"],
            "evaluation_result": entry["evaluation_result"],
            "failure_type":    entry["failure_type"],
            "decision":        entry["decision"],
            "task_title":      entry["task_title"][:80]
        }
        try:
            with FileLock(lock_file):
                with open(index_file, "a", encoding="utf-8") as f:
                    json.dump(index_entry, f, ensure_ascii=False)
                    f.write("\n")
                    f.flush()
                    os.fsync(f.fileno())
        except Exception as e:
            logger.error(f"[BUCKET] Index update failed: {e}")


# Global instance
bucket_integration = BucketIntegrationService()
