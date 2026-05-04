import re
import subprocess

def update_readme(path):
    with open(path, 'r', encoding='utf-8') as f:
        doc = f.read()

    # 4. Tags Section Placement
    doc = re.sub(r'\*\*Tags:\*\*.*?\n\n---\n', '', doc, flags=re.DOTALL)
    if '**Tech:**' not in doc:
        # insert right under title
        doc = re.sub(
            r'(# Parikshak — Deterministic Task Evaluation Engine\n)',
            r'\1\n**Tech:** `FastAPI` | `Rule Engine` | `Graph Routing` | `Deterministic Systems`\n\n',
            doc
        )

    # 2. Sharper Simple Flow
    doc = doc.replace(
        '[ Input ] → [ Rule Engine ] → [ Graph Traversal ] → [ Post-Processing ] → [ 7-Field Output ]',
        '[ Submission ] → [ Rule Engine (4 checks) ] → [ Task Graph ] → [ Decision Layer ] → [ 7-field Output ]'
    )

    # 3. Missing Visual Diagram (Mermaid)
    if '```mermaid' not in doc:
        mermaid_diagram = """
```mermaid
graph TD
    A[User Submission] --> B[API Layer]
    B --> C{Rule Engine<br/>4 binary checks}
    C -- PASS --> D[Task Graph]
    C -- FAIL --> E[Failure Routing]
    D --> F[Decision Layer]
    E --> F
    F --> G((7-field JSON Output))
```
"""
        doc = doc.replace('## How It Works (Simple Flow)\n```text\n[ Submission ] → [ Rule Engine (4 checks) ] → [ Task Graph ] → [ Decision Layer ] → [ 7-field Output ]\n```', 
            '## How It Works (Simple Flow)\n```text\n[ Submission ] → [ Rule Engine (4 checks) ] → [ Task Graph ] → [ Decision Layer ] → [ 7-field Output ]\n```\n' + mermaid_diagram)


    # 5. Why This Matters
    if '## Why This System Exists' not in doc:
        why_matters = """
## Why This System Exists

Most evaluation systems rely on scoring, weights, or heuristics, which introduce ambiguity and inconsistency. 

Parikshak removes this by enforcing:
- Binary rule evaluation
- Deterministic task routing
- Zero fallback ambiguity

This ensures identical inputs always produce identical outputs.
"""
        doc = doc.replace('## What This System Does (in 10 seconds)', why_matters + '\n## What This System Does (in 10 seconds)')

    with open(path, 'w', encoding='utf-8') as f:
        f.write(doc)

update_readme('README.md')
update_readme('REVIEW_PACKET.md')
print("Polished README with sharper flow, diagram, and 'Why This Matters'")

# Try to update Github about using GH CLI if it exists
try:
    subprocess.run([
        'gh', 'repo', 'edit',
        '--description', 'Deterministic rule-based task evaluation engine with strict graph routing and zero fallback logic.',
        '--add-topic', 'fastapi,rule-engine,deterministic-system,task-evaluation,graph-algorithms,backend-system'
    ], check=False)
except FileNotFoundError:
    print("GH CLI not found. User needs to manually update Github About section.")
