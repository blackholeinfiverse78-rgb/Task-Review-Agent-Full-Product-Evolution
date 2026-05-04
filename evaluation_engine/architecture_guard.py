"""
Architecture Guard - Assignment Engine Architecture Validation
Ensures valid task architecture and prevents invalid assignments
"""
from typing import Dict, Any

class ArchitectureGuard:
    """Architecture validation and correction for assignment engine"""
    
    def __init__(self):
        self.valid_task_types = ["advancement", "reinforcement", "correction"]
        self.valid_difficulties = ["beginner", "intermediate", "advanced", "foundational"]
        self.valid_focus_areas = [
            "general", "advanced_features", "skill_reinforcement", 
            "foundational_skills", "implementation", "architecture"
        ]
    
    def ensure_valid(self, task_data: Dict[str, Any], review_output: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure task data is architecturally valid"""
        validated_task = task_data.copy()
        
        # Validate task type
        if validated_task.get("task_type") not in self.valid_task_types:
            validated_task["task_type"] = "correction"
        
        # Validate difficulty
        if validated_task.get("difficulty") not in self.valid_difficulties:
            validated_task["difficulty"] = "beginner"
        
        # Validate focus area
        if validated_task.get("focus_area") not in self.valid_focus_areas:
            validated_task["focus_area"] = "general"
        
        # Ensure consistency
        if validated_task["task_type"] == "advancement" and validated_task["difficulty"] == "beginner":
            validated_task["difficulty"] = "intermediate"
        
        return validated_task