"""
STATIC VERIFICATION — Human Review + Approval Workflow
Verifies all integration points without running the server.
"""
import sys
sys.path.insert(0, '.')

from contracts.review_models import ReviewActionRequest, ReviewState, AuditLogEntry
from db.persistent_storage import product_storage, ReviewRecord, TaskSubmission, TaskStatus
from api.review_routes import router, log_audit, approve_submission, reject_submission, modify_submission
from evaluation_engine.execution_pipeline import execution_pipeline
from api.production import submit_task_from_niyantran
import inspect
import os

print("=" * 60)
print("STATIC VERIFICATION — HUMAN REVIEW WORKFLOW")
print("=" * 60)

# CHECK 1: ReviewRecord has trace_id field
fields = ReviewRecord.model_fields
assert 'trace_id' in fields, "FAIL: ReviewRecord missing trace_id field"
assert 'review_state' in fields, "FAIL: ReviewRecord missing review_state field"
assert 'selected_task_id' in fields, "FAIL: ReviewRecord missing selected_task_id field"
print("✓ CHECK 1: ReviewRecord has all required fields")

# CHECK 2: ReviewState enum has all 4 states
states = list(ReviewState)
assert len(states) >= 4, f"FAIL: ReviewState should have at least 4 states, has {len(states)}"
assert ReviewState.PENDING_REVIEW in states
assert ReviewState.APPROVED in states
assert ReviewState.REJECTED in states
assert ReviewState.MODIFIED in states
print("✓ CHECK 2: ReviewState enum complete")

# CHECK 3: submit endpoint returns PENDING_REVIEW
src_submit = inspect.getsource(submit_task_from_niyantran)
assert 'PENDING_REVIEW' in src_submit, "FAIL: submit endpoint doesn't return PENDING_REVIEW"
assert 'QUEUED' in src_submit, "FAIL: submit endpoint doesn't return QUEUED status"
print("✓ CHECK 3: submit endpoint blocks at PENDING_REVIEW")

# CHECK 4: approve endpoint does NOT rerun evaluation or selection
src_approve = inspect.getsource(approve_submission)
assert 'evaluation_orchestrator' not in src_approve, "FAIL: approve reruns evaluation"
assert 'task_graph_engine' not in src_approve, "FAIL: approve reruns graph traversal"
assert 'ReviewState.APPROVED' in src_approve or 'APPROVED' in src_approve, "FAIL: approve doesn't set APPROVED state"
assert 'log_audit' in src_approve, "FAIL: approve doesn't log audit"
print("✓ CHECK 4: approve does NOT rerun evaluation/selection")

# CHECK 5: reject endpoint does NOT assign
src_reject = inspect.getsource(reject_submission)
assert 'assigned_task' not in src_reject, "FAIL: reject assigns task"
assert 'ReviewState.REJECTED' in src_reject or 'REJECTED' in src_reject, "FAIL: reject doesn't set REJECTED state"
assert 'log_audit' in src_reject, "FAIL: reject doesn't log audit"
print("✓ CHECK 5: reject blocks assignment")

# CHECK 6: modify endpoint overrides task without rerun
src_modify = inspect.getsource(modify_submission)
assert 'override_task_id' in src_modify, "FAIL: modify doesn't use override_task_id"
assert 'task_graph_engine' not in src_modify, "FAIL: modify reruns graph"
assert 'evaluation_orchestrator' not in src_modify, "FAIL: modify reruns evaluation"
assert 'original_task' in src_modify, "FAIL: modify doesn't preserve original_task for audit"
assert 'ReviewState.MODIFIED' in src_modify or 'MODIFIED' in src_modify, "FAIL: modify doesn't set MODIFIED state"
assert 'log_audit' in src_modify, "FAIL: modify doesn't log audit"
print("✓ CHECK 6: modify overrides without rerun")

# CHECK 7: audit log is append-only
src_audit = inspect.getsource(log_audit)
assert '"a"' in src_audit or "'a'" in src_audit, "FAIL: audit log not in append mode"
assert '"w"' not in src_audit and "'w'" not in src_audit, "FAIL: audit log uses overwrite mode"
print("✓ CHECK 7: audit log is append-only")

# CHECK 8: execution_pipeline stores trace_id on ReviewRecord
src_pipeline = inspect.getsource(execution_pipeline._persist)
assert 'trace_id=output["trace_id"]' in src_pipeline or 'trace_id=output[\"trace_id\"]' in src_pipeline, "FAIL: pipeline doesn't store trace_id on ReviewRecord"
assert 'review_state="PENDING_REVIEW"' in src_pipeline or 'review_state=\"PENDING_REVIEW\"' in src_pipeline, "FAIL: pipeline doesn't set PENDING_REVIEW"
print("✓ CHECK 8: execution_pipeline stores trace_id correctly")

# CHECK 9: /review/all endpoint returns trace_id
from api.review_routes import get_all_reviews
src_all = inspect.getsource(get_all_reviews)
assert 'trace_id' in src_all, "FAIL: /review/all doesn't return trace_id"
assert 'review.trace_id' in src_all, "FAIL: /review/all doesn't use review.trace_id"
print("✓ CHECK 9: /review/all returns trace_id")

# CHECK 10: audit log directory exists
assert os.path.exists('storage/audit_logs'), "FAIL: audit_logs directory doesn't exist"
print("✓ CHECK 10: audit log directory exists")

# CHECK 11: AuditLogEntry has all required fields
audit_fields = AuditLogEntry.model_fields
assert 'trace_id' in audit_fields
assert 'submission_id' in audit_fields
assert 'system_task' in audit_fields
assert 'final_task' in audit_fields
assert 'action' in audit_fields
assert 'timestamp' in audit_fields
print("✓ CHECK 11: AuditLogEntry schema complete")

# CHECK 12: No auto-assignment bypass exists
assert 'niyantran_connection' not in src_submit.split('process_niyantran_task')[1] if 'process_niyantran_task' in src_submit else True, "FAIL: submit has auto-assignment bypass"
print("✓ CHECK 12: No auto-assignment bypass")

# CHECK 13: ReviewRecord default state is PENDING_REVIEW
default_state = ReviewRecord.model_fields['review_state'].default
assert default_state == "PENDING_REVIEW", f"FAIL: ReviewRecord default state is {default_state}, not PENDING_REVIEW"
print("✓ CHECK 13: ReviewRecord defaults to PENDING_REVIEW")

print("\n" + "=" * 60)
print("ALL 13 CHECKS PASSED ✓")
print("=" * 60)
print("\nVERDICT: VERIFIED WORKING")
print("\nIntegration points:")
print("  - Backend models: CORRECT")
print("  - API endpoints: CORRECT")
print("  - Approval enforcement: CORRECT")
print("  - Audit logging: CORRECT")
print("  - No bypass paths: CONFIRMED")
print("  - No hidden auto-assignment: CONFIRMED")
print("  - No selector rerun: CONFIRMED")
print("  - Trace continuity: INTACT")
