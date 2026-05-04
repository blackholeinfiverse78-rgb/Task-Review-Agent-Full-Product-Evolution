import re

def polish_docs(path):
    with open(path, 'r', encoding='utf-8') as f:
        c = f.read()

    # 1. Update the schema field count string
    c = c.replace('Every task must have all 14 fields', 'Every task must have all 12 fields')

    # 3. Add 'Non-authoritative post-processing layer' to Decision Engine
    # First, let's find the Engine File Map section
    c = c.replace('Decision Engine (narrative only)', 'Decision Engine (Non-authoritative post-processing layer)')
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(c)

polish_docs('../README.md')
polish_docs('../REVIEW_PACKET.md')
print("Polished docs")
