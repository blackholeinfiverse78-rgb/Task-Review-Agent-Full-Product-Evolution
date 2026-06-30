# Parikshak Adversarial Validation Matrix

This matrix details system evaluation performance against malicious gaming submissions.

| ID | Attack Vector | Expected Result | Actual Result | Verification Status | Risk Level | FP? | FN? | Confidence |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| ADV-01 | **Template Repositories**: Boilerplate template files present but 0% delivery of actual features. | `FAIL (incorrect_logic)` | `FAIL (incorrect_logic)` | **PASS** | `LOW` | No | No | 1.00 |
| ADV-02 | **Wrong-Language Repositories**: JS code submitted for a task explicitly requiring Python features. | `FAIL (incomplete)` | `FAIL (incomplete)` | **PASS** | `LOW` | No | No | 1.00 |
| ADV-03 | **Fake Architecture Repositories**: Claims layered architecture in description but features flat structure with single directory. | `FAIL (incorrect_logic)` | `FAIL (incorrect_logic)` | **PASS** | `LOW` | No | No | 1.00 |
| ADV-04 | **README-Only Repositories**: Repository contains only the README file, bypassing text limit, but has no source code files. | `FAIL (incomplete)` | `FAIL (incomplete)` | **PASS** | `LOW` | No | No | 1.00 |
| ADV-05 | **Copied Repositories**: Cloned repository containing generic structure but zero implementation of task specific features. | `FAIL (incorrect_logic)` | `FAIL (incorrect_logic)` | **PASS** | `LOW` | No | No | 1.00 |
| ADV-06 | **Generated AI Repositories**: Artificially high word count and fake code structures designed to pass basic matching heuristics. | `FAIL (incorrect_logic)` | `FAIL (incomplete)` | **FAIL** | `LOW` | No | No | 1.00 |
| ADV-07 | **Large Boilerplates**: Massive framework code (e.g. Django default) with no user modifications or features. | `FAIL (incorrect_logic)` | `FAIL (incorrect_logic)` | **PASS** | `LOW` | No | No | 1.00 |
| ADV-08 | **Keyword-Match False Positives**: Description contains engineering keywords but files are blank text files. | `FAIL (incomplete)` | `FAIL (incomplete)` | **PASS** | `LOW` | No | No | 1.00 |
| ADV-09 | **Correct Solutions With Missing Docs**: Clean, fully-layered correct implementation but lacks any documentation or testing files (no README/tests). | `FAIL (incomplete)` | `FAIL (incomplete)` | **PASS** | `LOW` | No | No | 1.00 |
| ADV-10 | **Empty Feature Submissions**: Submission contains valid repository URLs but zero deliverables or expected code structures. | `FAIL (incorrect_logic)` | `FAIL (incomplete)` | **FAIL** | `LOW` | No | No | 1.00 |
| ADV-11 | **Unrelated PDFs**: PDF text uploaded has engineering words but repository is missing or not provided. | `FAIL (incomplete)` | `FAIL (incomplete)` | **PASS** | `LOW` | No | No | 1.00 |

*Generated at: 2026-06-30T10:38:25.383349Z UTC*
