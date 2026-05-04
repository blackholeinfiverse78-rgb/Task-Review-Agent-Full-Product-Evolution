import re

def update_doc(path):
    with open(path, 'r', encoding='utf-8') as f:
        c = f.read()

    # Fix entry point
    c = c.replace('uvicorn app.main:app', 'uvicorn main:app')

    # Clarify Ownership
    ownership_text = """
### Architecture Ownership & Separation

**Evaluation Engine owns:**
- rule_engine
- assignment_engine
- signal_engine
- validator

**Task Selector owns:**
- final_convergence
- mandala_mapper

**Post-Processing Layers:**
- Decision Engine
- Human-in-Loop
- Bucket Logging
*(Note: These are strictly downstream and DO NOT affect task selection or the evaluation result. They are only post-processing layers.)*
"""
    
    # We will append the ownership text to the Architecture section or just before the DB section.
    if '### Architecture Ownership & Separation' not in c:
        if '## Architecture' in c:
            c = c.replace('## Architecture', '## Architecture\n' + ownership_text)
        elif '## Integration' in c:
            c = c.replace('## Integration', '## Architecture\n' + ownership_text + '\n## Integration')
        else:
            c += "\n" + ownership_text

    with open(path, 'w', encoding='utf-8') as f:
        f.write(c)

update_doc('README.md')
update_doc('REVIEW_PACKET.md')
print("Updated docs with Ownership and entrypoint fixes")
