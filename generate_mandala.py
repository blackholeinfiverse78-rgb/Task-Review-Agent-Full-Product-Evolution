import json
import os

mandala_data = [
    # Niyantran
    {"product": "Niyantran", "layer": "Governance", "subsystem": "Task Review Engine", "capability": "Submission Evaluation"},
    {"product": "Niyantran", "layer": "Governance", "subsystem": "Task Review Engine", "capability": "Task Enforcement"},
    {"product": "Niyantran", "layer": "Governance", "subsystem": "Access Control", "capability": "RBAC Management"},
    {"product": "Niyantran", "layer": "Core", "subsystem": "Database", "capability": "Relational Storage"},
    {"product": "Niyantran", "layer": "Testing", "subsystem": "QA Automation", "capability": "End-to-End Tests"},
    # Vaani
    {"product": "Vaani_TTS", "layer": "Core", "subsystem": "Inference Engine", "capability": "Voice Synthesis"},
    {"product": "Vaani_TTS", "layer": "Core", "subsystem": "Inference Engine", "capability": "Model Loading"},
    {"product": "Vaani_TTS", "layer": "API", "subsystem": "Gateway", "capability": "Audio Streaming"},
    # Parikshak
    {"product": "Parikshak", "layer": "Evaluation", "subsystem": "Code Analysis", "capability": "Static Linting"},
    {"product": "Parikshak", "layer": "Evaluation", "subsystem": "Code Analysis", "capability": "Security Scanning"},
    {"product": "Parikshak", "layer": "Governance", "subsystem": "Task Selection", "capability": "Deterministic Routing"},
    # InsightFlow
    {"product": "InsightFlow", "layer": "Frontend", "subsystem": "Dashboard", "capability": "Metrics Visualization"},
    {"product": "InsightFlow", "layer": "Core", "subsystem": "Analytics Engine", "capability": "Data Aggregation"}
]

os.makedirs('db', exist_ok=True)
with open('db/mandala.json', 'w') as f:
    json.dump(mandala_data, f, indent=4)

print("Mandala generated")
