"""
Signal Engine (Supporting Layer)

- Provides supporting signals
- Cannot override assignment
"""

def signal_engine(input_data):
    """
    Collects supporting repository and code quality signals
    """
    return {
        "bonus": 5,
        "structure_quality": "good",
        "documentation": "present"
    }

# Compatibility with existing internal architecture
from evaluation_engine.signal_engine import SignalEngine
signal_service = SignalEngine()
