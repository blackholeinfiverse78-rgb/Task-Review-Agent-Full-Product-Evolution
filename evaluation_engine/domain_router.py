"""
Domain Router - Routes evaluations through domain-aware pipelines
Detects domain from task signals and applies domain-specific feature expectations
"""
from typing import Dict, Any
import logging

logger = logging.getLogger("domain_router")

# Domain definitions: name → keywords that identify it + expected feature set
DOMAIN_PROFILES: Dict[str, Dict[str, Any]] = {
    "backend": {
        "keywords": {"api", "rest", "graphql", "fastapi", "flask", "django", "endpoint",
                     "route", "controller", "service", "database", "sql", "orm", "jwt",
                     "authentication", "auth", "server", "backend", "microservice"},
        "expected_features": ["api", "auth", "database", "service", "model"],
        "weight_overrides": {"repository_score": 1.2, "description_score": 1.0, "title_score": 0.8},
        "min_files": 8,
    },
    "frontend": {
        "keywords": {"react", "vue", "angular", "component", "ui", "dashboard", "frontend",
                     "css", "tailwind", "html", "typescript", "javascript", "redux", "state"},
        "expected_features": ["frontend", "dashboard", "service"],
        "weight_overrides": {"repository_score": 1.1, "description_score": 1.0, "title_score": 0.9},
        "min_files": 6,
    },
    "infrastructure": {
        "keywords": {"docker", "kubernetes", "k8s", "terraform", "ansible", "ci", "cd",
                     "pipeline", "deployment", "devops", "helm", "nginx", "aws", "azure",
                     "gcp", "cloud", "container", "orchestration"},
        "expected_features": ["docker", "deployment", "pipeline"],
        "weight_overrides": {"repository_score": 1.3, "description_score": 0.9, "title_score": 0.8},
        "min_files": 4,
    },
    "fullstack": {
        "keywords": {"fullstack", "full-stack", "full stack", "frontend", "backend",
                     "react", "fastapi", "node", "express"},
        "expected_features": ["api", "frontend", "database", "auth", "service"],
        "weight_overrides": {"repository_score": 1.2, "description_score": 1.1, "title_score": 0.9},
        "min_files": 12,
    },
    "ml": {
        "keywords": {"machine learning", "ml", "model", "training", "inference", "dataset",
                     "neural", "pytorch", "tensorflow", "sklearn", "prediction", "classification"},
        "expected_features": ["model", "pipeline", "evaluation"],
        "weight_overrides": {"repository_score": 1.1, "description_score": 1.2, "title_score": 0.9},
        "min_files": 5,
    },
}



class DomainRouter:
    """
    Routes each evaluation through a domain-aware context.
    Detects domain from title + description signals, then adjusts
    expected features and score weight overrides accordingly.
    """

    def detect_domain(self, task_title: str, task_description: str) -> str:
        """Detect domain from task text. Returns domain name string."""
        combined = (task_title + " " + task_description).lower()

        scores: Dict[str, int] = {}
        for domain, profile in DOMAIN_PROFILES.items():
            hit_count = sum(1 for kw in profile["keywords"] if kw in combined)
            if hit_count > 0:
                scores[domain] = hit_count

        if not scores:
            raise ValueError(
                f"DOMAIN_HARD_REJECT: No domain matched for input. "
                f"Task must contain keywords from one of: {list(DOMAIN_PROFILES.keys())}. "
                "No default routing permitted."
            )

        detected = max(scores, key=lambda d: scores[d])
        logger.info(f"[DOMAIN ROUTER] Detected domain: '{detected}' (hits: {scores[detected]})")
        return detected

    def get_domain_context(self, domain: str) -> Dict[str, Any]:
        """Return the full domain profile for a detected domain."""
        if domain not in DOMAIN_PROFILES:
            raise ValueError(
                f"DOMAIN_HARD_REJECT: Unknown domain '{domain}'. "
                f"Must be one of: {list(DOMAIN_PROFILES.keys())}."
            )
        return DOMAIN_PROFILES[domain]

    def apply_domain_adjustments(
        self,
        base_scores: Dict[str, float],
        domain: str,
        supporting_signals: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Apply domain-specific weight overrides to component scores and
        inject domain-aware missing feature hints.

        Args:
            base_scores: {"title_score": x, "description_score": y, "repository_score": z}
            domain: detected domain string
            supporting_signals: full signal dict from signal engine

        Returns:
            Adjusted scores + domain metadata
        """
        profile = self.get_domain_context(domain)
        overrides = profile["weight_overrides"]

        adjusted = {
            "title_score": round(base_scores.get("title_score", 0) * overrides.get("title_score", 1.0), 2),
            "description_score": round(base_scores.get("description_score", 0) * overrides.get("description_score", 1.0), 2),
            "repository_score": round(base_scores.get("repository_score", 0) * overrides.get("repository_score", 1.0), 2),
        }

        # Cap each component at its original max
        adjusted["title_score"] = min(adjusted["title_score"], 20.0)
        adjusted["description_score"] = min(adjusted["description_score"], 40.0)
        adjusted["repository_score"] = min(adjusted["repository_score"], 40.0)

        # Domain-aware missing feature hints
        implemented = set(supporting_signals.get("implemented_features", []))
        domain_expected = set(profile["expected_features"])
        domain_missing = sorted(domain_expected - implemented)

        # File count check against domain minimum
        file_count = supporting_signals.get("implementation_files", 0)
        min_files = profile["min_files"]
        file_gap = max(0, min_files - file_count)

        logger.info(
            f"[DOMAIN ROUTER] Domain '{domain}' adjustments applied. "
            f"Missing domain features: {domain_missing}, file gap: {file_gap}"
        )

        return {
            "adjusted_scores": adjusted,
            "domain": domain,
            "domain_expected_features": profile["expected_features"],
            "domain_missing_features": domain_missing,
            "file_count_gap": file_gap,
            "weight_overrides_applied": overrides,
        }

    def enrich_signals(
        self,
        supporting_signals: Dict[str, Any],
        task_title: str,
        task_description: str
    ) -> Dict[str, Any]:
        """
        Detect domain and inject domain context into supporting signals.
        Called by final_convergence before assignment engine evaluation.
        """
        domain = self.detect_domain(task_title, task_description)
        domain_context = self.get_domain_context(domain)

        enriched = dict(supporting_signals)
        enriched["domain"] = domain
        enriched["domain_expected_features"] = domain_context["expected_features"]
        enriched["domain_min_files"] = domain_context["min_files"]
        enriched["domain_weight_overrides"] = domain_context["weight_overrides"]

        return enriched


# Global instance
domain_router = DomainRouter()
