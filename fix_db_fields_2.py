import json

db_path = "db/niyantran_tasks.json"
with open(db_path, "r", encoding="utf-8") as f:
    tasks = json.load(f)

def clean_value(v):
    if isinstance(v, str):
        v = v.replace("score", "result").replace("Score", "Result")
        v = v.replace("scoring", "evaluating").replace("Scoring", "Evaluating")
        v = v.replace("weight", "value").replace("Weight", "Value")
        return v
    elif isinstance(v, list):
        return [clean_value(x) for x in v]
    elif isinstance(v, dict):
        return {k: clean_value(val) for k, val in v.items()}
    return v

for i, task in enumerate(tasks):
    tasks[i] = clean_value(task)

with open(db_path, "w", encoding="utf-8") as f:
    json.dump(tasks, f, indent=2)

print("Deep cleaned score/weight from DB")
