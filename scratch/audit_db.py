
import json
import os

def audit_db():
    db_path = "g:/Live Task Review Agent - 2/db/niyantran_tasks.json"
    if not os.path.exists(db_path):
        print(f"FAIL: DB not found at {db_path}")
        return

    with open(db_path, "r", encoding="utf-8") as f:
        tasks = json.load(f)

    violations = []
    
    # Check count
    if len(tasks) < 60:
        violations.append(f"Task count < 60 (found {len(tasks)})")

    required_fields = {
        "task_id", "product", "layer", "subsystem", "capability", 
        "dharma", "completion_signals", "prerequisites", 
        "next_tasks", "failure_tasks", "constraints"
    }
    
    required_failure_types = {
        "schema_violation", "incomplete", "incorrect_logic", "integration_fail"
    }

    all_task_ids = {t["task_id"] for t in tasks}
    
    for i, task in enumerate(tasks):
        t_id = task.get("task_id", f"INDEX_{i}")
        
        # Check required fields
        missing_fields = required_fields - set(task.keys())
        if missing_fields:
            violations.append(f"Task {t_id}: Missing fields {missing_fields}")
            
        # Check failure_tasks keys
        ft = task.get("failure_tasks", {})
        missing_ft = required_failure_types - set(ft.keys())
        if missing_ft:
            violations.append(f"Task {t_id}: Missing failure types {missing_ft}")
            
        # Check Mandala hierarchy (Section 4)
        if not all(task.get(f) for f in ["product", "layer", "subsystem", "capability"]):
            violations.append(f"Task {t_id}: Incomplete Mandala mapping")

        # Check referential integrity
        for nt in task.get("next_tasks", []):
            if nt not in all_task_ids:
                violations.append(f"Task {t_id}: next_task {nt} does not exist")
        
        for f_type, f_tasks in ft.items():
            for ft_id in f_tasks:
                if ft_id not in all_task_ids:
                    violations.append(f"Task {t_id}: failure_task {ft_id} for {f_type} does not exist")

    if violations:
        print("FAIL: DB Integrity Violations Found:")
        for v in violations:
            print(f" - {v}")
    else:
        print("PASS: DB Integrity Verified (Count: {}, All schema checks passed)".format(len(tasks)))

if __name__ == "__main__":
    audit_db()
