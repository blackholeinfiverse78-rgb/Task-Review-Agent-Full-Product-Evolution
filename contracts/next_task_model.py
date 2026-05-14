"""
Next Task Model - Assignment Engine Task Generation
Data model for next task assignments
"""
from typing import Dict, Any
from dataclasses import dataclass

@dataclass
class NextTask:
    """Next task assignment model"""
    title: str
    objective: str
    focus_area: str
    difficulty: str
    expected_deliverables: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "title": self.title,
            "objective": self.objective,
            "focus_area": self.focus_area,
            "difficulty": self.difficulty,
            "expected_deliverables": self.expected_deliverables
        }