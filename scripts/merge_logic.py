"""
Merge Logic (Hierarchical Integration)

- Enforces Assignment > Signals hierarchy
- Deterministic score merging
"""

def merge_logic(assignment, signals):
    """
    Sri Satya's Hierarchical Merge Logic
    Ensures that signals cannot override an assignment FAIL.
    """
    if assignment["status"] == "FAIL":
        return {
            "status": "FAIL",
            "score": assignment["accuracy"]
        }

    # Signals refine the score but do not change the core decision
    final_score = assignment["accuracy"] + signals.get("bonus", 0)

    return {
        "status": assignment["status"],
        "score": final_score
    }
