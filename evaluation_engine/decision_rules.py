"""
Decision Rules - Assignment Engine Decision Logic
Provides rule-based decision making for next task generation
"""
from typing import Dict, Any

class DecisionRules:
    """Rule-based decision logic for assignment engine"""
    
    def __init__(self):
        self.rules = {
            "pass": {
                "task_type": "advancement",
                "difficulty": "advanced",
                "focus_area": "advanced_features"
            },
            "borderline": {
                "task_type": "reinforcement", 
                "difficulty": "intermediate",
                "focus_area": "skill_reinforcement"
            },
            "fail": {
                "task_type": "correction",
                "difficulty": "beginner", 
                "focus_area": "foundational_skills"
            }
        }
    
    def decide(self, review_output: Dict[str, Any]) -> Dict[str, Any]:
        """Make decision based on review output"""
        status = review_output.get("status", "fail")
        
        base_decision = self.rules.get(status, self.rules["fail"]).copy()
        
        # Add common fields
        base_decision.update({
            "title": f"{base_decision['focus_area'].replace('_', ' ').title()} Task",
            "objective": f"Complete {base_decision['task_type']} assignment",
            "expected_deliverables": "Complete implementation"
        })
        
        return base_decision