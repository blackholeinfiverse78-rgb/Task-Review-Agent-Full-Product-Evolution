"""
Constitutional Readiness Engine — Parikshak TANTRA Readiness Layer
Combines reconstruction verification and deep artifact validation to classify trace readiness.
"""
import os
import json
from datetime import datetime, timezone
from typing import Dict, Any

from trace_reconstruction_validator import TraceReconstructionValidator
from artifact_validation_engine import ArtifactValidationEngine

class ConstitutionalReadinessEngine:
    def __init__(self, traces_dir: str = "storage/traces"):
        self.traces_dir = traces_dir
        self.reconstruction_validator = TraceReconstructionValidator(traces_dir)
        self.artifact_validator = ArtifactValidationEngine(traces_dir)

    def evaluate_readiness(self, trace_id: str) -> Dict[str, Any]:
        timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        
        # 1. Run reconstruction validation
        recon_report = self.reconstruction_validator.validate_reconstruction(trace_id)
        
        # 2. Run artifact validation
        val_report = self.artifact_validator.validate_artifacts(trace_id)
        
        # 3. Classify state
        verdict = "REJECTED"
        reasons = []
        
        # Determine any warnings
        has_warnings = False
        for layer_name, layer_info in val_report.get("layers", {}).items():
            if layer_info.get("warnings"):
                has_warnings = True
                reasons.extend(layer_info["warnings"])
        
        # Check if any optional files are missing (confidence < 1.0)
        if recon_report.get("confidence", 0.0) < 1.0 and recon_report.get("reconstructable", False):
            has_warnings = True
            missing_opt = [f for f in recon_report.get("missing_artifacts", [])]
            reasons.append(f"Missing optional artifacts: {missing_opt}")

        # Core classification logic
        if not recon_report.get("reconstructable", False):
            verdict = "REJECTED"
            reasons.append("Trace is not reconstructable: missing critical artifacts.")
            if recon_report.get("error"):
                reasons.append(recon_report["error"])
        elif not val_report.get("valid", False):
            verdict = "REJECTED"
            reasons.append("Integrity validation failed in one or more layers.")
            reasons.extend(val_report.get("errors", []))
        elif has_warnings:
            verdict = "NEEDS_REVIEW"
        else:
            verdict = "READY"

        return {
            "trace_id": trace_id,
            "verdict": verdict,
            "reconstructable": recon_report.get("reconstructable", False),
            "valid": val_report.get("valid", False),
            "reasons": reasons,
            "reconstruction_report": recon_report,
            "validation_report": val_report,
            "timestamp": timestamp
        }

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python constitutional_readiness_engine.py <trace_id> [traces_dir]")
        sys.exit(1)
        
    trace_id = sys.argv[1]
    traces_dir = sys.argv[2] if len(sys.argv) > 2 else "storage/traces"
    
    engine = ConstitutionalReadinessEngine(traces_dir)
    decision = engine.evaluate_readiness(trace_id)
    print(json.dumps(decision, indent=4))
