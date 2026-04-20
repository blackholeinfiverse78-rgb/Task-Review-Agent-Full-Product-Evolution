import json
import os

tasks_data = [
    {
        "task_id": "T-GOV-001", "product": "Niyantran", "layer": "Governance", "subsystem": "Task Review Engine", "capability": "Submission Evaluation",
        "prerequisites": [], "next_tasks": ["T-GOV-002"], "failure_tasks": ["T-GOV-F01"], 
        "completion_signals": ["Evaluation API returns 200", "DB logs evaluation score"], 
        "dharma": "Ensure accurate and unbiased evaluation of submissions."
    },
    {
        "task_id": "T-GOV-002", "product": "Niyantran", "layer": "Governance", "subsystem": "Task Review Engine", "capability": "Task Enforcement",
        "prerequisites": ["T-GOV-001"], "next_tasks": ["T-COR-001"], "failure_tasks": ["T-GOV-F02"], 
        "completion_signals": ["Graph updates properly", "Next task ID correctly recorded"], 
        "dharma": "Adapt dynamically via strict DB rules."
    },
    {
        "task_id": "T-COR-001", "product": "Niyantran", "layer": "Core", "subsystem": "Database", "capability": "Relational Storage",
        "prerequisites": ["T-GOV-002"], "next_tasks": ["T-TST-001"], "failure_tasks": ["T-COR-F01"], 
        "completion_signals": ["SQL Schema migrated without errors"], 
        "dharma": "Data resilience and strict schema enforcement."
    },
    {
        "task_id": "T-TST-001", "product": "Niyantran", "layer": "Testing", "subsystem": "QA Automation", "capability": "End-to-End Tests",
        "prerequisites": ["T-COR-001"], "next_tasks": ["T-VAA-001"], "failure_tasks": ["T-TST-F01"], 
        "completion_signals": ["pytest passes", "coverage > 80%"], 
        "dharma": "Trust but verify."
    },
    # Vaani
    {
        "task_id": "T-VAA-001", "product": "Vaani_TTS", "layer": "API", "subsystem": "Gateway", "capability": "Audio Streaming",
        "prerequisites": ["T-TST-001"], "next_tasks": ["COMPLETED"], "failure_tasks": ["T-VAA-F01"], 
        "completion_signals": ["WebSocket streams audio"], 
        "dharma": "Deliver zero-latency streams."
    },
    # Failures
    {
        "task_id": "T-GOV-F01", "product": "Niyantran", "layer": "Governance", "subsystem": "Task Review Engine", "capability": "Submission Evaluation",
        "prerequisites": [], "next_tasks": ["T-GOV-001"], "failure_tasks": ["T-SYS-F00"], 
        "completion_signals": ["Evaluation logic debugged and fixed"], 
        "dharma": "Diagnose evaluation issues systematically."
    },
    {
        "task_id": "T-GOV-F02", "product": "Niyantran", "layer": "Governance", "subsystem": "Task Review Engine", "capability": "Task Enforcement",
        "prerequisites": [], "next_tasks": ["T-GOV-002"], "failure_tasks": ["T-SYS-F00"], 
        "completion_signals": ["Enforcement loop fixed"], 
        "dharma": "Maintain execution structure."
    },
    {
        "task_id": "T-COR-F01", "product": "Niyantran", "layer": "Core", "subsystem": "Database", "capability": "Relational Storage",
        "prerequisites": [], "next_tasks": ["T-COR-001"], "failure_tasks": ["T-SYS-F00"], 
        "completion_signals": ["DB schema bug resolved"], 
        "dharma": "Fix relational structures."
    },
    {
        "task_id": "T-TST-F01", "product": "Niyantran", "layer": "Testing", "subsystem": "QA Automation", "capability": "End-to-End Tests",
        "prerequisites": [], "next_tasks": ["T-TST-001"], "failure_tasks": ["T-SYS-F00"], 
        "completion_signals": ["Flaky tests resolved"], 
        "dharma": "Ensure reliable tests."
    },
    {
        "task_id": "T-VAA-F01", "product": "Vaani_TTS", "layer": "API", "subsystem": "Gateway", "capability": "Audio Streaming",
        "prerequisites": [], "next_tasks": ["T-VAA-001"], "failure_tasks": ["T-SYS-F00"], 
        "completion_signals": ["Sockets re-connected"], 
        "dharma": "Ensure stream stability."
    },
    {
        "task_id": "T-SYS-F00", "product": "Parikshak", "layer": "Governance", "subsystem": "Task Selection", "capability": "Deterministic Routing",
        "prerequisites": [], "next_tasks": ["T-GOV-001"], "failure_tasks": ["T-SYS-F00"], 
        "completion_signals": ["Fallback resolved manually"], 
        "dharma": "Deep dive into catastrophic failure."
    }
]

os.makedirs('db', exist_ok=True)
with open('db/niyantran_tasks.json', 'w') as f:
    json.dump(tasks_data, f, indent=4)

print("Tasks generated")
