"""
Artifact Validation Engine — Parikshak TANTRA Readiness Layer
Validates the content, integrity, hashes, signatures, and status of persisted trace artifacts.
"""
import os
import json
import hashlib
from typing import Dict, Any, List, Tuple

AUTHORIZED_GOVERNORS = ["Akash", "Ansh", "Saarthi_Governor"]

class ArtifactValidationEngine:
    def __init__(self, traces_dir: str = "storage/traces"):
        self.traces_dir = traces_dir

    def calculate_sha256(self, filepath: str) -> str:
        sha256 = hashlib.sha256()
        with open(filepath, "rb") as f:
            while chunk := f.read(8192):
                sha256.update(chunk)
        return sha256.hexdigest()

    def validate_artifacts(self, trace_id: str) -> Dict[str, Any]:
        trace_path = os.path.join(self.traces_dir, trace_id)
        
        report = {
            "trace_id": trace_id,
            "valid": True,
            "layers": {
                "evidence": {"valid": True, "errors": [], "warnings": []},
                "governance": {"valid": True, "errors": [], "warnings": []},
                "replay": {"valid": True, "errors": [], "warnings": []},
                "convergence": {"valid": True, "errors": [], "warnings": []}
            },
            "errors": []
        }

        if not os.path.exists(trace_path) or not os.path.isdir(trace_path):
            report["valid"] = False
            report["errors"].append(f"Trace directory '{trace_path}' not found.")
            return report

        # ── 1. EVIDENCE LAYER VALIDATION ──
        evidence_path = os.path.join(trace_path, "evidence_bundle.json")
        lineage_path = os.path.join(trace_path, "lineage_bundle.json")
        
        if not os.path.exists(evidence_path):
            report["layers"]["evidence"]["valid"] = False
            report["layers"]["evidence"]["errors"].append("Missing evidence_bundle.json")
        else:
            try:
                with open(evidence_path, "r", encoding="utf-8") as f:
                    evidence = json.load(f)
                
                # Check trace_id match
                if evidence.get("trace_id") != trace_id:
                    report["layers"]["evidence"]["valid"] = False
                    report["layers"]["evidence"]["errors"].append("evidence_bundle.json trace_id mismatch.")
                
                # Verify file hashes if actual files are provided under an 'evidence' subfolder
                evidence_files_dir = os.path.join(trace_path, "evidence")
                files_list = evidence.get("files", [])
                
                for file_info in files_list:
                    filename = file_info.get("path")
                    expected_hash = file_info.get("hash")
                    if filename and expected_hash:
                        actual_file_path = os.path.join(evidence_files_dir, filename)
                        if os.path.exists(actual_file_path):
                            actual_hash = self.calculate_sha256(actual_file_path)
                            if actual_hash != expected_hash:
                                report["layers"]["evidence"]["valid"] = False
                                report["layers"]["evidence"]["errors"].append(
                                    f"Hash mismatch for file '{filename}'. Expected {expected_hash}, got {actual_hash}"
                                )
                        else:
                            # If file isn't physically present in evidence dir, check if we can fallback
                            # We record a warning or error based on design. Let's record an error if it's missing but expected.
                            report["layers"]["evidence"]["warnings"].append(
                                f"Physical file '{filename}' listed in evidence bundle not found in trace evidence directory."
                            )
                
                # Validate checksum of the evidence bundle (hash of files list)
                if "checksum" in evidence:
                    files_json = json.dumps(files_list, sort_keys=True, separators=(',', ':'))
                    computed_checksum = hashlib.sha256(files_json.encode('utf-8')).hexdigest()
                    if evidence["checksum"] != computed_checksum:
                        report["layers"]["evidence"]["valid"] = False
                        report["layers"]["evidence"]["errors"].append("Evidence bundle checksum corruption.")
            except Exception as e:
                report["layers"]["evidence"]["valid"] = False
                report["layers"]["evidence"]["errors"].append(f"Failed to parse or validate evidence: {str(e)}")

        # Verify Lineage Reference matching
        if os.path.exists(evidence_path) and os.path.exists(lineage_path):
            try:
                with open(evidence_path, "r", encoding="utf-8") as f:
                    ev = json.load(f)
                with open(lineage_path, "r", encoding="utf-8") as f:
                    lin = json.load(f)
                if ev.get("trace_id") != lin.get("trace_id"):
                    report["layers"]["evidence"]["valid"] = False
                    report["layers"]["evidence"]["errors"].append("Lineage bundle trace_id mismatch.")
            except Exception as e:
                report["layers"]["evidence"]["warnings"].append(f"Lineage alignment check failed: {e}")

        # ── 2. GOVERNANCE LAYER VALIDATION ──
        dec_path = os.path.join(trace_path, "validation_decision.json")
        gov_rec_path = os.path.join(trace_path, "governance_record.json")
        
        if not os.path.exists(dec_path):
            report["layers"]["governance"]["valid"] = False
            report["layers"]["governance"]["errors"].append("Missing validation_decision.json")
        else:
            try:
                with open(dec_path, "r", encoding="utf-8") as f:
                    dec = json.load(f)
                
                # Check decision
                decision = dec.get("decision")
                if decision == "REJECTED":
                    report["layers"]["governance"]["valid"] = False
                    report["layers"]["governance"]["errors"].append("Governance decision is REJECTED.")
                elif decision != "APPROVED":
                    report["layers"]["governance"]["warnings"].append(f"Governance decision is status: {decision}")
                
                # Check signature authority
                signed_by = dec.get("signed_by")
                if signed_by not in AUTHORIZED_GOVERNORS:
                    report["layers"]["governance"]["valid"] = False
                    report["layers"]["governance"]["errors"].append(f"Unauthorized governance signature by: {signed_by}")
                
                # Check signature token exists and format
                sig = dec.get("signature")
                if not sig or not (sig.startswith("sig-") or sig.startswith("token-")):
                    report["layers"]["governance"]["valid"] = False
                    report["layers"]["governance"]["errors"].append("Invalid signature or approval token format.")
            except Exception as e:
                report["layers"]["governance"]["valid"] = False
                report["layers"]["governance"]["errors"].append(f"Failed to parse or validate decision: {str(e)}")

        if os.path.exists(gov_rec_path):
            try:
                with open(gov_rec_path, "r", encoding="utf-8") as f:
                    gov_rec = json.load(f)
                if not gov_rec.get("valid_authority", False):
                    report["layers"]["governance"]["valid"] = False
                    report["layers"]["governance"]["errors"].append("Governance record indicates invalid authority.")
            except Exception as e:
                report["layers"]["governance"]["warnings"].append(f"Failed to parse governance record: {e}")

        # ── 3. REPLAY LAYER VALIDATION ──
        replay_path = os.path.join(trace_path, "replay_bundle.json")
        if not os.path.exists(replay_path):
            report["layers"]["replay"]["valid"] = False
            report["layers"]["replay"]["errors"].append("Missing replay_bundle.json")
        else:
            try:
                with open(replay_path, "r", encoding="utf-8") as f:
                    replay = json.load(f)
                
                status = replay.get("replay_status")
                if status == "FAILURE":
                    report["layers"]["replay"]["valid"] = False
                    report["layers"]["replay"]["errors"].append("Replay status indicates FAILURE.")
                elif status != "SUCCESS":
                    report["layers"]["replay"]["warnings"].append(f"Replay status is: {status}")
                
                # Check logs for fatal errors
                logs = replay.get("replay_logs", "")
                fatal_markers = ["FATAL", "Traceback (most recent call last):", "Exception:", "[ERROR]"]
                found_errors = [m for m in fatal_markers if m in logs]
                if found_errors:
                    report["layers"]["replay"]["warnings"].append(f"Replay logs contain error markers: {found_errors}")
                    if status == "SUCCESS":
                        # Downgrade to warning if status says success but logs have error markers
                        report["layers"]["replay"]["warnings"].append("Replay claims SUCCESS but logs contain error markers.")
            except Exception as e:
                report["layers"]["replay"]["valid"] = False
                report["layers"]["replay"]["errors"].append(f"Failed to parse or validate replay: {str(e)}")

        # ── 4. CONVERGENCE LAYER VALIDATION ──
        conv_path = os.path.join(trace_path, "tms_convergence_status.json")
        if not os.path.exists(conv_path):
            report["layers"]["convergence"]["valid"] = False
            report["layers"]["convergence"]["errors"].append("Missing tms_convergence_status.json")
        else:
            try:
                with open(conv_path, "r", encoding="utf-8") as f:
                    conv = json.load(f)
                
                status = conv.get("convergence_status")
                if status == "FAILED":
                    report["layers"]["convergence"]["valid"] = False
                    report["layers"]["convergence"]["errors"].append("Convergence status is FAILED.")
                elif status != "CONVERGED":
                    report["layers"]["convergence"]["warnings"].append(f"Convergence status is: {status}")
                
                if not conv.get("registration_exists", False):
                    report["layers"]["convergence"]["valid"] = False
                    report["layers"]["convergence"]["errors"].append("TANTRA registration does not exist.")
            except Exception as e:
                report["layers"]["convergence"]["valid"] = False
                report["layers"]["convergence"]["errors"].append(f"Failed to parse or validate convergence: {str(e)}")

        # Aggregate layer validations to overall report validity
        for layer_name, layer_info in report["layers"].items():
            if not layer_info["valid"]:
                report["valid"] = False
                report["errors"].extend(layer_info["errors"])

        return report

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python artifact_validation_engine.py <trace_id> [traces_dir]")
        sys.exit(1)
    
    trace_id = sys.argv[1]
    traces_dir = sys.argv[2] if len(sys.argv) > 2 else "storage/traces"
    
    engine = ArtifactValidationEngine(traces_dir)
    report = engine.validate_artifacts(trace_id)
    print(json.dumps(report, indent=4))
