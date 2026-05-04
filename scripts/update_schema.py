import json
import os

db_path = os.path.join("db", "niyantran_tasks.json")

with open(db_path, "r", encoding="utf-8") as f:
    tasks = json.load(f)

for task in tasks:
    if "mandala_mapping" not in task:
        task["mandala_mapping"] = {
            "product": task.pop("product", "Unknown"),
            "layer": task.pop("layer", "Unknown"),
            "subsystem": task.pop("subsystem", "Unknown"),
            "capability": task.pop("capability", "Unknown")
        }

with open(db_path, "w", encoding="utf-8") as f:
    json.dump(tasks, f, indent=2)

print("Updated db/niyantran_tasks.json")
