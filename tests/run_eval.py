import sys, logging
logging.disable(logging.CRITICAL)

from task_selector.review_orchestrator import ReviewOrchestrator
from evaluation_engine.review_engine import ReviewEngine
from models.schemas import Task
from models.persistent_storage import product_storage
from datetime import datetime

product_storage.clear_all()
orchestrator = ReviewOrchestrator(ReviewEngine())

description = """This repository implements a deterministic Task Review Agent that evaluates task submissions by aligning task title, description, and repository content with system-defined architectural rules. The system is a production-oriented evaluation pipeline, not a probabilistic AI reviewer, ensuring consistent, reproducible, and verifiable scoring outcomes.

## System Overview

The core enhancement is the integration of a Registry-Aware Validation Layer. Before any scoring occurs, each submission is validated against a Blueprint Registry, enforcing structural discipline. The architecture follows strict separation of concerns: validator.py handles validation, evaluation_engine.py orchestrates scoring, and review_orchestrator.py manages the full lifecycle.

## API Contract

The REST API exposes the following endpoints with strict Pydantic schema validation:

```
POST /api/v1/lifecycle/submit
  Request:  { task_title, task_description, module_id, schema_version, github_repo_link }
  Response: { submission_id, score, status, next_task }

GET /api/v1/lifecycle/review/{submission_id}
  Response: { score, status, title_analysis, description_analysis, repository_analysis }
```

All API contracts are enforced via Pydantic schema validation. Invalid payloads return HTTP 422 with deterministic error messages. The service layer adheres to a strict interface defined in review_engine_interface.py.

## Evaluation Pipeline Stages

The pipeline follows a strict five-stage execution flow:

1. Registry Validation — validate module_id, lifecycle_stage, schema_version against Blueprint Registry
2. Title Analysis — technical keyword detection, clarity scoring, alignment with description (weight: 20 pts)
3. Description Analysis — content depth, structure quality, technical density, requirement completeness (weight: 40 pts)
4. Repository Analysis — GitHub API assessment of code quality, architecture, documentation, file structure (weight: 40 pts)
5. Score Combination — deterministic formula: total = title_score + description_score + repository_score

Scoring formula applied by ScoringEngine:

```python
total_score = title_score + description_score + repository_score  # max 100
status = "pass" if total_score >= 80 else "borderline" if total_score >= 50 else "fail"
```

## Component Integration

Components integrate through explicit dependency injection. ReviewOrchestrator receives a ReviewEngineInterface instance at construction, decoupling orchestration from evaluation implementation:

```python
orchestrator = ReviewOrchestrator(ReviewEngine())
result = orchestrator.process_submission(task)
```

EvaluationEngine composes TitleAnalyzer, DescriptionAnalyzer, RepositoryAnalyzer, and ScoringEngine as injected services. Each service is independently testable and replaceable without modifying the pipeline. The ReviewEngine bridges EvaluationEngine output to the ReviewOutput Pydantic schema consumed by the API layer.

## Registry Validation Layer

The registry validation layer enforces structural discipline before any evaluation occurs:
- module_id must exist in the Blueprint Registry
- module lifecycle_stage must be production or development (not deprecated, not planning)
- schema_version must match the registered module version
- deprecated modules are rejected with deterministic error messages

If validation fails, the system returns a rejection response with score 0 and a corrective next task. No evaluation engine cycles are consumed on invalid submissions.

## Acceptance Criteria and Test Coverage

The system meets the following acceptance criteria:
- Valid module submission proceeds to full evaluation pipeline and returns score with next task
- Deprecated module submission returns rejection with reason before scoring begins
- Schema version mismatch returns INVALID status with specific mismatch details
- Same inputs always produce identical scores across repeated runs (determinism constraint)
- GitHub API timeout falls back gracefully to title and description scoring only (max 60 pts)

Test scenarios covered:

```
test_registry_validation.py   — valid, invalid, deprecated, schema-mismatch cases
test_scoring_engine.py        — deterministic score verification across 3 input tiers
test_review_orchestrator.py  — full lifecycle integration from submit to next task
test_review_engine.py         — evaluation engine unit tests with mock repository data
```

## Architecture and Scalability

The system is designed for production deployment with the following characteristics:
- Deterministic evaluation engine with no LLM-based reasoning or probabilistic scoring
- Modular service architecture enabling independent scaling of each pipeline stage
- In-memory storage layer with explicit lifecycle tracking via TaskSubmission, ReviewRecord, NextTaskRecord
- Registry-driven enforcement ensuring all evaluated work aligns with declared system modules
- Pydantic validation on all input and output schemas for strict API contract adherence
- CORS configuration for frontend integration with the React client at localhost:3000

This implementation transforms the Task Review Agent from a quality-based evaluator into a structure-aware enforcement system that guarantees structural correctness before scoring, consistent scoring behavior, and full alignment with system design principles.
"""

task = Task(
    task_id='ishan-registry-002',
    task_title='Registry-Aware Task Review Agent with Deterministic Evaluation Pipeline and API Integration',
    task_description=description,
    submitted_by='Ishan',
    timestamp=datetime.now(),
    module_id='task-review-agent',
    schema_version='v1.0',
    github_repo_link='https://github.com/blackholeinfiverse78-rgb/Task-Review-Agent-Full-Product-Evolution'
)

result = orchestrator.process_submission(task)
review = result['review']
next_task = result['next_task']

print("SUBMISSION_ID=" + result['submission_id'])
print("REVIEW_ID=" + result['review_id'])
print("TITLE_SCORE=" + str(review['title_score']))
print("DESC_SCORE=" + str(review['description_score']))
print("REPO_SCORE=" + str(review['repository_score']))
print("TOTAL_SCORE=" + str(review['score']))
print("STATUS=" + review['status'])
print("SUMMARY=" + review['evaluation_summary'])
hints = review.get('improvement_hints', [])
for i, h in enumerate(hints):
    print(f"HINT_{i+1}=" + h)
print("NEXT_TITLE=" + next_task['title'])
print("NEXT_TYPE=" + next_task['task_type'])
print("NEXT_DIFF=" + next_task['difficulty'])
print("NEXT_FOCUS=" + next_task['focus_area'])
print("NEXT_OBJ=" + next_task['objective'])
print("NEXT_REASON=" + next_task['reason'])
print("REG_STATUS=" + result['registry_validation']['status'])
