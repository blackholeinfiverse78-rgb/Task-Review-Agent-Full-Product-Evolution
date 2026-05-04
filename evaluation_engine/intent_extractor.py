"""
Intent Extractor - Step 1 of Deterministic Evaluation
Extracts core objectives and expected features from task metadata
"""
import re
from typing import Dict, Any

class IntentExtractor:
    def __init__(self):
        # Technical keywords to identify expected features/modules
        self.feature_keywords = {
            'api', 'endpoint', 'route', 'controller', 'service', 'database', 'model',
            'auth', 'login', 'security', 'frontend', 'dashboard',
            'review', 'evaluation', 'scoring', 'orchestrator', 'pipeline', 'deployment',
            'docker', 'kubernetes', 'documentation'
        }
        
    def extract(self, title: str, description: str, pdf_text: str = "") -> Dict[str, Any]:
        """
        Extract structured intent and requirements from all inputs.
        """
        # 1. Objective Extraction (Cleaned title or first sentence)
        objective = title.strip()
        
        # 2. Expected Features Extraction
        # Combine all text inputs for comprehensive requirement detection
        combined_text = (title + " " + description + " " + pdf_text).lower()
        found_features = set()
        for keyword in self.feature_keywords:
            if re.search(r'\b' + re.escape(keyword) + r'\b', combined_text):
                found_features.add(keyword)
        
        # 3. Expected Tech Stack Detection
        tech_keywords = {
            'python', 'javascript', 'typescript', 'fastapi', 'flask', 'django',
            'react', 'vue', 'angular', 'node', 'express', 'postgresql', 'sql',
            'mongodb', 'nosql', 'docker', 'kubernetes', 'aws', 'azure', 'gcp', 'java', 'go', 'rust'
        }
        expected_stack = [tech for tech in tech_keywords if re.search(r'\b' + re.escape(tech) + r'\b', combined_text)]

        # 4. Expected Architecture Detection
        arch_patterns = {
            'mvc': r'\bmvc\b|\bmodel-view-controller\b',
            'microservices': r'\bmicroservice\b|\bmicroservices\b',
            'layered': r'\blayered\b|\btiered\b|\bseparation\b',
            'clean': r'\bclean architecture\b|\bhexagonal\b'
        }
        expected_arch = "Standard"
        for arch, pattern in arch_patterns.items():
            if re.search(pattern, combined_text):
                expected_arch = arch
                break

        # 5. Expected Modules Detection
        modules = []
        module_patterns = [
            r'(\w+)\s+module',
            r'(\w+)\s+system',
            r'(\w+)\s+service',
            r'(\w+)\s+layer',
            r'(\w+)\s+engine'
        ]
        for pattern in module_patterns:
            matches = re.findall(pattern, combined_text)
            for match in matches:
                if len(match) > 3:
                    modules.append(match)
        
        # 6. Expected Complexity Estimation
        words = combined_text.split()
        complex_keywords = {'microservice', 'distributed', 'orchestration', 'asynchronous', 'concurrency', 'optimization'}
        complex_count = sum(1 for w in words if w in complex_keywords)
        
        if len(words) > 1000 or complex_count > 3:
            complexity = "high"
        elif len(words) > 300 or complex_count > 0:
            complexity = "medium"
        else:
            complexity = "low"
            
        return {
            "task_objective": objective,
            "expected_features": sorted(list(found_features)),
            "expected_modules": sorted(list(set(modules))),
            "expected_tech_stack": sorted(list(set(expected_stack))),
            "expected_architecture": expected_arch,
            "expected_complexity": complexity
        }
