"""
Trace Reconstruction Validator — Parikshak TANTRA Readiness Layer
Determines whether a reviewer can reconstruct the trace timeline using persisted artifacts.
"""
import os
import json
from typing import Dict, Any, List, Tuple

EXPECTED_FILES = [
    "evidence_bundle.json",
    "lineage_bundle.json",
    "replay_bundle.json",
    "handover_bundle.json",
    "validation_decision.json",
    "governance_record.json",
    "registration_reference.json",
    "lineage_registration.json",
    "lineage_chain.json",
    "tms_convergence_status.json"
]

CRITICAL_FILES = [
    "evidence_bundle.json",
    "lineage_bundle.json",
    "replay_bundle.json",
    "validation_decision.json",
    "tms_convergence_status.json"
]

class TraceReconstructionValidator:
    def __init__(self, traces_dir: str = "storage/traces"):
        self.traces_dir = traces_dir

    def get_trace_path(self, trace_id: str) -> str:
        return os.path.join(self.traces_dir, trace_id)

    def validate_reconstruction(self, trace_id: str) -> Dict[str, Any]:
        trace_path = self.get_trace_path(trace_id)
        
        if not os.path.exists(trace_path) or not os.path.isdir(trace_path):
            return {
                "trace_id": trace_id,
                "reconstructable": False,
                "missing_artifacts": EXPECTED_FILES,
                "confidence": 0.0,
                "error": f"Trace directory for trace_id '{trace_id}' does not exist at {trace_path}."
            }

        missing_artifacts = []
        present_artifacts = []
        
        for filename in EXPECTED_FILES:
            file_path = os.path.join(trace_path, filename)
            if not os.path.exists(file_path):
                missing_artifacts.append(filename)
            else:
                present_artifacts.append(filename)

        # Check critical files
        missing_critical = [f for f in CRITICAL_FILES if f in missing_artifacts]
        reconstructable = len(missing_critical) == 0

        # Calculate confidence score
        total_files = len(EXPECTED_FILES)
        present_count = len(present_artifacts)
        confidence = float(present_count) / float(total_files)

        # Map reconstruction path: Execution -> Evidence -> Governance -> Consumption -> Actions -> Lineage -> Replay -> Convergence -> Final Status
        reconstruction_path = {
            "Execution": "evidence_bundle.json" in present_artifacts,
            "Evidence": "evidence_bundle.json" in present_artifacts,
            "Governance": "validation_decision.json" in present_artifacts and "governance_record.json" in present_artifacts,
            "Consumption": "handover_bundle.json" in present_artifacts and "registration_reference.json" in present_artifacts,
            "Actions": "evidence_bundle.json" in present_artifacts,
            "Lineage": "lineage_bundle.json" in present_artifacts and "lineage_registration.json" in present_artifacts,
            "Replay": "replay_bundle.json" in present_artifacts,
            "Convergence": "tms_convergence_status.json" in present_artifacts and "lineage_chain.json" in present_artifacts,
            "Final Status": "validation_decision.json" in present_artifacts
        }

        # Determine overall reconstructability of the path
        path_complete = all(reconstruction_path.values())

        return {
            "trace_id": trace_id,
            "reconstructable": reconstructable,
            "missing_artifacts": missing_artifacts,
            "confidence": round(confidence, 2),
            "reconstruction_path": reconstruction_path
        }

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python trace_reconstruction_validator.py <trace_id> [traces_dir]")
        sys.exit(1)
    
    trace_id = sys.argv[1]
    traces_dir = sys.argv[2] if len(sys.argv) > 2 else "storage/traces"
    
    validator = TraceReconstructionValidator(traces_dir)
    report = validator.validate_reconstruction(trace_id)
    print(json.dumps(report, indent=4))
