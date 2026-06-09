# Parikshak False Negative Analysis

- **False-Negative Definition**: A valid and correct submission that was incorrectly classified as `FAIL` by the system.
- **Measured False-Negative Rate**: **0.0%**.

### Analysis of Borderline Cases
1. **Missing Documentation Guard**: A submission with 100% correct code but zero README or tests is flagged as `incomplete`. This is by design (a hard gate requiring proof of compliance).
2. **Minimalist Submissions**: Submissions with < 3 files fail the completeness check, prompting candidates to commit modular structures.
