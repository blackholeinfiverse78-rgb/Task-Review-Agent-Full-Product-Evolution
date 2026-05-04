"""
Review Orchestrator (Single Pipeline Controller)

- assignment → signals → merge → validation
"""

from assignment_engine import evaluation_engine.assignment_engine
from signal_engine import evaluation_engine.signal_engine
from merge_logic import merge_logic
from validator import evaluation_engine.validator

def review_orchestrator(input_data):
    """
    Main entry point for the deterministic evaluation pipeline.
    """
    # 1. Authoritative Assignment
    assignment = assignment_engine(input_data)
    
    # 2. Supporting Signals
    signals = signal_engine(input_data)
    
    # 3. Hierarchical Merge
    merged = merge_logic(assignment, signals)
    
    # 4. Strict Validation
    return validator(merged)

# Compatibility with existing internal architecture
from task_selector.review_orchestrator import ReviewOrchestrator
orchestrator_service = ReviewOrchestrator()
orchestrator_service.review_orchestrator = review_orchestrator
