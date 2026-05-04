import json
from task_selector.task_selector import task_selector

def run_tests():
    results = []

    # Scenario 1: Same input -> same task_id
    run1 = task_selector.select(
        score_10=8.0, 
        decision="APPROVED",
        task_title="Build Authentication System",
        task_description="Implement JWT based authentication",
        current_task_id="NT-COR-B-001",
        current_difficulty="beginner"
    )
    run2 = task_selector.select(
        score_10=8.0, 
        decision="APPROVED",
        task_title="Build Authentication System",
        task_description="Implement JWT based authentication",
        current_task_id="NT-COR-B-001",
        current_difficulty="beginner"
    )
    results.append({
        "scenario": "1. Same Input -> Same Task ID",
        "input_1": "NT-COR-B-001, Pass (8.0)",
        "output_1": run1["task_id"],
        "input_2": "NT-COR-B-001, Pass (8.0)",
        "output_2": run2["task_id"],
        "is_deterministic": run1["task_id"] == run2["task_id"]
    })

    # Scenario 2: Fail case -> correct failure branch
    # From DB, NT-COR-B-001 fail should lead to NT-COR-B-002
    fail_run = task_selector.select(
        score_10=4.0, 
        decision="REJECTED",
        task_title="Basic API",
        task_description="Building a REST API",
        current_task_id="NT-COR-B-001",
        current_difficulty="beginner"
    )
    results.append({
        "scenario": "2. Fail Case -> Correct Failure Branch",
        "input": "NT-COR-B-001, Fail (4.0)",
        "output": fail_run["task_id"],
        "expected": "NT-COR-B-002",
        "branch": fail_run.get("branch")
    })

    # Scenario 3: Pass case -> correct progression
    # From DB, NT-COR-B-001 pass should lead to NT-REI-B-001
    pass_run = task_selector.select(
        score_10=8.0, 
        decision="APPROVED",
        task_title="Basic API",
        task_description="Building a REST API",
        current_task_id="NT-COR-B-001",
        current_difficulty="beginner"
    )
    results.append({
        "scenario": "3. Pass Case -> Correct Progression",
        "input": "NT-COR-B-001, Pass (8.0)",
        "output": pass_run["task_id"],
        "expected": "NT-REI-B-001",
        "branch": pass_run.get("branch")
    })

    # Scenario 4: Mandala mapping determinism
    # "React dashboard visualization metrics" -> should map to insightflow
    mandala_analytics = task_selector.select(
        score_10=6.0, 
        decision="APPROVED",
        task_title="Dashboard",
        task_description="React dashboard visualization metrics",
        current_task_id=None,
        current_difficulty="intermediate"
    )
    results.append({
        "scenario": "4. Mandala Context Mapping",
        "input": "Keywords: dashboard visualization metrics",
        "mapped_product": mandala_analytics["mandala_context"]["product"],
        "expected_product": "insightflow"
    })

    # Scenario 5: Missing Task Fallback
    missing_task = task_selector.select(
        score_10=3.0, 
        decision="REJECTED",
        task_title="Unknown API",
        task_description="Building a REST API",
        current_task_id="ZZ-UNKNOWN-000",
        current_difficulty="beginner"
    )
    results.append({
        "scenario": "5. Missing Task ID Fallback Determinism",
        "input": "ZZ-UNKNOWN-000, Fail (3.0)",
        "output": missing_task["task_id"],
        "source": missing_task["source"]
    })

    with open("execution_output.json", "w") as f:
        json.dump(results, f, indent=2)

    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    run_tests()
