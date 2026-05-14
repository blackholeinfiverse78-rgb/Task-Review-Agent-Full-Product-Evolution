import json
from task_selector.niyantran_connection import niyantran_connection
from governance_layer.governance import GovernanceRequest, OperatorRole, OverrideReason
from api.review_routes import approve_submission
from db.persistent_storage import product_storage
from replay_audit.replay_engine import replay_engine
import asyncio

async def test_flow():
    print("--- 1. Submitting to Niyantran (Submission -> Eval -> Traversal -> Queue) ---")
    task_req = {
        "task_id": "T-GOV-001",
        "task_title": "Fix the sorting bug in the dashboard",
        "task_description": "The dashboard table is sorting the dates alphabetically instead of chronologically. Please fix it.",
        "submitted_by": "developer1",
        "trace_id": "trace-abcdef-001"
    }
    
    try:
        # Phase 3: Submission -> Evaluation -> Traversal
        eval_result = niyantran_connection.process_niyantran_task(task_req)
        print(f"Eval result: {json.dumps(eval_result, indent=2)}")
        
        # At this point, the task is in PENDING_REVIEW state in the DB
        submission_id = eval_result["submission_id"]
        review = product_storage.get_review_by_submission(submission_id)
        print(f"Current DB state: {review.review_state if review else 'NOT FOUND'}")
        
        print("\n--- 2. Human Approval (Governance -> Human Approval -> Assignment) ---")
        gov_req = GovernanceRequest(
            trace_id="trace-abcdef-001",
            submission_id=submission_id,
            operator_id="admin-123",
            operator_role=OperatorRole.SENIOR_REVIEW_OPERATOR,
            action="approve",
            reason_taxonomy=OverrideReason.REQUIREMENT_CORRECTION
        )
        
        approval_result = await approve_submission(gov_req)
        print(f"Approval result: {approval_result}")
        
        print("\n--- 3. Bounded Persistence Check ---")
        review_after = product_storage.get_review_by_submission(submission_id)
        print(f"State after approval: {review_after.review_state}")
        
        print("\n--- 4. Replay Reconstruction Proof ---")
        replay = replay_engine.generate_forensic_report("trace-abcdef-001")
        print(f"Replay trace:")
        print(json.dumps(replay, indent=2))
        
    except Exception as e:
        print(f"Exception during test: {e}")

if __name__ == "__main__":
    asyncio.run(test_flow())
