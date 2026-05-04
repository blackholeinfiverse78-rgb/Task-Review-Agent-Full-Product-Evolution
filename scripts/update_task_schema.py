import json

schema_path = 'task_selector/task_schema.json'
with open(schema_path, 'r', encoding='utf-8') as f:
    schema = json.load(f)

# Update to 12 fields
schema['required_fields'] = [
    "task_id", "product", "layer", "subsystem", "capability",
    "dharma", "completion_signals", "failure_type",
    "prerequisites", "next_tasks", "failure_tasks", "constraints"
]

# Ensure definitions match
new_defs = {}
for k in schema['required_fields']:
    if k in schema['field_definitions']:
        new_defs[k] = schema['field_definitions'][k]
    else:
        # Add missing
        if k == 'failure_type':
            new_defs[k] = {"type": ["string", "null"], "description": "Failure type if any"}
        elif k == 'constraints':
            new_defs[k] = {"type": "array", "items": {"type": "string"}, "description": "Task constraints"}

schema['field_definitions'] = new_defs

with open(schema_path, 'w', encoding='utf-8') as f:
    json.dump(schema, f, indent=2)
print("Updated task_schema.json to 12 fields")
