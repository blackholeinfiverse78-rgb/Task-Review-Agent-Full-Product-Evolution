"""
Product Core v1 - Stability Testing
Comprehensive stability verification for lifecycle API.
"""
import time
import json
from datetime import datetime
from typing import List, Dict, Any

from task_selector.review_orchestrator import ReviewOrchestrator
from evaluation_engine.review_engine import ReviewEngine
from models.schemas import Task
from models.persistent_storage import product_storage


class StabilityTester:
    """Deterministic stability testing for lifecycle system"""
    
    def __init__(self):
        self.orchestrator = ReviewOrchestrator(review_engine=ReviewEngine())
        self.results = []
        self.errors = []
    
    def test_sequential_submissions(self, count: int = 50) -> Dict[str, Any]:
        """Test sequential submissions with varying inputs"""
        print(f"\n[TEST 1] Sequential Submissions ({count} tasks)")
        print("=" * 60)
        
        start_time = time.time()
        scores = []
        execution_times = []
        
        for i in range(count):
            task = Task(
                task_id=f"seq-task-{i}",
                task_title=f"Sequential Test Task {i}",
                task_description=f"Objective: Test sequential submission {i}. Requirement: Verify stability.",
                submitted_by=f"Tester-{i % 5}",  # 5 different testers
                timestamp=datetime.now()
            )
            
            task_start = time.time()
            try:
                result = self.orchestrator.process_submission(task)
                task_time = (time.time() - task_start) * 1000
                
                scores.append(result["review"]["score"])
                execution_times.append(task_time)
                
                if (i + 1) % 10 == 0:
                    print(f"  Completed: {i + 1}/{count} tasks")
            except Exception as e:
                self.errors.append(f"Sequential test {i}: {str(e)}")
                print(f"  ERROR at task {i}: {str(e)}")
        
        total_time = (time.time() - start_time) * 1000
        
        report = {
            "test": "sequential_submissions",
            "count": count,
            "total_time_ms": round(total_time, 2),
            "avg_time_ms": round(sum(execution_times) / len(execution_times), 2),
            "min_time_ms": round(min(execution_times), 2),
            "max_time_ms": round(max(execution_times), 2),
            "score_range": f"{min(scores)}-{max(scores)}",
            "errors": len(self.errors),
            "success_rate": f"{((count - len(self.errors)) / count * 100):.1f}%"
        }
        
        print(f"\n  Total Time: {report['total_time_ms']}ms")
        print(f"  Avg Time: {report['avg_time_ms']}ms")
        print(f"  Score Range: {report['score_range']}")
        print(f"  Success Rate: {report['success_rate']}")
        
        return report
    
    def test_identical_submissions(self, count: int = 10) -> Dict[str, Any]:
        """Test identical submissions for determinism"""
        print(f"\n[TEST 2] Identical Submissions ({count} repeats)")
        print("=" * 60)
        
        # Fixed task for determinism testing
        base_task = Task(
            task_id="determinism-test",
            task_title="Determinism Verification Task",
            task_description="Objective: Verify deterministic behavior. Requirement: Same input yields same output.",
            submitted_by="QA Engineer",
            timestamp=datetime(2026, 2, 5, 12, 0, 0)  # Fixed timestamp
        )
        
        start_time = time.time()
        scores = []
        statuses = []
        task_types = []
        
        for i in range(count):
            product_storage.clear_all()  # Clear for clean test
            
            try:
                result = self.orchestrator.process_submission(base_task)
                scores.append(result["review"]["score"])
                statuses.append(result["review"]["status"])
                task_types.append(result["next_task"]["task_type"])
            except Exception as e:
                self.errors.append(f"Identical test {i}: {str(e)}")
                print(f"  ERROR at iteration {i}: {str(e)}")
        
        total_time = (time.time() - start_time) * 1000
        
        # Check for variance
        score_variance = len(set(scores))
        status_variance = len(set(statuses))
        task_type_variance = len(set(task_types))
        
        deterministic = (score_variance == 1 and status_variance == 1 and task_type_variance == 1)
        
        report = {
            "test": "identical_submissions",
            "count": count,
            "total_time_ms": round(total_time, 2),
            "score_variance": score_variance,
            "status_variance": status_variance,
            "task_type_variance": task_type_variance,
            "deterministic": deterministic,
            "score": scores[0] if scores else None,
            "status": statuses[0] if statuses else None,
            "task_type": task_types[0] if task_types else None,
            "errors": len(self.errors)
        }
        
        print(f"\n  Deterministic: {'YES' if deterministic else 'NO'}")
        print(f"  Score: {report['score']} (variance: {score_variance})")
        print(f"  Status: {report['status']} (variance: {status_variance})")
        print(f"  Task Type: {report['task_type']} (variance: {task_type_variance})")
        
        return report
    
    def test_state_verification(self) -> Dict[str, Any]:
        """Verify storage state integrity"""
        print(f"\n[TEST 3] State Verification")
        print("=" * 60)
        
        submission_count = len(product_storage.submissions)
        review_count = len(product_storage.reviews)
        next_task_count = len(product_storage.next_tasks)
        
        # Verify relationships
        orphaned_reviews = 0
        orphaned_next_tasks = 0
        
        for review_id, review in product_storage.reviews.items():
            if review.submission_id not in product_storage.submissions:
                orphaned_reviews += 1
        
        for next_task_id, next_task in product_storage.next_tasks.items():
            if next_task.previous_submission_id not in product_storage.submissions:
                orphaned_next_tasks += 1
        
        state_valid = (orphaned_reviews == 0 and orphaned_next_tasks == 0)
        
        report = {
            "test": "state_verification",
            "submission_count": submission_count,
            "review_count": review_count,
            "next_task_count": next_task_count,
            "orphaned_reviews": orphaned_reviews,
            "orphaned_next_tasks": orphaned_next_tasks,
            "state_valid": state_valid
        }
        
        print(f"\n  Submissions: {submission_count}")
        print(f"  Reviews: {review_count}")
        print(f"  Next Tasks: {next_task_count}")
        print(f"  Orphaned Reviews: {orphaned_reviews}")
        print(f"  Orphaned Next Tasks: {orphaned_next_tasks}")
        print(f"  State Valid: {'YES' if state_valid else 'NO'}")
        
        return report
    
    def run_full_suite(self) -> Dict[str, Any]:
        """Run complete stability test suite"""
        print("\n" + "=" * 60)
        print("PRODUCT CORE v1 - STABILITY TEST SUITE")
        print("=" * 60)
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        suite_start = time.time()
        
        # Clear storage for clean start
        product_storage.clear_all()
        
        # Run tests
        test1 = self.test_sequential_submissions(50)
        test2 = self.test_identical_submissions(10)
        test3 = self.test_state_verification()
        
        suite_time = (time.time() - suite_start) * 1000
        
        # Generate final report
        report = {
            "suite": "Product Core v1 Stability",
            "timestamp": datetime.now().isoformat(),
            "total_time_ms": round(suite_time, 2),
            "tests": {
                "sequential_submissions": test1,
                "identical_submissions": test2,
                "state_verification": test3
            },
            "summary": {
                "total_errors": len(self.errors),
                "deterministic": test2["deterministic"],
                "state_valid": test3["state_valid"],
                "overall_status": "PASS" if (len(self.errors) == 0 and test2["deterministic"] and test3["state_valid"]) else "FAIL"
            }
        }
        
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"  Total Time: {report['total_time_ms']}ms")
        print(f"  Total Errors: {report['summary']['total_errors']}")
        print(f"  Deterministic: {'YES' if report['summary']['deterministic'] else 'NO'}")
        print(f"  State Valid: {'YES' if report['summary']['state_valid'] else 'NO'}")
        print(f"  Overall Status: {report['summary']['overall_status']}")
        print("=" * 60)
        
        return report
    
    def save_report(self, report: Dict[str, Any], filename: str = "stability_report.json"):
        """Save stability report to file"""
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\nReport saved to: {filename}")


if __name__ == "__main__":
    tester = StabilityTester()
    report = tester.run_full_suite()
    tester.save_report(report)
