import json

tasks_data = [
    {
        "task_id": "T-GOV-001", "product": "Niyantran", "layer": "Governance", "subsystem": "Task Review Engine", "capability": "Submission Evaluation",
        "prerequisites": [], "next_tasks": ["T-GOV-002"], "failure_tasks": ["T-GOV-F01"], "completion_signals": ["Evaluation registered"], "dharma": "Validate fairly."
    },
    {
        "task_id": "T-GOV-002", "product": "Niyantran", "layer": "Governance", "subsystem": "Task Review Engine", "capability": "Task Modification",
        "prerequisites": ["T-GOV-001"], "next_tasks": ["T-GOV-003"], "failure_tasks": ["T-GOV-F02"], "completion_signals": ["Task successfully modified"], "dharma": "Adapt dynamically."
    },
    {
        "task_id": "T-GOV-003", "product": "Niyantran", "layer": "Governance", "subsystem": "Task Review Engine", "capability": "Task Enforcement",
        "prerequisites": ["T-GOV-002"], "next_tasks": ["T-GOV-004"], "failure_tasks": ["T-GOV-F03"], "completion_signals": ["Enforcement applied"], "dharma": "Never bypass execution."
    },
    {
        "task_id": "T-GOV-004", "product": "Niyantran", "layer": "Governance", "subsystem": "Access Control", "capability": "RBAC Management",
        "prerequisites": ["T-GOV-003"], "next_tasks": ["T-COR-001"], "failure_tasks": ["T-GOV-F04"], "completion_signals": ["RBAC rules written"], "dharma": "Least privilege."
    },
    {
        "task_id": "T-COR-001", "product": "Niyantran", "layer": "Core", "subsystem": "Database", "capability": "Relational Storage",
        "prerequisites": ["T-GOV-004"], "next_tasks": ["T-COR-002"], "failure_tasks": ["T-COR-F01"], "completion_signals": ["Schema deployed"], "dharma": "Data resilience."
    },
    {
        "task_id": "T-COR-002", "product": "Niyantran", "layer": "Core", "subsystem": "Database", "capability": "Vector Search",
        "prerequisites": ["T-COR-001"], "next_tasks": ["T-COR-003"], "failure_tasks": ["T-COR-F02"], "completion_signals": ["Indexes built"], "dharma": "Semantic alignment."
    },
    {
        "task_id": "T-COR-003", "product": "Niyantran", "layer": "Core", "subsystem": "Authentication", "capability": "MFA Verification",
        "prerequisites": ["T-COR-002"], "next_tasks": ["T-API-001"], "failure_tasks": ["T-COR-F03"], "completion_signals": ["Challenges generated"], "dharma": "Secure access."
    },
    {
        "task_id": "T-API-001", "product": "Niyantran", "layer": "API", "subsystem": "External Gateway", "capability": "Rate Limiting",
        "prerequisites": ["T-COR-003"], "next_tasks": ["T-FRN-001"], "failure_tasks": ["T-API-F01"], "completion_signals": ["Limits applied"], "dharma": "System stability."
    },
    {
        "task_id": "T-FRN-001", "product": "Niyantran", "layer": "Frontend", "subsystem": "Dashboard", "capability": "Real-time Metrics",
        "prerequisites": ["T-API-001"], "next_tasks": ["T-TST-001"], "failure_tasks": ["T-FRN-F01"], "completion_signals": ["Sockets connected"], "dharma": "Clear visibility."
    },
    {
        "task_id": "T-TST-001", "product": "Niyantran", "layer": "Testing", "subsystem": "QA Automation", "capability": "End-to-End Tests",
        "prerequisites": ["T-FRN-001"], "next_tasks": ["T-GOV-001"], "failure_tasks": ["T-TST-F01"], "completion_signals": ["Passed all checks"], "dharma": "Trust."
    },
    # Failure tasks
    {
        "task_id": "T-GOV-F01", "product": "Niyantran", "layer": "Governance", "subsystem": "Task Review Engine", "capability": "Submission Evaluation",
        "prerequisites": [], "next_tasks": ["T-GOV-001"], "failure_tasks": ["T-GOV-F00"], "completion_signals": ["Issue isolated"], "dharma": "Diagnose evaluation issues."
    },
    {
        "task_id": "T-GOV-F02", "product": "Niyantran", "layer": "Governance", "subsystem": "Task Review Engine", "capability": "Task Modification",
        "prerequisites": [], "next_tasks": ["T-GOV-002"], "failure_tasks": ["T-GOV-F00"], "completion_signals": ["Modification rules revised"], "dharma": "Fix modification flow."
    },
    {
        "task_id": "T-GOV-F03", "product": "Niyantran", "layer": "Governance", "subsystem": "Task Review Engine", "capability": "Task Enforcement",
        "prerequisites": [], "next_tasks": ["T-GOV-003"], "failure_tasks": ["T-GOV-F00"], "completion_signals": ["Enforcement rules corrected"], "dharma": "Restore execution layer."
    },
    {
        "task_id": "T-GOV-F04", "product": "Niyantran", "layer": "Governance", "subsystem": "Access Control", "capability": "RBAC Management",
        "prerequisites": [], "next_tasks": ["T-GOV-004"], "failure_tasks": ["T-GOV-F00"], "completion_signals": ["Policy re-evaluated"], "dharma": "Fix RBAC issues."
    },
    {
        "task_id": "T-COR-F01", "product": "Niyantran", "layer": "Core", "subsystem": "Database", "capability": "Relational Storage",
        "prerequisites": [], "next_tasks": ["T-COR-001"], "failure_tasks": ["T-GOV-F00"], "completion_signals": ["Schema fixed"], "dharma": "Fix Relational DB."
    },
    {
        "task_id": "T-COR-F02", "product": "Niyantran", "layer": "Core", "subsystem": "Database", "capability": "Vector Search",
        "prerequisites": [], "next_tasks": ["T-COR-002"], "failure_tasks": ["T-GOV-F00"], "completion_signals": ["Index updated"], "dharma": "Fix Vector setup."
    },
    {
        "task_id": "T-COR-F03", "product": "Niyantran", "layer": "Core", "subsystem": "Authentication", "capability": "MFA Verification",
        "prerequisites": [], "next_tasks": ["T-COR-003"], "failure_tasks": ["T-GOV-F00"], "completion_signals": ["MFA logic corrected"], "dharma": "Fix Authentication."
    },
    {
        "task_id": "T-API-F01", "product": "Niyantran", "layer": "API", "subsystem": "External Gateway", "capability": "Rate Limiting",
        "prerequisites": [], "next_tasks": ["T-API-001"], "failure_tasks": ["T-GOV-F00"], "completion_signals": ["Limits calibrated"], "dharma": "Fix API load management."
    },
    {
        "task_id": "T-FRN-F01", "product": "Niyantran", "layer": "Frontend", "subsystem": "Dashboard", "capability": "Real-time Metrics",
        "prerequisites": [], "next_tasks": ["T-FRN-001"], "failure_tasks": ["T-GOV-F00"], "completion_signals": ["Dashboard resolved"], "dharma": "Fix metrics display."
    },
    {
        "task_id": "T-TST-F01", "product": "Niyantran", "layer": "Testing", "subsystem": "QA Automation", "capability": "End-to-End Tests",
        "prerequisites": [], "next_tasks": ["T-TST-001"], "failure_tasks": ["T-GOV-F00"], "completion_signals": ["Test suite stabilized"], "dharma": "Fix testing suite."
    },
    {
        "task_id": "T-GOV-F00", "product": "Niyantran", "layer": "Governance", "subsystem": "Task Review Engine", "capability": "Submission Evaluation",
        "prerequisites": [], "next_tasks": ["T-GOV-F01"], "failure_tasks": ["T-GOV-F00"], "completion_signals": ["Root cause analyzed"], "dharma": "Deep dive into catastrophic failure."
    }
]

with open('c:\\Live Task Review Agent - 2\\db\\niyantran_tasks.json', 'w') as f:
    json.dump(tasks_data, f, indent=4)

print("Tasks generated")
