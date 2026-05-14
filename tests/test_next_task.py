"""
Test next task storage and retrieval
"""
import sys
import os

# Add paths for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from db.persistent_storage import product_storage
from task_selector.review_orchestrator import ReviewOrchestrator
from contracts.schemas import Task
from datetime import datetime

def test_next_task_storage():
    """Test that next tasks are being stored and retrieved correctly"""
    
    # Clear storage first
    product_storage.clear_all()
    
    # Create orchestrator
    orchestrator = ReviewOrchestrator()
    
    # Create test task
    task = Task(
        task_id="test-task-001",
        task_title="Test Authentication API",
        task_description="Build a simple authentication API with JWT tokens",
        submitted_by="test-user",
        github_repo_link="https://github.com/test/auth-api",
        module_id="task-review-agent",
        schema_version="v1.0",
        timestamp=datetime.now()
    )
    
    # Process submission
    result = orchestrator.process_submission(task)
    
    print("=" * 60)
    print("NEXT TASK STORAGE TEST")
    print("=" * 60)
    
    submission_id = result.get("submission_id")
    next_task_id = result.get("next_task_id")
    
    print(f"Submission ID: {submission_id}")
    print(f"Next Task ID: {next_task_id}")
    
    # Check if submission exists
    submission = product_storage.get_submission(submission_id)
    print(f"Submission stored: {submission is not None}")
    
    # Check if review exists
    review = product_storage.get_review_by_submission(submission_id)
    print(f"Review stored: {review is not None}")
    
    # Check if next task exists by ID
    next_task_by_id = product_storage.get_next_task(next_task_id)
    print(f"Next task by ID: {next_task_by_id is not None}")
    
    # Check if next task exists by submission
    next_task_by_submission = product_storage.get_next_task_by_submission(submission_id)
    print(f"Next task by submission: {next_task_by_submission is not None}")
    
    if next_task_by_submission:
        print(f"Next task details:")
        print(f"  ID: {next_task_by_submission.next_task_id}")
        print(f"  Type: {next_task_by_submission.task_type}")
        print(f"  Title: {next_task_by_submission.title}")
        print(f"  Difficulty: {next_task_by_submission.difficulty}")
    
    # Show all stored data
    print(f"\nStorage contents:")
    print(f"  Submissions: {len(product_storage.submissions)}")
    print(f"  Reviews: {len(product_storage.reviews)}")
    print(f"  Next tasks: {len(product_storage.next_tasks)}")
    
    # List all next task IDs
    print(f"  Next task IDs: {list(product_storage.next_tasks.keys())}")
    
    return submission_id, next_task_id

if __name__ == "__main__":
    test_next_task_storage()