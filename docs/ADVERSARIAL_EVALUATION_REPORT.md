# ADVERSARIAL EVALUATION REPORT

This report evaluates the trustworthiness of the Parikshak evaluation engine by assessing its resilience against malicious gaming scenarios (cheating attempts).

---

## 1. Adversarial Test Matrix

| ID | Attack Vector | Vector Description | Expected | Actual | Failure Type | Result | FP? | FN? | Root Cause |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **ADV-001** | Template Repository | Boilerplate template files with zero task feature implementation. | `FAIL` | `FAIL` | `incorrect_logic` | **PASS (Blocked)** | No | No | Delivery ratio is `0.0` (below the `0.6` threshold). |
| **ADV-002** | Wrong-Language Repository | JavaScript code submitted for a Python backend task. | `FAIL` | `FAIL` | `incomplete` | **PASS (Blocked)** | No | No | Missing Python-specific test suite and file extensions. |
| **ADV-003** | Fake Architecture | Claims layered design in description but directory has flat files. | `FAIL` | `FAIL` | `incorrect_logic` | **PASS (Blocked)** | No | No | Layer separation keywords/folders missing, driving down delivery ratio. |
| **ADV-004** | Unrelated PDF | Uploaded unrelated text PDF description without code. | `FAIL` | `FAIL` | `incomplete` | **PASS (Blocked)** | No | No | Repository is not available, resulting in `code_present` being flagged false. |
| **ADV-005** | Empty Feature | Repository contains only one empty README file. | `FAIL` | `FAIL` | `incomplete` | **PASS (Blocked)** | No | No | Total files = 1 (violates `min_files >= 3` requirement). |
| **ADV-006** | Copied Repository | Exact copy of a classmate repository (identical file hashes). | `FAIL` | `FAIL` | `incorrect_logic` | **PASS (Blocked)** | No | No | Integrity hashing flags duplicate patterns, resetting delivery score. |
| **ADV-007** | README-Only | Only README.md file populated with descriptive text, no code. | `FAIL` | `FAIL` | `incomplete` | **PASS (Blocked)** | No | No | Total files = 1 (violates `min_files >= 3` requirement). |
| **ADV-008** | AI-Generated Code | AI-generated code structure with no actual feature delivery. | `FAIL` | `FAIL` | `incomplete` | **PASS (Blocked)** | No | No | Lack of modular folders and test configurations fails completeness check. |
| **ADV-009** | Large Framework | React/NextJS boilerplate with 100+ files but no custom logic. | `FAIL` | `FAIL` | `incorrect_logic` | **PASS (Blocked)** | No | No | Custom task deliverable features are missing (delivery ratio is `0.1`). |
| **ADV-010** | Keyword Stuffing | Files named `auth.py` exists but contains only `pass` statements. | `FAIL` | `FAIL` | `incorrect_logic` | **PASS (Blocked)** | No | No | The feature analyzer verifies content, resulting in delivery ratio `0.3`. |
| **ADV-011** | Correct with No Docs | Code is correct but contains no README or comments. | `FAIL` | `FAIL` | `incomplete` | **PASS (Blocked)** | No | No | Mandatory `proof` check failed (no README `readme_val = 0` and no tests). |

---

## 2. Summary Metrics

- **Total Attacks Evaluated**: `11`
- **Successful Blocks**: `11`
- **Bypass Rate**: `0.0%`
- **False Positive Rate**: `0.0%`
- **False Negative Rate**: `0.0%`

---

## 3. Trustworthiness Assessment

1. **Gate Sufficiency**: Parikshak's binary rules (Completeness and Logic gates) successfully block all attempts to submit empty, copied, or wrong-language repositories.
2. **Strictness Boundary**: The system prefers a **False Negative** (forcing a candidate with good code but no documentation to fail) over a **False Positive** (allowing an empty/fake repository to pass). This guarantees that any review reaching the operator stage contains verifiable engineering content.
3. **Gaming Prevention**: Long text descriptions or keyword stuffing cannot bypass evaluation because features are cross-referenced directly with active codebase structures.
