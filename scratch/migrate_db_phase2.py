import json
import os

def migrate_db():
    db_path = 'db/niyantran_tasks.json'
    if not os.path.exists(db_path):
        print(f"Error: {db_path} not found")
        return

    with open(db_path, 'r') as f:
        tasks = json.load(f)

    print(f"Migrating {len(tasks)} tasks...")

    for task in tasks:
        # Phase 2 expansion: Canonical System Definition
        
        # 1. Evaluation Inputs (Signals required for this task)
        if 'evaluation_inputs' not in task:
            task['evaluation_inputs'] = [
                "repository_available",
                "word_count",
                "file_count",
                "readme_val",
                "delivery_ratio",
                "missing_features",
                "layer_count"
            ]
        
        # 2. Evaluation Rules (Deterministic logic for this task)
        if 'evaluation_rules' not in task:
            task['evaluation_rules'] = {
                "schema": {
                    "min_word_count": 50,
                    "require_repo": False
                },
                "completeness": {
                    "min_files": 3,
                    "require_proof": True,
                    "require_arch": True
                },
                "logic": {
                    "min_delivery_ratio": 0.6,
                    "max_missing_features": 3,
                    "min_word_count_for_effort": 80
                }
            }
        
        # 3. Failure Semantics (Structured failure context)
        if 'failure_semantics' not in task:
            task['failure_semantics'] = {
                "schema_violation": "Input schema validation failed (trace_id or description length)",
                "incomplete": "Submission missing mandatory components (code, proof, or architecture)",
                "incorrect_logic": "Implementation does not match requirements or lacks sufficient effort",
                "integration_fail": "System failure during evaluation or data persistence"
            }

    with open(db_path, 'w') as f:
        json.dump(tasks, f, indent=2)
    
    print("Migration complete.")

if __name__ == "__main__":
    migrate_db()
