
import requests
import json

BASE_URL = "http://localhost:8000/api/v1/task"

def run_test_case(payload, label):
    print(f"\n--- Testing: {label} ---")
    try:
        res = requests.post(f"{BASE_URL}/submit", json=payload)
        print(f"Status: {res.status_code}")
        print(f"Response: {json.dumps(res.json(), indent=2)}")
    except Exception as e:
        print(f"Exception: {e}")

# 1-word input
run_test_case({
    "task_title": "Short",
    "task_description": "Small",
    "submitted_by": "X"
}, "1-word/Minimal Input")

# Markdown-heavy README paste (Long input)
large_description = "# Title\n\n" + "Requirement: This is a requirement. " * 50 + "\n\n" + "### Details\n" + "Constraint: None. " * 50
run_test_case({
    "task_title": "Markdown Heavy Task with lots of symbols and structure",
    "task_description": large_description,
    "submitted_by": "Documentation Enthusiast"
}, "Markdown Heavy/Long Input")

# Special characters
run_test_case({
    "task_title": "Title with %^&*()_+ and emoji 🚀",
    "task_description": "Objective: Test symbols like <> ? / \ | ` ~ [ ] { } ; : ' \" . , and more emoji 🔥🌊",
    "submitted_by": "Byte Master"
}, "Special Characters")
