import os
import shutil
from pathlib import Path
import re

CWD = Path(r"g:\Live Task Review Agent - 2")

# Desired structure map:
# src -> dest (within CWD)
MOVES = [
    # Contracts
    ("models/schemas.py", "contracts/schemas.py"),
    ("models/review_models.py", "contracts/review_models.py"),
    ("models/next_task_model.py", "contracts/next_task_model.py"),
    ("core/interfaces/next_task_interface.py", "contracts/next_task_interface.py"),
    ("core/interfaces/review_engine_interface.py", "contracts/review_engine_interface.py"),
    
    # Governance
    ("models/governance.py", "governance_layer/governance.py"),
    
    # DB
    ("models/persistent_storage.py", "db/persistent_storage.py"),
    
    # Replay Audit
    ("engine/replay_engine.py", "replay_audit/replay_engine.py"),
    ("engine/atomic_persistence.py", "replay_audit/atomic_persistence.py"),
    
    # Observability
    ("engine/observability.py", "observability/observability.py"),
    
    # Task Selector / Evaluation Engine 
    ("engine/execution_pipeline.py", "evaluation_engine/execution_pipeline.py"),
    ("engine/task_graph_engine.py", "task_selector/task_graph_engine.py"),
    ("engine/mandala_mapper.py", "task_selector/mandala_mapper.py"),
    ("registry/task_registry.py", "task_selector/task_registry.py"),
    
    # Delete unused ones if needed, but let's just move everything out of models, engine, core, registry
]

# We also need to rewrite imports across all python files.
IMPORT_REWRITES = [
    (r"models\.schemas", r"contracts.schemas"),
    (r"models\.review_models", r"contracts.review_models"),
    (r"models\.next_task_model", r"contracts.next_task_model"),
    (r"core\.interfaces\.next_task_interface", r"contracts.next_task_interface"),
    (r"core\.interfaces\.review_engine_interface", r"contracts.review_engine_interface"),
    (r"models\.governance", r"governance_layer.governance"),
    (r"models\.persistent_storage", r"db.persistent_storage"),
    (r"engine\.replay_engine", r"replay_audit.replay_engine"),
    (r"engine\.atomic_persistence", r"replay_audit.atomic_persistence"),
    (r"engine\.observability", r"observability.observability"),
    (r"engine\.execution_pipeline", r"evaluation_evaluation_engine.execution_pipeline"),
    (r"engine\.task_graph_engine", r"task_selector.task_graph_engine"),
    (r"engine\.mandala_mapper", r"task_selector.mandala_mapper"),
    (r"registry\.task_registry", r"task_selector.task_registry"),
    (r"from contracts import", r"from contracts import"),
    (r"from evaluation_engine import", r"from evaluation_engine import"), # Broad strokes, usually not used like this
]

def ensure_dir(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)

def update_file_imports(filepath: Path):
    if not filepath.exists() or not filepath.is_file():
        return
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except UnicodeDecodeError:
        return # Skip binary or non-utf8 files
        
    original = content
    for pattern, repl in IMPORT_REWRITES:
        content = re.sub(pattern, repl, content)
        
    if original != content:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Updated imports in {filepath.relative_to(CWD)}")

def main():
    # 1. Move files
    for src_rel, dst_rel in MOVES:
        src = CWD / src_rel
        dst = CWD / dst_rel
        if src.exists():
            print(f"Moving {src_rel} to {dst_rel}")
            ensure_dir(dst)
            shutil.move(str(src), str(dst))
        else:
            print(f"Warning: {src_rel} not found.")

    # 2. Update imports in all python files
    for filepath in CWD.rglob("*.py"):
        if ".git" in str(filepath) or "__pycache__" in str(filepath) or "venv" in str(filepath):
            continue
        update_file_imports(filepath)

if __name__ == "__main__":
    main()
