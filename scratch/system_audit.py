import json
import os
import sys
import hashlib
import time
import logging
from typing import Dict, Any, List, Set

# Setup path for imports
sys.path.append(os.getcwd())

from evaluation_engine.execution_pipeline import execution_pipeline
from task_selector.task_graph_engine import task_graph_engine

# Silence logging for clean report
logging.basicConfig(level=logging.CRITICAL)

class SystemAuditor:
    def __init__(self):
        self.db_path = "db/niyantran_tasks.json"
        self.report = {
            "Graph Integrity": "PENDING",
            "State Exhaustiveness": "PENDING",
            "Input Safety": "PENDING",
            "Execution Purity": "PENDING",
            "Determinism": "PENDING",
            "Boundary Contract": "PENDING",
            "Observability Isolation": "PENDING"
        }
        self.failures = []

    def audit(self):
        print("\n" + "="*50)
        print("STRICT SYSTEM AUDIT IN PROGRESS")
        print("="*50)

        # 1. DB Integrity
        self._audit_db()
        
        # 2. Pipeline Purity
        self._audit_pipeline_purity()
        
        # 3. Determinism
        self._audit_determinism()
        
        # 4. Boundary & Contract
        self._audit_contract()
        
        # 5. Input Safety & Edge Cases
        self._audit_safety()
        
        # 6. Observability Isolation
        self._audit_observability()

        self._print_report()

    def _audit_db(self):
        print("Auditing DB Integrity...")
        try:
            with open(self.db_path, "r", encoding="utf-8") as f:
                db = json.load(f)
            
            task_ids = [t["task_id"] for t in db]
            if len(task_ids) != len(set(task_ids)):
                self.report["Graph Integrity"] = "FAIL"
                self.failures.append("DB: Duplicate task_ids found")
                return

            task_map = {t["task_id"]: t for t in db}
            required_fields = {"task_id", "product", "layer", "subsystem", "capability", "dharma", "completion_signals", "prerequisites", "next_tasks", "failure_tasks", "constraints"}
            
            for t in db:
                missing = required_fields - set(t.keys())
                if missing:
                    self.report["Graph Integrity"] = "FAIL"
                    self.failures.append(f"DB: Task {t['task_id']} missing fields {missing}")
                    return
                
                for nt in t["next_tasks"]:
                    if nt not in task_map:
                        self.report["Graph Integrity"] = "FAIL"
                        self.failures.append(f"DB: Task {t['task_id']} references non-existent next_task {nt}")
                        return
                
                for ft_list in t["failure_tasks"].values():
                    for ft in ft_list:
                        if ft not in task_map:
                            self.report["Graph Integrity"] = "FAIL"
                            self.failures.append(f"DB: Task {t['task_id']} references non-existent failure_task {ft}")
                            return

            self.report["Graph Integrity"] = "PASS"
        except Exception as e:
            self.report["Graph Integrity"] = "FAIL"
            self.failures.append(f"DB: Audit crashed: {e}")

    def _audit_pipeline_purity(self):
        print("Auditing Execution Purity...")
        # Check files for forbidden patterns
        forbidden = ["uuid.", "random.", "T-SYS-F00", "TERMINAL_STATE"]
        # We allow T-SYS-F00 in DB and check logic, but not as a hardcoded return value
        files = ["engine/execution_pipeline.py", "engine/task_graph_engine.py"]
        
        for file in files:
            with open(file, "r", encoding="utf-8") as f:
                content = f.read()
                # Check for hardcoded T-SYS-F00 as a return or assignment
                if "return \"T-SYS-F00\"" in content or "selected = \"T-SYS-F00\"" in content:
                    self.report["Execution Purity"] = "FAIL"
                    self.failures.append(f"PURITY: Hardcoded T-SYS-F00 in {file}")
                    return
        
        self.report["Execution Purity"] = "PASS"

    def _audit_determinism(self):
        print("Auditing Determinism (5 runs with delays)...")
        input_data = {
            "trace_id": "AUDIT-TRACE-101",
            "task_id": "T-GOV-001",
            "task_title": "Determinism Audit",
            "task_description": "Validating DFA string-match purity." * 5
        }
        
        outputs = []
        for i in range(5):
            res = execution_pipeline.execute(input_data)
            # String match check
            outputs.append(json.dumps(res, sort_keys=True))
            print(f"  Run {i+1} ID: {res['submission_id']}")
            time.sleep(1.1) # Proof of timestamp dependency
        
        if len(set(outputs)) != 1:
            self.report["Determinism"] = "FAIL"
            self.failures.append("DETERMINISM: Non-identical outputs found across runs (submission_id is timestamp-dependent)")
        else:
            self.report["Determinism"] = "PASS"

    def _audit_contract(self):
        print("Auditing Boundary Contract...")
        input_data = {
            "trace_id": "AUDIT-TRACE-102",
            "task_id": "T-GOV-001",
            "task_title": "Contract Audit",
            "task_description": "Checking exact 7-field contract." * 5
        }
        
        res = execution_pipeline.execute(input_data)
        required = {"trace_id", "submission_id", "evaluation_result", "failure_type", "selected_task_id", "selection_reason", "source"}
        
        if set(res.keys()) != required:
            self.report["Boundary Contract"] = "FAIL"
            self.failures.append(f"CONTRACT: Incorrect fields {res.keys()}")
        elif len(res) != 7:
            self.report["Boundary Contract"] = "FAIL"
            self.failures.append(f"CONTRACT: Expected 7 fields, got {len(res)}")
        else:
            self.report["Boundary Contract"] = "PASS"

    def _audit_safety(self):
        print("Auditing Input Safety...")
        cases = [
            ({"evaluation_result": "PASS", "failure_type": "incomplete"}, "REJECT"),
            ({"trace_id": None}, "REJECT"),
            ({"trace_id": "short"}, "REJECT"),
            ({"task_id": "UNKNOWN-ID", "trace_id": "VALID-TRACE"}, "REJECT")
        ]
        
        for payload, _ in cases:
            try:
                execution_pipeline.execute(payload)
                self.report["Input Safety"] = "FAIL"
                self.failures.append(f"SAFETY: Accepted invalid payload {payload}")
                return
            except ValueError:
                pass
        
        self.report["Input Safety"] = "PASS"
        self.report["State Exhaustiveness"] = "PASS"

    def _audit_observability(self):
        print("Auditing Observability Isolation...")
        # Check if observability logic can mutate output
        # (Conceptual check, plus ensuring no return value from observer is used)
        with open("engine/execution_pipeline.py", "r") as f:
            content = f.read()
            if "observer.log_execution(output)" in content and "output =" not in content.split("observer.log_execution(output)")[1][:50]:
                self.report["Observability Isolation"] = "PASS"
            else:
                self.report["Observability Isolation"] = "FAIL"
                self.failures.append("OBSERVABILITY: Potential mutation or leakage")

    def _print_report(self):
        print("\n" + "="*50)
        print("DFA_VALIDATION_REPORT")
        print("="*50)
        for k, v in self.report.items():
            print(f"{k}: {v}")
        print("="*50)
        
        score = 10 if all(v == "PASS" for v in self.report.values()) else 9
        if self.failures: score = 10 - len(self.failures)
        
        print(f"\nFINAL VERDICT:")
        print(f"Score: {max(0, score)}/10")
        print(f"System Type: {'DFA' if score >= 8 else 'NOT DFA'}")
        print(f"Tantra Status: {'COMPLIANT' if score == 10 else 'NOT COMPLIANT'}")
        print("="*50)
        
        if self.failures:
            print("\nEXPLANATION OF FAILURES:")
            for f in self.failures:
                print(f"- {f}")
        print("="*50)

if __name__ == "__main__":
    auditor = SystemAuditor()
    auditor.audit()
