import os
import re

eval_services = [
    "rule_engine", "signal_engine", "domain_router", "review_packet_parser",
    "validator", "review_engine", "description_analyzer", "feature_matcher",
    "intent_extractor", "repository_analyzer", "title_analyzer", "shraddha_validation",
    "assignment_engine", "architecture_guard", "decision_rules", "pdf_analyzer"
]

task_sel_services = [
    "task_selector", "task_selection_engine", "mandala_mapper",
    "production_decision_engine", "human_in_loop", "final_convergence",
    "review_orchestrator", "niyantran_connection", "bucket_integration",
    "context_registry"
]

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    new_content = content
    
    # Absolute app imports
    new_content = new_content.replace('from api', 'from api')
    new_content = new_content.replace('import api', 'import api')
    new_content = new_content.replace('from models', 'from models')
    new_content = new_content.replace('import models', 'import models')
    new_content = new_content.replace('from registry', 'from registry')
    new_content = new_content.replace('from core', 'from core')
    new_content = new_content.replace('from main', 'from main')
    new_content = new_content.replace('from api', 'from api') # in main.py
    
    # App services imports
    for svc in eval_services:
        new_content = new_content.replace(f'app.services.{svc}', f'evaluation_engine.{svc}')
        new_content = new_content.replace(f'from .{svc}', f'from evaluation_engine.{svc}')
        new_content = new_content.replace(f'from ..services.{svc}', f'from evaluation_engine.{svc}')
        new_content = new_content.replace(f'import {svc}', f'import evaluation_engine.{svc}')
        
    for svc in task_sel_services:
        new_content = new_content.replace(f'app.services.{svc}', f'task_selector.{svc}')
        new_content = new_content.replace(f'from .{svc}', f'from task_selector.{svc}')
        new_content = new_content.replace(f'from ..services.{svc}', f'from task_selector.{svc}')
        new_content = new_content.replace(f'import {svc}', f'import task_selector.task_selector.{svc}')
        
    # Relative imports in the old services folder
    new_content = new_content.replace('from models', 'from models')
    new_content = new_content.replace('from registry', 'from registry')
    new_content = new_content.replace('from core', 'from core')
    new_content = new_content.replace('from api', 'from api')

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

