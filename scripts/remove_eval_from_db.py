import json
import os

db_path = os.path.join("db", "niyantran_tasks.json")
with open(db_path, "r", encoding="utf-8") as f:
    tasks = json.load(f)

for task in tasks:
    task.pop("evaluation_inputs", None)
    task.pop("evaluation_rules", None)

with open(db_path, "w", encoding="utf-8") as f:
    json.dump(tasks, f, indent=2)

print("Removed evaluation_inputs and evaluation_rules from DB")
