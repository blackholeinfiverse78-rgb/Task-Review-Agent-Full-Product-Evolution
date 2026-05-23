"""
Task Review Engine - Final Convergence Adapter
Bridges the evaluation engine with the ReviewOutput schema.
"""
from typing import Optional
from contracts.schemas import Task, ReviewOutput, Analysis, Meta
from contracts.review_engine_interface import ReviewEngineInterface
from evaluation_engine.orchestrator import evaluation_orchestrator
import logging
import time

logger = logging.getLogger("review_engine")

class ReviewEngine(ReviewEngineInterface):
    def __init__(self):
        pass

    # ── Allow ReviewEngine.review_task(task) (classmethod-style calls from tests) ──
    def __class_getitem__(cls, item):
        return cls

    @classmethod
    def review_task(cls, task: Task) -> "ReviewOutput":
        """
        Evaluate task and return ReviewOutput.
        Callable as both classmethod and instance method.
        """
        return cls._do_review(task)

    @classmethod
    def _do_review(cls, task: Task) -> "ReviewOutput":
        start_time = time.time()

        # Clean description — strip legacy GitHub marker if present
        description = task.task_description
        github_url = None
        clean_description = description

        if "--- GitHub Repository Metrics ---" in description:
            try:
                marker = "--- GitHub Repository Metrics ---"
                parts = description.split(marker)
                clean_description = parts[0].strip()
                content = parts[1].strip()
                import json
                if "---" in content:
                    content = content.split("---")[0].strip()
                metrics = json.loads(content)
                github_url = metrics.get('url')
            except Exception as e:
                logger.warning(f"Failed to extract GitHub URL from description: {e}")

        # PDF text
        pdf_text = getattr(task, 'pdf_extracted_text', "") or ""
        if not pdf_text and "--- Extracted PDF Content ---" in description:
            try:
                pdf_text = description.split("--- Extracted PDF Content ---")[1].strip()
            except (IndexError, AttributeError):
                pass

        # Use deterministic evaluation engine
        eval_output = evaluation_orchestrator.evaluate_submission(
            task_title=task.task_title,
            task_description=clean_description,
            repository_url=getattr(task, 'github_repo_link', None) or github_url,
            module_id=getattr(task, 'module_id', 'task-review-agent'),
            schema_version=getattr(task, 'schema_version', 'v1.0'),
            pdf_text=pdf_text
        )

        eval_result = eval_output.get("evaluation_result", "FAIL")
        failure_type = eval_output.get("failure_type")

        # Derive numeric score from TEXT signals only (independent of binary rule engine)
        word_count = len(clean_description.split())
        title_words = len(task.task_title.split())
        tech_keywords = {
            "api", "database", "async", "security", "jwt", "test", "layer",
            "architecture", "objective", "requirement", "constraint", "schema",
            "pipeline", "validation", "module", "microservice", "cache",
            "frontend", "backend", "integration", "implementation", "deploy",
            "kubernetes", "docker", "migration", "cluster", "authentication",
            "authorization", "access", "control", "load", "balancing"
        }
        structure_markers = {"objective", "requirement", "constraint", "deliverable", "timeline", "scope"}

        desc_lower = (task.task_title + " " + clean_description).lower()
        keyword_hits = sum(1 for kw in tech_keywords if kw in desc_lower)
        structure_hits = sum(1 for m in structure_markers if m in desc_lower)
        has_tech = keyword_hits >= 3

        # Compute score 0-100 purely from content signals
        base = 0
        base += min(30, word_count // 3)      # up to 30 pts for word count
        base += min(10, title_words * 2)       # up to 10 pts for title length
        base += min(30, keyword_hits * 4)      # up to 30 pts for technical keywords
        base += min(20, structure_hits * 6)    # up to 20 pts for structure markers
        base += min(10, len(clean_description) // 100)  # up to 10 pts for raw length
        score = min(100, base)

        # Classify status
        if score >= 75:
            status = "pass"
        elif score >= 50:
            status = "borderline"
        else:
            status = "fail"


        # Analysis sub-scores
        analysis = Analysis(
            technical_quality=score,
            clarity=score,
            discipline_signals=score
        )

        failure_reasons = [failure_type] if failure_type else []
        if not failure_reasons and score < 50:
            failure_reasons = ["Insufficient technical content in title and description."]

        improvement_hints = []
        if failure_type == "incomplete":
            improvement_hints = ["Add a GitHub repository with code.", "Add README and tests."]
        elif failure_type == "schema_violation":
            improvement_hints = ["Provide more detailed task description (min 50 words)."]
        elif failure_type == "incorrect_logic":
            improvement_hints = ["Ensure delivery ratio meets minimum threshold.", "Add more detail."]

        meta = Meta(
            evaluation_time_ms=int((time.time() - start_time) * 1000),
            mode="hybrid"
        )

        return ReviewOutput(
            score=score,
            readiness_percent=score,
            status=status,
            failure_reasons=failure_reasons[:3],
            improvement_hints=improvement_hints[:5],
            analysis=analysis,
            meta=meta,
            feature_coverage=0.0,
            architecture_score=0.0,
            code_quality_score=0.0,
            completeness_score=float(score),
            missing_features=[],
            requirement_match=0.0,
            evaluation_summary=f"Deterministic evaluation: {eval_result}",
            documentation_score=0.0,
            documentation_alignment="low",
            analysis_pdf={},
            title_score=0.0,
            description_score=float(score),
            repository_score=0.0
        )

    def evaluate(self, task: dict) -> dict:
        task_obj = Task(**task)
        result = self.review_task(task_obj)
        return result.model_dump()
