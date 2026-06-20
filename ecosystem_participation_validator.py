"""
Ecosystem Participation Validator — Parikshak Phase IV
Validates layer placement, authority boundaries, ownership, dependencies, and ecosystem registrations.
Rejects systems that cannot clearly declare their ecosystem role.
"""
import os
import json
from typing import Dict, Any, List

class EcosystemParticipationValidator:
    def __init__(self, traces_dir: str = "storage/traces"):
        self.traces_dir = traces_dir

    def _read_json(self, trace_path: str, filename: str) -> Dict[str, Any]:
        filepath = os.path.join(trace_path, filename)
        if not os.path.exists(filepath):
            return {}
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def validate_placement(self, trace_path: str) -> Dict[str, Any]:
        placement = self._read_json(trace_path, "ecosystem_placement.json")
        if not placement:
            return {
                "status": "UNKNOWN",
                "errors": ["Missing ecosystem_placement.json file."]
            }
            
        errors = []
        valid_layers = ["Core", "Adapter", "Integration", "Boundary"]
        layer = placement.get("layer")
        
        if not layer:
            errors.append("Layer placement not declared.")
        elif layer not in valid_layers:
            errors.append(f"Invalid layer placement: {layer}. Must be one of {valid_layers}.")
            
        boundary = placement.get("authority_boundary")
        if not boundary:
            errors.append("Authority boundary not declared.")
            
        ownership = placement.get("ownership_declaration")
        if not ownership or not (ownership.get("owner_team") or ownership.get("owner_email")):
            errors.append("Ownership team or email not declared.")

        if errors:
            return {"status": "FAIL", "errors": errors}
        return {"status": "PASS", "details": placement}

    def _has_cycles(self, graph: Dict[str, List[str]]) -> bool:
        visited = set()
        rec_stack = set()
        
        def dfs(node):
            if node in rec_stack:
                return True
            if node in visited:
                return False
            visited.add(node)
            rec_stack.add(node)
            for neighbor in graph.get(node, []):
                if dfs(neighbor):
                    return True
            rec_stack.remove(node)
            return False
            
        for node in graph:
            if node not in visited:
                if dfs(node):
                    return True
        return False

    def validate_dependencies(self, trace_path: str) -> Dict[str, Any]:
        dep_graph = self._read_json(trace_path, "dependency_graph.json")
        if not dep_graph:
            return {
                "status": "UNKNOWN",
                "errors": ["Missing dependency_graph.json file."]
            }
            
        errors = []
        dependencies = dep_graph.get("dependencies", {})
        
        # Check cycles
        if self._has_cycles(dependencies):
            errors.append("Circular dependency path detected in dependency graph.")
            
        # Check forbidden packages
        forbidden = ["unverified_lib", "unsafe_bridge_plugin", "backdoor"]
        for pkg, deps in dependencies.items():
            if pkg in forbidden:
                errors.append(f"Forbidden package import detected: {pkg}")
            for dep in deps:
                if dep in forbidden:
                    errors.append(f"Forbidden package dependency detected: {dep}")
                    
        if errors:
            return {"status": "FAIL", "errors": errors}
        return {"status": "PASS", "details": dep_graph}

    def validate_participation(self, trace_path: str) -> Dict[str, Any]:
        consumer_reg = self._read_json(trace_path, "consumer_registration.json")
        arch_part = self._read_json(trace_path, "architectural_participation.json")
        
        if not consumer_reg or not arch_part:
            return {
                "status": "UNKNOWN",
                "errors": ["Missing consumer_registration.json or architectural_participation.json."]
            }
            
        errors = []
        if not consumer_reg.get("registered", False):
            errors.append("System is not registered as a governed participant inside consumer registration ledger.")
            
        if not consumer_reg.get("consumer_id"):
            errors.append("Missing registered consumer_id.")
            
        upstreams = arch_part.get("upstream_systems", [])
        downstreams = arch_part.get("downstream_systems", [])
        participants = arch_part.get("runtime_participants", [])
        
        if not upstreams and not downstreams:
            errors.append("Isolated system detected: Must declare upstream or downstream systems.")
            
        if not participants:
            errors.append("No active runtime participants declared in architectural participation.")

        if errors:
            return {"status": "FAIL", "errors": errors}
        return {"status": "PASS", "details": arch_part}

    def generate_participation_report(self, trace_id: str) -> Dict[str, Any]:
        trace_path = os.path.join(self.traces_dir, trace_id)
        
        report = {
            "trace_id": trace_id,
            "verdict": "REJECTED",
            "layer_placement": {"status": "UNKNOWN", "errors": []},
            "dependencies": {"status": "UNKNOWN", "errors": []},
            "ecosystem_participation": {"status": "UNKNOWN", "errors": []},
            "reasons": []
        }
        
        if not os.path.exists(trace_path) or not os.path.isdir(trace_path):
            report["reasons"].append(f"Trace folder '{trace_id}' not found on disk.")
            return report

        # Run validations
        placement = self.validate_placement(trace_path)
        deps = self.validate_dependencies(trace_path)
        part = self.validate_participation(trace_path)
        
        report["layer_placement"] = placement
        report["dependencies"] = deps
        report["ecosystem_participation"] = part
        
        # Aggregate failures
        all_passed = True
        for section in ["layer_placement", "dependencies", "ecosystem_participation"]:
            sec_report = report[section]
            if sec_report["status"] == "FAIL":
                all_passed = False
                report["reasons"].extend(sec_report.get("errors", []))
            elif sec_report["status"] == "UNKNOWN":
                all_passed = False
                report["reasons"].extend(sec_report.get("errors", []))

        if all_passed:
            report["verdict"] = "ACCEPTED"
        else:
            report["verdict"] = "REJECTED"
            
        return report

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python ecosystem_participation_validator.py <trace_id> [traces_dir]")
        sys.exit(1)
        
    trace_id = sys.argv[1]
    traces_dir = sys.argv[2] if len(sys.argv) > 2 else "storage/traces"
    
    val = EcosystemParticipationValidator(traces_dir)
    report = val.generate_participation_report(trace_id)
    print(json.dumps(report, indent=4))
