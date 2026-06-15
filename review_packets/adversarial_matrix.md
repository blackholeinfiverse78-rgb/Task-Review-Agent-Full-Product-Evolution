# Parikshak Adversarial Validation Matrix

This matrix maps adversarial/cheat attempts against the Parikshak rule engine.

| ID | Attack Vector | Description | Target | Actual | Failure Type | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| ADV-001 | **Template Repository** | Boilerplate template files with zero task feature implementation. | `FAIL` | `FAIL` | `incorrect_logic` | ✅ BLOCKED (FAIL) |
| ADV-002 | **Wrong-Language Repository** | JavaScript code submitted for Python backend task. | `FAIL` | `FAIL` | `incomplete` | ✅ BLOCKED (FAIL) |
| ADV-003 | **Fake Architecture Repository** | Claims layered design in description but directory has flat files. | `FAIL` | `FAIL` | `incorrect_logic` | ✅ BLOCKED (FAIL) |
| ADV-004 | **Unrelated PDF** | Unrelated lorem-ipsum PDF description text without code. | `FAIL` | `FAIL` | `incomplete` | ✅ BLOCKED (FAIL) |
| ADV-005 | **Empty Feature Submission** | Repository contains only one empty README file. | `FAIL` | `FAIL` | `incomplete` | ✅ BLOCKED (FAIL) |
| ADV-006 | **Copied Repository** | Exact copy of a classmate repository (detected by identical file hashes). | `FAIL` | `FAIL` | `incorrect_logic` | ✅ BLOCKED (FAIL) |
| ADV-007 | **README-Only Repository** | Only README.md file populated with descriptive text, no code files. | `FAIL` | `FAIL` | `incomplete` | ✅ BLOCKED (FAIL) |
| ADV-008 | **AI-Generated Code (Keyword Gaming)** | Contains comments matching keywords but logic is empty/fake. | `FAIL` | `FAIL` | `incomplete` | ✅ BLOCKED (FAIL) |
| ADV-009 | **Large Framework Boilerplate** | React/NextJS boilerplate with 100+ files but no custom changes. | `FAIL` | `FAIL` | `incorrect_logic` | ✅ BLOCKED (FAIL) |
| ADV-010 | **Keyword Matching but Incorrect Logic** | Files named auth.py exists but contains only 'pass' statements. | `FAIL` | `FAIL` | `incorrect_logic` | ✅ BLOCKED (FAIL) |
| ADV-011 | **Correct Implementation with Missing Docs** | Python code is correct but contains no README or comments. | `FAIL` | `FAIL` | `incomplete` | ✅ BLOCKED (FAIL) |

---

## Metric Breakdown
- **Total Attacks**: 11
- **Blocked**: 11
- **Bypassed**: 0
- **False Positive Rate**: `0.0%`
- **False Negative Rate**: `0.0%`
