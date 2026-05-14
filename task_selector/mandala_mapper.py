import json
import os
import re

class MandalaMapper:
    def __init__(self):
        self.db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'db', 'mandala.json')
        self.mandala_data = self._load_mandala()

    def _load_mandala(self):
        with open(self.db_path, 'r') as f:
            return json.load(f)

    def resolve_context(self, task_title: str, task_description: str) -> dict:
        """
        Resolve exact capability mapping from mandala using simple rule-based approach.
        No ML, just exact or substring matching.
        """
        combined_text = f"{task_title} {task_description}".lower()
        
        # Simple scoring based on capability matches
        best_match = None
        highest_score = 0
        rule_trace = []
        
        for item in self.mandala_data:
            score = 0
            # weight layer matches
            if item['layer'].lower() in combined_text:
                score += 1
                rule_trace.append(f"Matched text to layer {item['layer']}")
            # weight subsystem matches
            if item['subsystem'].lower() in combined_text:
                score += 2
                rule_trace.append(f"Matched text to subsystem {item['subsystem']}")
            # weight capability matches
            if item['capability'].lower() in combined_text:
                score += 5
                rule_trace.append(f"Matched text to capability {item['capability']}")
                
            if score > highest_score:
                highest_score = score
                best_match = item
                
        # If mapping fails (no meaningful match), HARD REJECT
        if highest_score < 5:
            # We must have at least matched the capability (score >= 5) to trust it
            # Fallback exact partial matches just in case
            for item in self.mandala_data:
                parts = item['capability'].lower().split()
                if all(part in combined_text for part in parts):
                    return {
                        "product": item["product"],
                        "layer": item["layer"],
                        "subsystem": item["subsystem"],
                        "capability": item["capability"],
                        "mapping_rules_applied": ["Exact keyword substring match fallback"]
                    }
            raise ValueError(f"HARD REJECT: Task could not be mapped to Mandala capabilities. Trace: {rule_trace}")
            
        result = dict(best_match)
        result["mapping_rules_applied"] = rule_trace
        return result

mandala_mapper = MandalaMapper()
