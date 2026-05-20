"""
Parikshak Graph Engine — Phase 3
Deterministic task graph traversal.

Input:  current_task_id + evaluation_result (pass/fail)
Output: next_task_id

Rules:
  pass (score >= 6) → next_tasks[0]
  fail (score <  6) → failure_tasks[0]

BOUNDARY RULES:
  - NO task generation — only traversal of existing graph
  - Same (task_id, result) always returns same next_task_id
  - Graph loaded from task_database.json — never mutated at runtime
"""
import json
import os
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger("graph_engine")

_DB_PATH = os.path.join(os.path.dirname(__file__), "task_database.json")


class GraphEngine:
    """
    Deterministic graph traversal over the task database.
    Reads task_database.json once at startup — immutable at runtime.
    """

    PASS_THRESHOLD = 6.0  # score >= 6 → pass branch

    def __init__(self, db_path: str = _DB_PATH):
        self._db_path = db_path
        self._tasks: Dict[str, Dict[str, Any]] = {}
        self._load()

    def _load(self) -> None:
        try:
            with open(self._db_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._tasks = data.get("tasks", {})
            logger.info(f"[GRAPH ENGINE] Loaded {len(self._tasks)} tasks from database")
        except Exception as e:
            logger.error(f"[GRAPH ENGINE] Failed to load task database: {e}")
            self._tasks = {}

    # ── Public API ────────────────────────────────────────────────────────

    def traverse(
        self,
        current_task_id: str,
        score_10: float,
        decision: str = ""
    ) -> Dict[str, Any]:
        """
        Deterministic graph traversal.

        Args:
            current_task_id: The task just evaluated
            score_10:        Evaluation score 0–10
            decision:        "APPROVED" or "REJECTED" (optional, derived from score if empty)

        Returns:
            {
              next_task_id, title, task_type, difficulty,
              branch, selection_reason, source
            }
        """
        # Derive pass/fail from score if decision not provided
        if decision == "APPROVED" or score_10 >= self.PASS_THRESHOLD:
            branch = "pass"
        else:
            branch = "fail"

        task = self._tasks.get(current_task_id)

        if not task:
            # Task not in DB — fall back to selection engine logic
            logger.warning(f"[GRAPH ENGINE] task_id '{current_task_id}' not in database — using fallback")
            return self._fallback(current_task_id, branch, score_10)

        # Select next task from correct branch
        if branch == "pass":
            candidates = task.get("next_tasks", [])
            branch_label = "next_tasks"
        else:
            candidates = task.get("failure_tasks", [])
            branch_label = "failure_tasks"

        if not candidates:
            logger.warning(f"[GRAPH ENGINE] No {branch_label} for '{current_task_id}' — using fallback")
            return self._fallback(current_task_id, branch, score_10)

        next_task_id = candidates[0]  # Always first — deterministic
        next_task = self._tasks.get(next_task_id, {})

        logger.info(
            f"[GRAPH ENGINE] {current_task_id} + {branch} -> {next_task_id} "
            f"({next_task.get('title', '?')})"
        )

        return {
            "next_task_id":     next_task_id,
            "title":            next_task.get("title", "Task Assignment"),
            "task_type":        self._branch_to_type(branch),
            "difficulty":       next_task.get("difficulty", "beginner"),
            "objective":        next_task.get("description", "Complete the assigned task"),
            "dharma":           next_task.get("dharma", ""),
            "product":          next_task.get("product", "niyantran"),
            "layer":            next_task.get("layer", "governance"),
            "subsystem":        next_task.get("subsystem", ""),
            "capability":       next_task.get("capability", ""),
            "completion_signals": next_task.get("completion_signals", []),
            "branch":           branch,
            "selection_reason": (
                f"graph_traversal: {current_task_id} + {branch} "
                f"-> {branch_label}[0] = {next_task_id}"
            ),
            "source":           "task_graph",
        }

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Return full task record. None if not found."""
        return self._tasks.get(task_id)

    def get_prerequisites(self, task_id: str) -> List[str]:
        """Return prerequisite task_ids for a task."""
        task = self._tasks.get(task_id, {})
        return task.get("prerequisites", [])

    def get_completion_signals(self, task_id: str) -> List[str]:
        """Return completion signals for a task."""
        task = self._tasks.get(task_id, {})
        return task.get("completion_signals", [])

    def list_tasks_by_product(self, product: str) -> List[str]:
        """Return all task_ids for a given product."""
        return [
            tid for tid, t in self._tasks.items()
            if t.get("product") == product
        ]

    def list_tasks_by_difficulty(self, difficulty: str) -> List[str]:
        """Return all task_ids for a given difficulty."""
        return [
            tid for tid, t in self._tasks.items()
            if t.get("difficulty") == difficulty
        ]

    def validate_task_id(self, task_id: str) -> bool:
        """Check if task_id exists in the database."""
        return task_id in self._tasks

    def check_completion_signals(
        self,
        task_id: str,
        repo_signals: dict
    ) -> dict:
        """
        Gap 3: Check completion_signals for a task against repo signals.
        Deterministic — same repo_signals always returns same result.

        Checks each signal keyword against:
          - repo file paths
          - component names (tests, docs, routes, services, models)
          - quality signals (readme_score, documentation_density)
          - architecture signals (has_layers, modular, layer_count)

        Returns:
            {
              task_id, required_signals, met_signals,
              unmet_signals, completion_ratio, is_complete
            }
        """
        task = self._tasks.get(task_id)
        if not task:
            return {
                "task_id": task_id,
                "required_signals": [],
                "met_signals": [],
                "unmet_signals": [],
                "completion_ratio": 0.0,
                "is_complete": False,
                "error": f"task_id '{task_id}' not in database"
            }

        required = task.get("completion_signals", [])
        if not required:
            return {
                "task_id": task_id,
                "required_signals": [],
                "met_signals": [],
                "unmet_signals": [],
                "completion_ratio": 1.0,
                "is_complete": True
            }

        # Build a flat searchable text from all repo signals
        structure   = repo_signals.get("structure", {})
        components  = repo_signals.get("components", {})
        quality     = repo_signals.get("quality", {})
        architecture = repo_signals.get("architecture", {})
        metadata    = repo_signals.get("metadata", {})

        all_paths = list(structure.get("raw_paths", []))
        for bucket in components.values():
            if isinstance(bucket, list):
                all_paths.extend(bucket)
        searchable = " ".join(all_paths).lower()

        # Signal → check mapping
        signal_checks = {
            # Presence checks
            "github_repo_present":      bool(metadata.get("name")),
            "readme_exists":            quality.get("readme_score", 0) >= 1,
            "api_endpoints_present":    len(components.get("routes", [])) > 0,
            "folder_structure_present": architecture.get("modular", False),
            "min_5_files":              structure.get("total_files", 0) >= 5,
            "min_3_services":           len(components.get("services", [])) >= 3,
            "min_2_nodes":              structure.get("total_files", 0) >= 2,
            "tests_present":            len(components.get("tests", [])) > 0,
            "unit_tests":               len(components.get("tests", [])) > 0,
            "integration_tests":        any("integr" in p for p in components.get("tests", [])),
            "api_docs":                 len(components.get("docs", [])) > 0,
            "service_layer_present":    len(components.get("services", [])) > 0,
            "db_integration":           any(k in searchable for k in ["db", "database", "model", "schema"]),
            "jwt_auth_present":         any(k in searchable for k in ["auth", "jwt", "token"]),
            "docker_compose":           any(k in searchable for k in ["docker", "compose"]),
            "kubernetes_deployment":    any(k in searchable for k in ["kubernetes", "k8s", "helm"]),
            "clean_architecture":       architecture.get("layer_count", 0) >= 3,
            "domain_layer_isolated":    architecture.get("has_layers", False),
            "infrastructure_separated": architecture.get("layer_count", 0) >= 2,
            "normalised_schema":        any(k in searchable for k in ["migration", "schema", "model"]),
            "migrations_present":       any("migrat" in p for p in all_paths),
            "rubric_implemented":        any(k in searchable for k in ["rubric", "score", "evaluat"]),
            "binary_criteria":          any(k in searchable for k in ["rubric", "criteria", "binary"]),
            "deterministic_formula":    any(k in searchable for k in ["formula", "score", "calculat"]),
            "structured_output":        len(components.get("models", [])) > 0,
            "pac_detection":            any(k in searchable for k in ["pac", "proof", "architecture"]),
            "binary_signals":           any(k in searchable for k in ["signal", "binary", "detect"]),
            "repo_analysis":            bool(metadata.get("name")),
            "deterministic_pipeline":   architecture.get("layer_count", 0) >= 2,
            "bucket_logging":           any(k in searchable for k in ["bucket", "log", "storage"]),
            "same_input_same_output":   len(components.get("tests", [])) > 0,
            "ros2_package":             any(k in searchable for k in ["ros", "package", "launch"]),
            "pub_sub_comm":             any(k in searchable for k in ["publish", "subscribe", "topic"]),
            "launch_file":              any("launch" in p for p in all_paths),
            "sensor_integrated":        any(k in searchable for k in ["sensor", "lidar", "camera"]),
            "slam_implemented":         any(k in searchable for k in ["slam", "navigation", "map"]),
            "solidity_contract":        any(k in searchable for k in ["solidity", ".sol", "contract"]),
            "hardhat_tests":            any(k in searchable for k in ["hardhat", "test", "mocha"]),
            "erc20_implemented":        any(k in searchable for k in ["erc20", "token", "transfer"]),
            "staking_contract":         any(k in searchable for k in ["stake", "staking", "reward"]),
            "web3_frontend":            any(k in searchable for k in ["web3", "frontend", "react"]),
            "dashboard_present":        any(k in searchable for k in ["dashboard", "chart", "metric"]),
            "kpi_metrics":              any(k in searchable for k in ["kpi", "metric", "analytics"]),
        }

        met   = [s for s in required if signal_checks.get(s, False)]
        unmet = [s for s in required if not signal_checks.get(s, False)]
        ratio = len(met) / len(required) if required else 1.0

        logger.info(
            f"[GRAPH ENGINE] completion_signals for {task_id}: "
            f"{len(met)}/{len(required)} met (ratio={ratio:.2f})"
        )

        return {
            "task_id":          task_id,
            "required_signals": required,
            "met_signals":      met,
            "unmet_signals":    unmet,
            "completion_ratio": round(ratio, 3),
            "is_complete":      ratio >= 1.0,
        }

    def get_stats(self) -> Dict[str, Any]:
        """Return database statistics."""
        products = {}
        difficulties = {"beginner": 0, "intermediate": 0, "advanced": 0}
        for t in self._tasks.values():
            p = t.get("product", "unknown")
            products[p] = products.get(p, 0) + 1
            d = t.get("difficulty", "beginner")
            if d in difficulties:
                difficulties[d] += 1
        return {
            "total_tasks": len(self._tasks),
            "by_product": products,
            "by_difficulty": difficulties,
        }

    # ── Private ───────────────────────────────────────────────────────────

    def _fallback(self, task_id: str, branch: str, score_10: float) -> Dict[str, Any]:
        """Fallback when task_id not in DB — return safe default."""
        if branch == "pass":
            fallback_id = "NT-ADV-B-001"
        elif score_10 >= 4.0:
            fallback_id = "NT-REI-B-001"
        else:
            fallback_id = "NT-COR-B-001"

        meta = self._tasks.get(fallback_id, {})
        return {
            "next_task_id":     fallback_id,
            "title":            meta.get("title", "Foundational Implementation Correction"),
            "task_type":        self._branch_to_type(branch),
            "difficulty":       meta.get("difficulty", "beginner"),
            "objective":        meta.get("description", "Complete the assigned task"),
            "dharma":           meta.get("dharma", ""),
            "product":          meta.get("product", "niyantran"),
            "layer":            meta.get("layer", "governance"),
            "subsystem":        meta.get("subsystem", ""),
            "capability":       meta.get("capability", ""),
            "completion_signals": meta.get("completion_signals", []),
            "branch":           branch,
            "selection_reason": f"fallback: task_id '{task_id}' not in DB -> {fallback_id}",
            "source":           "task_graph",
        }

    def _branch_to_type(self, branch: str) -> str:
        return {"pass": "advancement", "fail": "correction"}.get(branch, "correction")


# Global instance
graph_engine = GraphEngine()
