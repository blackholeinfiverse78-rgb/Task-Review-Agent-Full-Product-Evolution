import os
import glob

replacements = {
    "canonical_intelligence_engine": "assignment_engine",
    "signal_collector": "signal_engine",
    "product_orchestrator": "review_orchestrator",
    "registry_validator": "validator",
    "ProductOrchestrator": "ReviewOrchestrator",
    "SignalCollector": "SignalEngine",
    "RegistryValidator": "Validator",
    "CanonicalIntelligenceEngine": "AssignmentEngine",
    "canonical_intelligence": "assignment_engine"
}

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    new_content = content
    for old, new in replacements.items():
        new_content = new_content.replace(old, new)
        
    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Updated {filepath}")

for root, _, files in os.walk("app"):
    for file in files:
        if file.endswith(".py"):
            process_file(os.path.join(root, file))

for root, _, files in os.walk("tests"):
    for file in files:
        if file.endswith(".py"):
            process_file(os.path.join(root, file))

for root, _, files in os.walk("intelligence-integration-module-main"):
    for file in files:
        if file.endswith(".py"):
            process_file(os.path.join(root, file))

process_file("README.md")
