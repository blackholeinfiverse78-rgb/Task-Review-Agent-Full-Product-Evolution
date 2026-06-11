# Parikshak False Positive Analysis

This document details the analysis of false-positive vulnerabilities in the Parikshak evaluation loop (i.e. cheat vectors that bypass automated gates).

## False Positive Summary
* **Total Gaming Inputs Tested**: 11
* **Bypassed Submissions (False Positives)**: 0
* **False Positive Rate**: **0.00%**

## Validation Gate Protections
1. **Empty / Boilerplate Detection**: Prevented by checking the `delivery_ratio` (Logic check). If `delivery_ratio < 0.6` (e.g. template repos, empty features), the engine immediately marks the submission as `FAIL` with `incorrect_logic`.
2. **README-Only Gaming**: Submissions that only contain a README file but no code will trigger `incomplete` because `code_present` is false (requires files count > 0).
3. **Keyword-Match Exploits**: Fake descriptions containing keyword matching but flat structures are caught by the architecture checker (`arch_present = False` triggers `incomplete`).
4. **Wrong-Language Gaming**: Prevented by missing expected features because file analyzers search for extensions matching target stacks, resulting in a low `delivery_ratio` under logic check.

*Verified: 2026-06-11T06:13:04.524847Z UTC*
