import os
import re

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    new_content = content
    # Fix from evaluation_engine.svc import svc
    new_content = re.sub(r'from evaluation_engine\.([a-zA-Z_]+) import evaluation_engine\.\1', r'from evaluation_engine.\1 import \1', new_content)
    new_content = re.sub(r'from task_selector\.([a-zA-Z_]+) import task_selector\.\1', r'from task_selector.\1 import \1', new_content)

    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Updated {filepath}")

for root, dirs, files in os.walk("."):
    if ".git" in root or "__pycache__" in root or "venv" in root:
        continue
    for file in files:
        if file.endswith(".py"):
            process_file(os.path.join(root, file))
