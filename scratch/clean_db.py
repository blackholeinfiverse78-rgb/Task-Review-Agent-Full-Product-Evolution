
import json

db_path = r"g:\Live Task Review Agent - 2\db\niyantran_tasks.json"

with open(db_path, "r", encoding="utf-8") as f:
    tasks = json.load(f)

# Ensure COMPLETED task exists
all_task_ids = {t["task_id"] for t in tasks}
if "COMPLETED" not in all_task_ids:
    tasks.append({
        "task_id": "COMPLETED",
        "product": "System",
        "layer": "Final",
        "subsystem": "Terminal",
        "capability": "Lifecycle Completion",
        "dharma": "Signal end of task lifecycle.",
        "completion_signals": ["all_tasks_done"],
        "prerequisites": [],
        "next_tasks": [],
        "failure_tasks": {
            "schema_violation": [],
            "incomplete": [],
            "incorrect_logic": [],
            "integration_fail": []
        },
        "constraints": []
    })

# Verify all next_tasks and failure_tasks exist. If not, redirect to COMPLETED.
all_task_ids = {t["task_id"] for t in tasks}
for task in tasks:
    new_next = []
    for nt in task.get("next_tasks", []):
        if nt in all_task_ids or nt in ["TERMINAL_STATE", "COMPLETED"]:
            new_next.append(nt)
        else:
            new_next.append("COMPLETED")
    task["next_tasks"] = new_next

    ft = task.get("failure_tasks", {})
    for f_type in ft:
        new_f_tasks = []
        for ft_id in ft[f_type]:
            if ft_id in all_task_ids or ft_id in ["TERMINAL_STATE", "COMPLETED"]:
                new_f_tasks.append(ft_id)
            else:
                new_f_tasks.append("COMPLETED")
        ft[f_type] = new_f_tasks

with open(db_path, "w", encoding="utf-8") as f:
    json.dump(tasks, f, indent=2)

print("PASS: DB cleaned and referential integrity enforced.")
