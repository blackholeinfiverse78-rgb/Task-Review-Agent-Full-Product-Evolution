
import sys
import os

# Add the workspace root to sys.path
sys.path.append("g:/Live Task Review Agent - 2")

try:
    from engine.task_graph_engine import task_graph_engine
    print("PASS: TaskGraphEngine loaded successfully")
except Exception as e:
    print(f"FAIL: TaskGraphEngine failed to load: {e}")
