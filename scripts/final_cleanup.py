import json
import re

# 1. Clean db/niyantran_tasks.json
with open('../db/niyantran_tasks.json', 'r', encoding='utf-8') as f:
    tasks = json.load(f)

for t in tasks:
    t.pop('evaluation_inputs', None)
    t.pop('evaluation_rules', None)

with open('../db/niyantran_tasks.json', 'w', encoding='utf-8') as f:
    json.dump(tasks, f, indent=2)

# 2. Fix audit_checks.py
with open('../audit_checks.py', 'r', encoding='utf-8') as f:
    audit = f.read()

audit = audit.replace("'evaluation_inputs',", "")
audit = audit.replace("'evaluation_rules',", "")

with open('../audit_checks.py', 'w', encoding='utf-8') as f:
    f.write(audit)

# 3. Clean README.md and REVIEW_PACKET.md
def remove_old_flow(path):
    with open(path, 'r', encoding='utf-8') as f:
        doc = f.read()
    
    # We will just remove lines that match 'app/services/' which might be leftover.
    # Actually wait, the user said "Your README shows: Old flow (with app/services) New flow (clean separation)".
    # Let's see if there's any text "Old flow" or similar.
    # The user said "Old flow (with app/services)" and "New flow (clean separation)".
    doc = re.sub(r'Old flow.*?New flow', 'New flow', doc, flags=re.IGNORECASE | re.DOTALL)
    
    # Alternatively, I can just use a regex to strip out any lines containing 'app/services'
    lines = doc.split('\n')
    new_lines = []
    skip = False
    for line in lines:
        if 'app/services' in line:
            continue
        if 'Old flow' in line or 'Old Flow' in line:
            skip = True
            continue
        if skip and ('New flow' in line or 'New Flow' in line):
            skip = False
            # keep the 'New Flow' line
            new_lines.append(line)
            continue
        if not skip:
            new_lines.append(line)
            
    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))

remove_old_flow('../README.md')
remove_old_flow('../REVIEW_PACKET.md')

print("All cleaned!")
