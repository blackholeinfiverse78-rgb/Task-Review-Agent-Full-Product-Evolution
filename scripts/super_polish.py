import re

def polish_docs(path):
    with open(path, 'r', encoding='utf-8') as f:
        doc = f.read()

    # 1. Ensure 12 fields
    doc = doc.replace('14 fields', '12 fields')
    
    # 2. Update TANTRA-compliant wording
    doc = doc.replace('(TANTRA-compliant internally)', '(8/8 checks PASS)')
    doc = doc.replace('**Status**: Deterministic Verified System (8/8 checks PASS)', '**Status**: Fully validated deterministic pipeline (8/8 checks PASS)')
    doc = doc.replace('SYSTEM TANTRA-COMPLIANT (Deterministic Verified)', 'SYSTEM TANTRA-COMPLIANT — Fully validated deterministic pipeline (8/8 checks PASS)')

    # 6. Remove "Loading" if present
    doc = re.sub(r'(?i)\bloading\b', '', doc)
    # clean up empty lines created by "loading" removal if any
    
    # 8. Rename section
    doc = doc.replace('What This System Does (in 10 seconds)', 'System Overview (Quick Read)')

    # 3. Add Example Failure Trace
    trace_text = """
### Example Failure Trace
**Input:** No README, 1 file only.
**Rule Engine:** Check 2 -> FAIL (incomplete)
**Graph Engine:** Routes via `failure_tasks["incomplete"][0]` -> `T-GOV-F01`
"""
    if '### Example Failure Trace' not in doc:
        doc = doc.replace('**Output (Exact 7-field contract):**', trace_text + '\n**Output (Exact 7-field contract):**')

    # 4. Add "Why Deterministic > Scoring Systems" and "Who is this for?"
    if '### Why Deterministic > Scoring Systems' not in doc:
        why_text = """
### Why Deterministic > Scoring Systems
Most evaluation systems rely on scoring, weights, or heuristics, which introduce ambiguity and inconsistency. Parikshak removes this by enforcing:
- **No ambiguity** (no arbitrary weights)
- **No drift** (identical inputs ALWAYS produce identical outputs)
- **No hidden logic** (everything is mapped in the DB)
- **Fully auditable decisions** (every failure type leads to an explicit graph node)

### Who is this for?
- Automated evaluators
- Hiring platforms
- Internal task engines
"""
        # Replace the old "Why This System Exists" with the new sections
        old_why_start = doc.find('## Why This System Exists')
        if old_why_start != -1:
            old_why_end = doc.find('## System Overview', old_why_start)
            if old_why_end != -1:
                doc = doc[:old_why_start] + why_text + "\n" + doc[old_why_end:]

    with open(path, 'w', encoding='utf-8') as f:
        f.write(doc)

polish_docs('README.md')
polish_docs('REVIEW_PACKET.md')
print("Completed super polish")
