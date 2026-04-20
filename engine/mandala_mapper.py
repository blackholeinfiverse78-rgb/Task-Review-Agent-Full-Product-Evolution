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
        
        for item in self.mandala_data:
            score = 0
            # weight layer matches
            if item['layer'].lower() in combined_text:
                score += 1
            # weight subsystem matches
            if item['subsystem'].lower() in combined_text:
                score += 2
            # weight capability matches
            if item['capability'].lower() in combined_text:
                score += 5
                
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
                        "capability": item["capability"]
                    }
            raise ValueError("HARD REJECT: Task could not be mapped to Mandala capabilities.")
            
        return dict(best_match)

mandala_mapper = MandalaMapper()
