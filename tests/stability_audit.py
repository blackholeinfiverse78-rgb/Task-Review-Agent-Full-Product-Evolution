"""
Determinism and Stability Audit - Product Core v1
Comprehensive testing suite for production readiness verification
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from task_selector.review_orchestrator import ReviewOrchestrator
from evaluation_engine.review_engine import ReviewEngine
from models.schemas import Task
from models.persistent_storage import product_storage
from datetime import datetime
import time
import traceback

class StabilityAuditor:
    def __init__(self):
        self.orchestrator = ReviewOrchestrator(review_engine=ReviewEngine())
        self.test_results = {
            'stability': False,
            'determinism': False,
            'storage_integrity': False
        }
        self.logs = []
    
    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        log_entry = f"[{timestamp}] {message}"
        self.logs.append(log_entry)
        print(log_entry)
    
    def test_1_sequential_load(self):
        """TEST 1 — Sequential Load Test: 50 sequential submissions"""
        self.log("=" * 60)
        self.log("TEST 1 — SEQUENTIAL LOAD TEST (50 submissions)")
        self.log("=" * 60)
        
        product_storage.clear_all()
        crashes = 0
        state_corruptions = 0
        storage_errors = 0
        
        try:
            for i in range(50):
                try:
                    # Create unique task
                    task = Task(
                        task_id=f"load-test-{i:03d}",
                        task_title=f"Load Test Task {i+1:02d} - Sequential Processing",
                        task_description=f"""
                        Objective: Test system stability under sequential load (iteration {i+1}/50)
                        Requirement: Process task without crashes or state corruption
                        Technical Details: FastAPI, PostgreSQL, Redis integration
                        Load Test Parameters: Sequential submission #{i+1}
                        """,
                        submitted_by=f"LoadTester{i+1:02d}",
                        timestamp=datetime.now()
                    )
                    
                    # Process submission
                    result = self.orchestrator.process_submission(task)
                    
                    # Verify result structure
                    required_keys = ['submission_id', 'review_id', 'next_task_id', 'review', 'next_task']
                    for key in required_keys:
                        if key not in result:
                            state_corruptions += 1
                            self.log(f"  ❌ Missing key '{key}' in result {i+1}")
                    
                    # Verify storage
                    submission = product_storage.get_submission(result['submission_id'])
                    review = product_storage.get_review(result['review_id'])
                    next_task = product_storage.get_next_task(result['next_task_id'])
                    
                    if not submission or not review or not next_task:
                        storage_errors += 1
                        self.log(f"  ❌ Storage error in iteration {i+1}")
                    
                    if (i + 1) % 10 == 0:
                        self.log(f"  ✓ Completed {i+1}/50 submissions")
                        
                except Exception as e:
                    crashes += 1
                    self.log(f"  ❌ CRASH in iteration {i+1}: {str(e)}")
            
            # Final verification
            total_submissions = len(product_storage.submissions)
            total_reviews = len(product_storage.reviews)
            total_next_tasks = len(product_storage.next_tasks)
            
            self.log(f"\n[LOAD TEST RESULTS]")
            self.log(f"  Submissions Processed: {total_submissions}/50")
            self.log(f"  Reviews Created: {total_reviews}/50")
            self.log(f"  Next Tasks Assigned: {total_next_tasks}/50")
            self.log(f"  Crashes: {crashes}")
            self.log(f"  State Corruptions: {state_corruptions}")
            self.log(f"  Storage Errors: {storage_errors}")
            
            # Pass criteria: No crashes, complete storage, minimal errors
            if crashes == 0 and total_submissions == 50 and storage_errors == 0:
                self.test_results['stability'] = True
                self.log(f"  ✅ STABILITY TEST: PASS")
            else:
                self.log(f"  ❌ STABILITY TEST: FAIL")
                
        except Exception as e:
            self.log(f"  ❌ FATAL ERROR in load test: {str(e)}")
            self.log(f"  Traceback: {traceback.format_exc()}")
    
    def test_2_determinism(self):
        """TEST 2 — Determinism Test: Identical submissions"""
        self.log("\n" + "=" * 60)
        self.log("TEST 2 — DETERMINISM TEST (5 identical submissions)")
        self.log("=" * 60)
        
        product_storage.clear_all()
        
        # Fixed task for determinism testing
        base_task = Task(
            task_id="determinism-test-base",
            task_title="Determinism Verification Task with Specific Technical Requirements",
            task_description="""
            Objective: Verify absolute determinism in review scoring and task assignment
            Requirement: Identical input must produce identical output every time
            Constraint: Zero variance allowed in scores, status, or next task assignment
            
            Technical Stack:
            - FastAPI framework with async processing
            - PostgreSQL database with connection pooling
            - Redis caching layer for performance
            - Docker containerization for deployment
            - JWT authentication with refresh tokens
            
            Implementation Details:
            1. API endpoint design and validation
            2. Database schema optimization
            3. Caching strategy implementation
            4. Security layer configuration
            5. Testing and documentation
            """,
            submitted_by="DeterminismTester",
            timestamp=datetime(2026, 2, 5, 14, 30, 0)  # Fixed timestamp
        )
        
        results = []
        
        try:
            for i in range(5):
                product_storage.clear_all()  # Fresh state for each test
                
                result = self.orchestrator.process_submission(base_task)
                results.append({
                    'iteration': i + 1,
                    'score': result['review']['score'],
                    'status': result['review']['status'],
                    'readiness': result['review']['readiness_percent'],
                    'next_task_type': result['next_task']['task_type'],
                    'next_task_title': result['next_task']['title'],
                    'next_task_difficulty': result['next_task']['difficulty']
                })
                
                self.log(f"  Iteration {i+1}: Score={result['review']['score']}, "
                        f"Status={result['review']['status']}, "
                        f"NextTask={result['next_task']['task_type']}")
            
            # Verify determinism
            first_result = results[0]
            determinism_violations = 0
            
            for i, result in enumerate(results[1:], 2):
                if result['score'] != first_result['score']:
                    determinism_violations += 1
                    self.log(f"  ❌ Score variance: Iteration {i} = {result['score']} vs {first_result['score']}")
                
                if result['status'] != first_result['status']:
                    determinism_violations += 1
                    self.log(f"  ❌ Status variance: Iteration {i} = {result['status']} vs {first_result['status']}")
                
                if result['next_task_type'] != first_result['next_task_type']:
                    determinism_violations += 1
                    self.log(f"  ❌ Next task type variance: Iteration {i} = {result['next_task_type']} vs {first_result['next_task_type']}")
            
            self.log(f"\n[DETERMINISM RESULTS]")
            self.log(f"  Consistent Score: {first_result['score']}")
            self.log(f"  Consistent Status: {first_result['status']}")
            self.log(f"  Consistent Next Task: {first_result['next_task_type']}")
            self.log(f"  Determinism Violations: {determinism_violations}")
            
            if determinism_violations == 0:
                self.test_results['determinism'] = True
                self.log(f"  ✅ DETERMINISM TEST: PASS")
            else:
                self.log(f"  ❌ DETERMINISM TEST: FAIL")
                
        except Exception as e:
            self.log(f"  ❌ FATAL ERROR in determinism test: {str(e)}")
    
    def test_3_storage_consistency(self):
        """TEST 3 — Storage Consistency: Verify data integrity"""
        self.log("\n" + "=" * 60)
        self.log("TEST 3 — STORAGE CONSISTENCY TEST")
        self.log("=" * 60)
        
        # Use existing data from previous tests or create fresh
        if len(product_storage.submissions) == 0:
            self.log("  Creating test data for storage consistency check...")
            for i in range(10):
                task = Task(
                    task_id=f"storage-test-{i}",
                    task_title=f"Storage Test Task {i+1}",
                    task_description=f"Testing storage consistency for task {i+1}",
                    submitted_by=f"StorageTester{i+1}",
                    timestamp=datetime.now()
                )
                self.orchestrator.process_submission(task)
        
        try:
            # Get all stored data
            all_submissions = list(product_storage.submissions.values())
            all_reviews = list(product_storage.reviews.values())
            all_next_tasks = list(product_storage.next_tasks.values())
            
            self.log(f"  Total Submissions: {len(all_submissions)}")
            self.log(f"  Total Reviews: {len(all_reviews)}")
            self.log(f"  Total Next Tasks: {len(all_next_tasks)}")
            
            # Verify 1: All submissions have corresponding reviews
            missing_reviews = 0
            for submission in all_submissions:
                review = product_storage.get_review_by_submission(submission.submission_id)
                if not review:
                    missing_reviews += 1
                    self.log(f"  ❌ Missing review for submission {submission.submission_id}")
            
            # Verify 2: All submissions have corresponding next tasks
            missing_next_tasks = 0
            for submission in all_submissions:
                next_task = product_storage.get_next_task_by_submission(submission.submission_id)
                if not next_task:
                    missing_next_tasks += 1
                    self.log(f"  ❌ Missing next task for submission {submission.submission_id}")
            
            # Verify 3: Review-NextTask linking integrity
            broken_links = 0
            for next_task in all_next_tasks:
                review = product_storage.get_review(next_task.review_id)
                if not review:
                    broken_links += 1
                    self.log(f"  ❌ Broken link: Next task {next_task.next_task_id} references non-existent review {next_task.review_id}")
            
            # Verify 4: Complete lifecycle retrieval
            lifecycle_errors = 0
            for submission in all_submissions[:5]:  # Test first 5
                lifecycle = product_storage.get_lifecycle(submission.submission_id)
                if not lifecycle or not lifecycle['submission'] or not lifecycle['review'] or not lifecycle['next_task']:
                    lifecycle_errors += 1
                    self.log(f"  ❌ Incomplete lifecycle for submission {submission.submission_id}")
            
            self.log(f"\n[STORAGE CONSISTENCY RESULTS]")
            self.log(f"  Missing Reviews: {missing_reviews}")
            self.log(f"  Missing Next Tasks: {missing_next_tasks}")
            self.log(f"  Broken Links: {broken_links}")
            self.log(f"  Lifecycle Errors: {lifecycle_errors}")
            
            total_errors = missing_reviews + missing_next_tasks + broken_links + lifecycle_errors
            
            if total_errors == 0:
                self.test_results['storage_integrity'] = True
                self.log(f"  ✅ STORAGE CONSISTENCY TEST: PASS")
            else:
                self.log(f"  ❌ STORAGE CONSISTENCY TEST: FAIL ({total_errors} errors)")
                
        except Exception as e:
            self.log(f"  ❌ FATAL ERROR in storage consistency test: {str(e)}")
    
    def run_full_audit(self):
        """Run complete audit suite"""
        start_time = time.time()
        
        self.log("DETERMINISM AND STABILITY AUDIT - PRODUCT CORE v1")
        self.log(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Run all tests
        self.test_1_sequential_load()
        self.test_2_determinism()
        self.test_3_storage_consistency()
        
        # Final results
        end_time = time.time()
        duration = end_time - start_time
        
        self.log("\n" + "=" * 60)
        self.log("AUDIT RESULTS SUMMARY")
        self.log("=" * 60)
        
        stability_status = "PASS" if self.test_results['stability'] else "FAIL"
        determinism_status = "PASS" if self.test_results['determinism'] else "FAIL"
        storage_status = "PASS" if self.test_results['storage_integrity'] else "FAIL"
        
        self.log(f"Stability Status: {stability_status}")
        self.log(f"Determinism Status: {determinism_status}")
        self.log(f"Storage Integrity: {storage_status}")
        self.log(f"Total Audit Duration: {duration:.2f} seconds")
        
        overall_pass = all(self.test_results.values())
        overall_status = "PASS" if overall_pass else "FAIL"
        self.log(f"Overall Audit Status: {overall_status}")
        
        return self.test_results

if __name__ == "__main__":
    auditor = StabilityAuditor()
    results = auditor.run_full_audit()