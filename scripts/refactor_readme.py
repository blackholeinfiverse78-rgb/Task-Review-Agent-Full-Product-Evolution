import re

def update_readme(path):
    with open(path, 'r', encoding='utf-8') as f:
        doc = f.read()

    # Soften TANTRA-COMPLIANT
    doc = doc.replace('**Status**: TANTRA-COMPLIANT', '**Status**: Deterministic Verified System (TANTRA-compliant internally)')
    doc = doc.replace('SYSTEM TANTRA-COMPLIANT', 'SYSTEM TANTRA-COMPLIANT (Deterministic Verified)')

    # Add About / Value Prop and Tags if not present
    if "## What This System Does" not in doc:
        intro = """
> **Parikshak** is a deterministic, rule-based engineering task evaluation engine that strictly maps submissions to next tasks without any numeric scoring, arbitrary weighting, or fallback routing.

**Tags:** `fastapi`, `rule-engine`, `deterministic-system`, `task-evaluation`, `graph-routing`

---

## What This System Does (in 10 seconds)
Parikshak takes an engineering submission, strictly evaluates it against 4 binary rules, and deterministically routes it to the exact next task using a hard-coded graph database. It guarantees that the same input will always produce the exact same 7-field output contract.

## How It Works (Simple Flow)
```text
[ Input ] → [ Rule Engine ] → [ Graph Traversal ] → [ Post-Processing ] → [ 7-Field Output ]
```
1. **Input**: A JSON or multipart submission containing repository links, files, and metadata.
2. **Rule Engine**: Evaluates 4 strict binary conditions (Schema, Completeness, Logic, Integration). First failure stops execution.
3. **Graph Traversal**: Routes the PASS/FAIL result to the exact `next_tasks` or `failure_tasks` mapped in the database.
4. **Output**: Returns a strict 7-field JSON contract. No exceptions.
"""
        # Replace the first paragraph and Architecture heading with our new intro
        doc = re.sub(r'Parikshak is a fully deterministic.*?---\n+## Architecture', intro + '\n---\n\n## Architecture', doc, flags=re.DOTALL)

    # Add Example Execution
    if "## Example Execution" not in doc:
        example = """
## Example Execution

**Input (from Niyantran/Frontend):**
```json
{
  "trace_id": "abc-123-xyz",
  "task_id": "T-GOV-001",
  "submission": {
    "repository_url": "https://github.com/org/repo",
    "files_changed": 12,
    "has_tests": true
  }
}
```

**Output (Exact 7-field contract):**
```json
{
  "trace_id": "abc-123-xyz",
  "submission_id": "sub-88192a",
  "evaluation_result": "FAIL",
  "failure_type": "incomplete",
  "selected_task_id": "T-GOV-F01",
  "selection_reason": "FAIL -> failure_tasks['incomplete'][0] = T-GOV-F01",
  "source": "task_graph"
}
```
"""
        # Insert before Output Contract
        doc = doc.replace('## Output Contract (Exact)', example + '\n---\n\n## Output Contract (Exact)')

    with open(path, 'w', encoding='utf-8') as f:
        f.write(doc)

update_readme('README.md')
update_readme('REVIEW_PACKET.md')
print("Refactored docs successfully")
