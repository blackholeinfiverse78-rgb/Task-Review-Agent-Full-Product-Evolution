import requests
import uuid
import pytest

BASE_URL = "http://127.0.0.1:8000/api/v1/task"

def test_memory_limit():
    print("--- Testing Memory Limit (1005 submissions) ---")
    # Storage limit is 1000. 1005 should evict the first 5.
    ids = []
    for i in range(1005):
        payload = {
            "task_title": f"Task Number {i} - Persistent Title for Memory Test",
            "task_description": "Requirement: Test memory limits. Objective: Ensure LRU/FIFO eviction works.",
            "submitted_by": "Memory Tester"
        }
        try:
            res = requests.post(f"{BASE_URL}/submit", json=payload)
        except requests.exceptions.ConnectionError:
            pytest.skip("FastAPI server is not running on localhost:8000")
        ids.append(res.json()["task_id"])
        if i % 100 == 0:
            print(f"Submitted {i}...")

    # First ID should be gone (404)
    res_first = requests.post(f"{BASE_URL}/review", json={"task_id": ids[0]})
    print(f"First ID Status (Expected 404): {res_first.status_code}")

    # Last ID should be present (200)
    res_last = requests.post(f"{BASE_URL}/review", json={"task_id": ids[-1]})
    print(f"Last ID Status (Expected 200): {res_last.status_code}")

    if res_first.status_code == 404 and res_last.status_code == 200:
        print("MEMORY LIMIT TEST PASSED: Overflow evicted successfully.")
    else:
        print("MEMORY LIMIT TEST FAILED!")

if __name__ == "__main__":
    test_memory_limit()
