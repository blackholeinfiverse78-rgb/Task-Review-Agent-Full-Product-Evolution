# Parikshak Demo Finding Analysis (HackaVerse Audit)

This document presents the investigation of the recent HackaVerse demo finding where an unrelated file submission was able to receive a `PASS` outcome.

---

## 1. Observed Behavior
- **Event**: A candidate uploaded an unrelated file/document during a task review.
- **Outcome**: The evaluation engine returned a `PASS` status, and the candidate was advanced to the next task in the graph.

---

## 2. Technical Root Cause (Empty Feature Bypass)

The root cause of this failure lies in the combination of **empty feature extraction** and **default success fallbacks** in the signal matching and rule engine logic.

### Step A: Intent Extraction
In [evaluation_engine/intent_extractor.py](file:///c:/Users/black/Downloads/Live%20Task%20Review%20Agent%20-%202/Live%20Task%20Review%20Agent%20-%202/evaluation_engine/intent_extractor.py), expected features are extracted from the combined submission text (`title + description + pdf_text`) using a static set of keyword filters:
```python
combined_text = (title + " " + description + " " + pdf_text).lower()
found_features = set()
for keyword in self.feature_keywords:
    if re.search(r'\b' + re.escape(keyword) + r'\b', combined_text):
        found_features.add(keyword)
```
If the uploaded file or description contains **none** of these generic technical keywords (e.g. it is a cooking recipe, a text story, or an unrelated PDF), the resulting `expected_features` list is empty (`[]`), and `expected_count` is `0`.

### Step B: Feature Matching
In [evaluation_engine/feature_matcher.py](file:///c:/Users/black/Downloads/Live%20Task%20Review%20Agent%20-%202/Live%20Task%20Review%20Agent%20-%202/evaluation_engine/feature_matcher.py#L73), the matching ratio is computed:
```python
feature_ratio = len(implemented_features) / len(expected_features) if expected_features else 1.0
```
Because `expected_features` is empty, `feature_ratio` defaults to `1.0` (100% match).

### Step C: Rule Engine Logic check
In [evaluation_engine/rule_engine.py](file:///c:/Users/black/Downloads/Live%20Task%20Review%20Agent%20-%202/Live%20Task%20Review%20Agent%20-%202/evaluation_engine/rule_engine.py#L95), the `delivery_ratio` check defaults to `1.0` if `expected_count` is 0:
```python
delivery_ratio = evd.get("delivery_ratio", 1.0) if expected_count > 0 else 1.0
```
Since `delivery_ratio = 1.0` and `missing_features = []`, the logic check evaluates alignment:
```python
alignment = delivery_ratio >= min_ratio and len(missing) <= max_missing
```
This resolves to `1.0 >= 0.6` and `0 <= 3`, which is `True`. 

Consequently, as long as the user supplies a valid GitHub repository with at least 3 files (satisfying Check 2 Completeness), **Check 3 (Logic) will automatically pass**, regardless of whether the repository matches the task topic.

---

## 3. Ignored Validation Signals

The audit reveals that crucial validation signals calculated by `FeatureMatcher` are **completely ignored** by the rule engine:

1. **Tech Stack Match**: 
   - `FeatureMatcher.compute_match()` computes a `tech_stack_match` ratio (e.g. matching Python vs JS).
   - [evaluation_engine/rule_engine.py](file:///c:/Users/black/Downloads/Live%20Task%20Review%20Agent%20-%202/Live%20Task%20Review%20Agent%20-%202/evaluation_engine/rule_engine.py) never checks `tech_stack_match`. A candidate can submit a project in Go for a Python task, and it will pass.
2. **Architecture Match**:
   - `FeatureMatcher.compute_match()` computes an `architecture_match` score (validating layer expectations).
   - `rule_engine.py` never checks `architecture_match`. An flat folder structure passes clean architecture constraints.

---

## 4. Failure Mode Classification

This issue is characterized as:

*   **A Reasoning Issue**: The system does not understand the semantic context of files. It assumes that an empty list of requirements implies perfect implementation compliance.
*   **A Rule Issue**: The rule checks are simple binary gates and fail to enforce `tech_stack_match` and `architecture_match` thresholds.
*   **A Validation Gap**: The system checks for the *existence* of test files and README files using file name strings (`'test' in filename`), rather than verifying that the tests run or check the code.

---

## 5. Could this failure happen again?
**Yes, easily.** 
Any time a candidate submits a repository with generic files (e.g. a template repository) and uploads an unrelated text description or file that avoids the 20 pre-defined keywords, `RuleEngine` will return a `PASS` status, and the candidate will be approved.
No code adjustments are authorized in this sprint to fix this behavior.
