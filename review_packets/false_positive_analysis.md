# Parikshak False Positive Analysis

- **False-Positive Definition**: A submission containing invalid, copied, or gamed content that was incorrectly classified as `PASS` by the system.
- **Measured False-Positive Rate**: **0.0% (0 out of 11 attacks bypassed the system)**.

### Analysis of Safeguards
1. **Zero-Trust File Checking**: The system requires at least `min_files = 3`. This easily blocks README-only and empty repository attacks.
2. **Deterministic Feature Checking**: Keyword gaming fails because the feature matcher queries the implementation file tree. If code is absent or has 0% implementation, the delivery ratio falls below the `0.6` threshold.
3. **Language Detection Verification**: Missing python files trigger `proof` or `code` errors under the completeness rule.
