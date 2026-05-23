import sys
import os
import json
import time
import uuid
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
import multiprocessing

# Add workspace root to system path
sys.path.append(os.getcwd())

from db.persistent_storage import (
    product_storage, TaskSubmission, ReviewRecord, NextTaskRecord, TaskStatus, TaskType
)
from task_selector.bucket_integration import bucket_integration
from replay_audit.atomic_persistence import write_replay_checkpoint, load_checkpoint
from replay_audit.replay_engine import replay_engine

# Top-level helper functions for pickling compatibility on Windows

def _submit_one(index):
    # We need to re-initialize product_storage in sub-processes
    from db.persistent_storage import product_storage, TaskSubmission, TaskStatus
    from datetime import datetime
    import uuid
    
    sub_id = f"sub-test-{index}-{uuid.uuid4().hex[:6]}"
    submission = TaskSubmission(
        submission_id=sub_id,
        task_id=f"task-concurrency-{index}",
        task_title=f"Concurrency Submission {index}",
        task_description=f"This is a description for concurrency submission {index} with enough length.",
        submitted_by=f"Worker-{index}",
        submitted_at=datetime.now(),
        status=TaskStatus.SUBMITTED,
        previous_task_id=None,
        module_id="task-review-agent",
        schema_version="v1.0",
        registry_validation_status="VALID",
        review_state="PENDING_REVIEW"
    )
    product_storage.store_submission(submission)
    return sub_id


def _attempt_approve(args):
    worker_id, review_id = args
    from db.persistent_storage import product_storage
    from contracts.review_models import ReviewState
    
    success = False
    error_msg = ""
    
    # We acquire lock to do read-modify-write
    with product_storage.lock():
        product_storage._load_nolock()
        rev = product_storage.get_review(review_id)
        if rev.review_state in ["APPROVED", "REJECTED"]:
            error_msg = "Already approved (state check)"
        elif rev.version != 1:
            error_msg = f"Version mismatch: expected 1, got {rev.version}"
        else:
            # Perform state update
            rev.review_state = "APPROVED"
            rev.version += 1
            product_storage.reviews[review_id] = rev
            product_storage._save_nolock()
            success = True
            
    return success, error_msg


def _log_one(index):
    from task_selector.bucket_integration import bucket_integration
    import uuid
    
    trace_id = f"trace-bucket-{index}-{uuid.uuid4().hex[:6]}"
    mock_eval = {
        "evaluation_result": "PASS",
        "failure_type": None,
        "pac": {},
        "rubric": {},
        "requires_human_review": False
    }
    mock_signals = {
        "domain": "engineering",
        "repository_available": True,
        "expected_vs_delivered_evidence": {"delivery_ratio": 0.9}
    }
    mock_decision = {
        "decision": "APPROVED",
        "confidence": 1.0,
        "next_direction": "advancement"
    }
    mock_next_task = {
        "next_task_id": f"task-next-{index}",
        "task_type": "advancement",
        "title": f"Next Task Title {index}",
        "difficulty": "beginner"
    }
    mock_task_data = {
        "task_id": f"task-id-{index}",
        "task_title": f"Task Title {index}",
        "task_description": f"Description for task {index}.",
        "submitted_by": f"User-{index}",
        "github_repo_link": "https://github.com/test/repo"
    }
    
    bucket_integration.log_evaluation(
        mock_eval, mock_signals, mock_decision,
        mock_next_task, mock_task_data, trace_id=trace_id
    )
    return trace_id


def _read_one(ckpt_id):
    from replay_audit.atomic_persistence import load_checkpoint
    payload = load_checkpoint(ckpt_id)
    return payload["checkpoint_id"]


def run_concurrent_submissions(num_submissions=20):
    print(f"\n--- Running Concurrent Submissions (Total: {num_submissions}) ---")
    
    # Pre-clean storage
    product_storage.clear_all()
    
    # Use process pool to verify cross-process safety
    with ProcessPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(_submit_one, i) for i in range(num_submissions)]
        results = [f.result() for f in futures]

    # Verify results in main process
    product_storage._load()
    loaded_subs = product_storage.submissions
    print(f"Total Submissions stored: {len(loaded_subs)}")
    assert len(loaded_subs) == num_submissions, f"Expected {num_submissions}, got {len(loaded_subs)}"
    
    # Check that all files can be parsed and nothing is corrupted
    for sub_id in results:
        assert sub_id in loaded_subs
        assert loaded_subs[sub_id].task_title.startswith("Concurrency Submission")
    print("✅ Concurrent Submissions passed (no corruption, all saved successfully).")


def run_concurrent_approvals():
    print("\n--- Running Concurrent Approvals / OCC Validation ---")
    
    product_storage.clear_all()
    
    # Create a base submission
    sub_id = "sub-occ-test-001"
    submission = TaskSubmission(
        submission_id=sub_id,
        task_id="task-occ",
        task_title="OCC Validation Task Title",
        task_description="This task is used for checking optimistic concurrency control under heavy load.",
        submitted_by="Admin",
        submitted_at=datetime.now(),
        status=TaskStatus.SUBMITTED,
        previous_task_id=None,
        module_id="task-review-agent",
        schema_version="v1.0",
        registry_validation_status="VALID",
        review_state="PENDING_REVIEW"
    )
    product_storage.store_submission(submission)
    
    # Create the review record with version=1
    review_id = f"rev-{sub_id}"
    review = ReviewRecord(
        review_id=review_id,
        submission_id=sub_id,
        evaluation_result="PASS",
        failure_type=None,
        decision="APPROVED",
        reviewed_at=datetime.now(),
        score=90,
        readiness_percent=90,
        status="pass",
        candidate_name="Admin",
        task_title="OCC Validation Task Title",
        review_state="PENDING_REVIEW",
        version=1
    )
    product_storage.store_review(review)
    
    # Spawn 10 concurrent processes trying to approve version 1
    num_workers = 10
    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        futures = [executor.submit(_attempt_approve, (i, review_id)) for i in range(num_workers)]
        results = [f.result() for f in futures]
        
    successes = [r for r in results if r[0]]
    failures = [r for r in results if not r[0]]
    
    print(f"Concurrent Approvals: {len(successes)} succeeded, {len(failures)} failed")
    # Verify OCC: exactly 1 must succeed, others must fail due to version mismatch
    assert len(successes) == 1, f"OCC broken: expected 1 success, got {len(successes)}"
    assert len(failures) == num_workers - 1
    
    # Reload and double-check version and state
    product_storage._load()
    final_rev = product_storage.get_review(review_id)
    assert final_rev.review_state == "APPROVED"
    assert final_rev.version == 2
    print("✅ OCC validation passed (no duplicate approvals, version control works).")


def run_concurrent_bucket_writes(num_writes=30):
    print(f"\n--- Running Concurrent Bucket Writes (Total: {num_writes}) ---")
    
    # Ensure logs path exists and is clean
    log_dir = "storage/bucket_logs"
    index_file = os.path.join(log_dir, "evaluation_index.jsonl")
    if os.path.exists(index_file):
        os.remove(index_file)
    open(index_file, "w").close()

    # Spawn concurrent writes
    with ProcessPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(_log_one, i) for i in range(num_writes)]
        results = [f.result() for f in futures]

    # Verify JSONL lines are intact and parse correctly
    assert os.path.exists(index_file)
    lines_read = 0
    with open(index_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            lines_read += 1
            # Check if this line is valid JSON
            try:
                data = json.loads(line)
                assert "trace_id" in data
                assert data["trace_id"].startswith("trace-bucket-")
            except json.JSONDecodeError as e:
                raise AssertionError(f"Corrupt JSONL line detected: {line} | Error: {e}")
                
    print(f"Total valid JSONL lines in index: {lines_read}")
    assert lines_read == num_writes, f"Expected {num_writes} lines, found {lines_read}"
    print("✅ Concurrent bucket writes passed (all appends succeeded, JSONL is valid).")


def run_concurrent_replay_reads(num_reads=30):
    print(f"\n--- Running Concurrent Replay Reads (Total: {num_reads}) ---")
    
    # Pre-write some checkpoints
    trace_id = f"trace-replay-read-{uuid.uuid4().hex[:6]}"
    checkpoint_ids = []
    # Clear directory first to avoid reading mismatched pre-existing files
    ckpt_dir = "storage/checkpoints"
    if os.path.exists(ckpt_dir):
        for f in os.listdir(ckpt_dir):
            try:
                os.remove(os.path.join(ckpt_dir, f))
            except Exception:
                pass
    os.makedirs(ckpt_dir, exist_ok=True)
    
    for i in range(5):
        ckpt_id = write_replay_checkpoint(trace_id, {
            "event_id": f"evt-read-test-{i}",
            "action": "approve",
            "submission_id": f"sub-read-{i}",
            "operator_id": "op-reader"
        })
        checkpoint_ids.append(ckpt_id)
        
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(_read_one, checkpoint_ids[i % len(checkpoint_ids)]) for i in range(num_reads)]
        results = [f.result() for f in futures]
        
    print(f"Total read operations completed successfully: {len(results)}")
    assert len(results) == num_reads
    print("✅ Concurrent replay reads passed (checkpoints loaded and validated successfully).")


def run_all_concurrency_tests():
    print("==================================================")
    print("🏁 RUNNING CONCURRENCY TEST SUITE")
    print("==================================================")
    try:
        run_concurrent_submissions()
        run_concurrent_approvals()
        run_concurrent_bucket_writes()
        run_concurrent_replay_reads()
        print("\n==================================================")
        print("🎉 ALL CONCURRENCY TESTS PASSED!")
        print("==================================================")
        return True
    except Exception as e:
        import traceback
        print("\n❌ CONCURRENCY TEST FAILURE:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_all_concurrency_tests()
    sys.exit(0 if success else 1)
