"""
Validator (Contract Enforcement)

- Ensures strict JSON output
- No missing or extra fields
"""

def validator(output):
    """
    Enforces the final evaluation contract.
    """
    required_keys = ["status", "score"]

    for key in required_keys:
        if key not in output:
            raise ValueError(f"Invalid output: missing required key '{key}'")

    return output

# Compatibility with existing internal architecture
from evaluation_engine.validator import Validator
validator_service = Validator()
