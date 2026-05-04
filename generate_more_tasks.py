import json
import os

db_path = os.path.join("db", "niyantran_tasks.json")

with open(db_path, "r", encoding="utf-8") as f:
    tasks = json.load(f)

# Ensure we have at least 65 tasks
current_count = len(tasks)
needed = 65 - current_count

template_task = tasks[0]
new_tasks = []

products = ["Niyantran", "Vaani_TTS", "Parikshak", "Shraddha"]
layers = ["Frontend", "Backend", "Database", "Security", "Infrastructure"]
subsystems = ["API", "Storage", "Auth", "Compute", "UI"]

t_index = 100
while needed > 0:
    for prod in products:
        for layer in layers:
            for subs in subsystems:
                if needed <= 0:
                    break
                task_id = f"T-GEN-{t_index}"
                t_index += 1
                new_task = {
                    "task_id": task_id,
                    "product": prod,
                    "layer": layer,
                    "subsystem": subs,
                    "capability": f"Auto {prod} {layer}",
                    "dharma": "Auto generated dharma.",
                    "evaluation_inputs": template_task["evaluation_inputs"],
                    "evaluation_rules": template_task["evaluation_rules"],
                    "completion_signals": template_task["completion_signals"],
                    "failure_type": None,
                    "prerequisites": [],
                    "next_tasks": [f"T-GEN-{t_index}"], # chain them
                    "failure_tasks": {
                        "schema_violation": ["T-SYS-F00"],
                        "incomplete": ["T-SYS-F00"],
                        "incorrect_logic": ["T-SYS-F00"],
                        "integration_fail": ["T-SYS-F00"]
                    },
                    "constraints": template_task["constraints"]
                }
                new_tasks.append(new_task)
                needed -= 1

# update the last one's next task to something existing
if new_tasks:
    new_tasks[-1]["next_tasks"] = ["T-GOV-001"]

tasks.extend(new_tasks)

with open(db_path, "w", encoding="utf-8") as f:
    json.dump(tasks, f, indent=2)

print(f"Generated {len(new_tasks)} new tasks. Total: {len(tasks)}")
