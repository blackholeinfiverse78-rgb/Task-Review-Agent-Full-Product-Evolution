
import requests
import time

BASE_URL = "http://127.0.0.1:8000/api/v1/task"

valid_full = {
    "task_title": "Build a Secure Async API Gateway for User Authentication and Management",
    "task_description": "The objective is to implement a robust API gateway. Requirements include schema validation using Pydantic, security constraints for JWT, and async database connections. This task ensures production readiness by adding caching and frontend integration layers. Final success criteria: 100% test coverage and full documentation.",
    "submitted_by": "Load Tester"
}

if __name__ == "__main__":
    print("--- Testing Speed (127.0.0.1) ---")
    start = time.time()
    res_submit = requests.post(f"{BASE_URL}/submit", json=valid_full)
    tid = res_submit.json()["task_id"]
    res_review = requests.post(f"{BASE_URL}/review", json={"task_id": tid})
    duration = (time.time() - start) * 1000
    print(f"Status {res_review.status_code}, Overall Time {duration:.2f}ms")
    print(f"Engine Eval Time: {res_review.json()['meta']['evaluation_time_ms']}ms")
