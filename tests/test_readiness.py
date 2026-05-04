import unittest
from task_selector.review_orchestrator import ReviewOrchestrator

class TestReadinessClassification(unittest.TestCase):
    def test_pass_scores(self):
        """Test score >= 85 -> PASS"""
        self.assertEqual(ReviewOrchestrator.classify_readiness(85), "PASS")
        self.assertEqual(ReviewOrchestrator.classify_readiness(100), "PASS")
        self.assertEqual(ReviewOrchestrator.classify_readiness(90), "PASS")

    def test_borderline_scores(self):
        """Test score 60-84 -> BORDERLINE"""
        self.assertEqual(ReviewOrchestrator.classify_readiness(60), "BORDERLINE")
        self.assertEqual(ReviewOrchestrator.classify_readiness(84), "BORDERLINE")
        self.assertEqual(ReviewOrchestrator.classify_readiness(72), "BORDERLINE")

    def test_fail_scores(self):
        """Test score < 60 -> FAIL"""
        self.assertEqual(ReviewOrchestrator.classify_readiness(59), "FAIL")
        self.assertEqual(ReviewOrchestrator.classify_readiness(0), "FAIL")
        self.assertEqual(ReviewOrchestrator.classify_readiness(30), "FAIL")

    def test_edge_cases(self):
        """Test out of bounds scores"""
        self.assertEqual(ReviewOrchestrator.classify_readiness(-10), "FAIL")  # Should treat as 0 -> FAIL
        self.assertEqual(ReviewOrchestrator.classify_readiness(110), "PASS") # Should treat as 100 -> PASS

if __name__ == '__main__':
    unittest.main()
