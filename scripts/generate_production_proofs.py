"""
Generate Production Readiness Certification Runtime Proofs
Writes three realistic trace directories on disk (Ready, Needs Review, Rejected) and executes Parikshak to generate validation proofs.
"""
import os
import sys
import json
from datetime import datetime, timezone
from typing import Any

# Add root directory to sys.path
sys.path.append(os.getcwd())

TRACES_DIR = "storage/traces"
PROOFS_DIR = "runtime_certification_proofs"

def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)

def write_json(path: str, filename: str, data: Any):
    ensure_dir(path)
    with open(os.path.join(path, filename), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def create_ready_system():
    trace_id = "trace-prod-ready"
    path = os.path.join(TRACES_DIR, trace_id)
    
    # 1. Pratham
    write_json(path, "evidence_bundle.json", {
        "trace_id": trace_id,
        "files": [{"path": "app.py", "hash": "8f8e8d8c8b8a", "size": 1024}],
        "checksum": "a1b2c3d4e5f6",
        "timestamp": _utcnow()
    })
    write_json(path, "replay_bundle.json", {
        "trace_id": trace_id,
        "replay_script": "pytest tests/",
        "replay_status": "SUCCESS",
        "replay_logs": "test_app.py . [100%]\n1 passed in 0.05s"
    })
    write_json(path, "lineage_bundle.json", {
        "trace_id": trace_id,
        "parent_trace_id": "trace-parent-111",
        "lineage_path": ["trace-parent-111"],
        "integrity_hash": "lin-hash-111"
    })
    write_json(path, "handover_bundle.json", {
        "trace_id": trace_id,
        "recipient": "TANTRA_CORE",
        "handover_status": "COMPLETE"
    })
    
    # 2. Shakti (Ansh)
    write_json(path, "governance_record.json", {
        "trace_id": trace_id,
        "governor": "Akash",
        "authority_level": "Level_3_Governor",
        "valid_authority": True
    })
    write_json(path, "validation_decision.json", {
        "trace_id": trace_id,
        "decision": "APPROVED",
        "signed_by": "Akash",
        "signature": "sig-governor-akash-approved-789"
    })
    write_json(path, "replay_verification.json", {
        "trace_id": trace_id,
        "verified_status": "VERIFIED"
    })
    write_json(path, "constitutional_history.json", {
        "trace_id": trace_id,
        "violations_count": 0,
        "has_blocker": False
    })
    write_json(path, "consumer_registration.json", {
        "trace_id": trace_id,
        "consumer_id": "accounts-api-service",
        "registered": True
    })
    
    # 3. MDU
    write_json(path, "registration_reference.json", {
        "trace_id": trace_id,
        "registration_id": "reg-mdu-111",
        "schema_version": "v1.0"
    })
    write_json(path, "lineage_registration.json", {
        "trace_id": trace_id,
        "lineage_root": "trace-parent-111",
        "registered": True
    })
    write_json(path, "lineage_chain.json", {
        "trace_id": trace_id,
        "chain": [trace_id, "trace-parent-111"],
        "valid_chain": True
    })
    write_json(path, "schema_metadata.json", {
        "trace_id": trace_id,
        "schema_version": "v1.0",
        "schema_drift": False
    })
    
    # 4. TMS
    write_json(path, "tms_convergence_status.json", {
        "trace_id": trace_id,
        "convergence_status": "CONVERGED",
        "registration_exists": True
    })
    write_json(path, "ecosystem_placement.json", {
        "trace_id": trace_id,
        "layer": "Core",
        "authority_boundary": "bhiv.core.accounts",
        "ownership_declaration": {"owner_team": "account-devs"}
    })
    write_json(path, "architectural_participation.json", {
        "trace_id": trace_id,
        "runtime_participants": ["accounts-api"],
        "upstream_systems": ["auth-gate"],
        "downstream_systems": ["ledger-writer"]
    })
    
    # 5. Core Checklist / Ecosystem telemetry & security
    write_json(path, "observability_telemetry.json", {
        "trace_id": trace_id,
        "otel_initialized": True,
        "metrics_active": True
    })
    write_json(path, "security_metadata.json", {
        "trace_id": trace_id,
        "critical_vulnerabilities": 0,
        "high_vulnerabilities": 0,
        "signature_verified": True
    })
    write_json(path, "recovery_metadata.json", {
        "trace_id": trace_id,
        "recovery_tested": True,
        "rollback_anchors_count": 3,
        "recovery_status": "SUCCESS"
    })
    write_json(path, "dependency_graph.json", {
        "trace_id": trace_id,
        "dependencies": {
            "accounts-api": ["db-lib", "auth-utils"],
            "db-lib": [],
            "auth-utils": []
        }
    })

def create_needs_review_system():
    trace_id = "trace-prod-needs-review"
    path = os.path.join(TRACES_DIR, trace_id)
    
    # 1. Pratham
    write_json(path, "evidence_bundle.json", {
        "trace_id": trace_id,
        "files": [{"path": "app.py", "hash": "8f8e8d8c8b8a", "size": 1024}],
        "checksum": "a1b2c3d4e5f6",
        "timestamp": _utcnow()
    })
    write_json(path, "replay_bundle.json", {
        "trace_id": trace_id,
        "replay_script": "pytest tests/",
        "replay_status": "SUCCESS",
        "replay_logs": "test_app.py . [100%]\n1 passed in 0.05s"
    })
    write_json(path, "lineage_bundle.json", {
        "trace_id": trace_id,
        "parent_trace_id": "trace-parent-111",
        "lineage_path": ["trace-parent-111"],
        "integrity_hash": "lin-hash-111"
    })
    write_json(path, "handover_bundle.json", {
        "trace_id": trace_id,
        "recipient": "TANTRA_CORE",
        "handover_status": "COMPLETE"
    })
    
    # 2. Shakti (Ansh)
    # Human validation decision is missing -> This flags it for Manual Review (NEEDS REVIEW)
    
    write_json(path, "governance_record.json", {
        "trace_id": trace_id,
        "governor": "Akash",
        "authority_level": "Level_3_Governor",
        "valid_authority": True
    })
    write_json(path, "replay_verification.json", {
        "trace_id": trace_id,
        "verified_status": "VERIFIED"
    })
    write_json(path, "constitutional_history.json", {
        "trace_id": trace_id,
        "violations_count": 0,
        "has_blocker": False
    })
    write_json(path, "consumer_registration.json", {
        "trace_id": trace_id,
        "consumer_id": "accounts-api-service",
        "registered": True
    })
    
    # 3. MDU
    write_json(path, "registration_reference.json", {
        "trace_id": trace_id,
        "registration_id": "reg-mdu-111",
        "schema_version": "v1.0"
    })
    write_json(path, "lineage_registration.json", {
        "trace_id": trace_id,
        "lineage_root": "trace-parent-111",
        "registered": True
    })
    write_json(path, "lineage_chain.json", {
        "trace_id": trace_id,
        "chain": [trace_id, "trace-parent-111"],
        "valid_chain": True
    })
    write_json(path, "schema_metadata.json", {
        "trace_id": trace_id,
        "schema_version": "v1.0",
        "schema_drift": False
    })
    
    # 4. TMS
    write_json(path, "tms_convergence_status.json", {
        "trace_id": trace_id,
        "convergence_status": "CONVERGED",
        "registration_exists": True
    })
    write_json(path, "ecosystem_placement.json", {
        "trace_id": trace_id,
        "layer": "Core",
        "authority_boundary": "bhiv.core.accounts",
        "ownership_declaration": {"owner_team": "account-devs"}
    })
    write_json(path, "architectural_participation.json", {
        "trace_id": trace_id,
        "runtime_participants": ["accounts-api"],
        "upstream_systems": ["auth-gate"],
        "downstream_systems": ["ledger-writer"]
    })
    
    # 5. Core Checklist
    write_json(path, "observability_telemetry.json", {
        "trace_id": trace_id,
        "otel_initialized": True,
        "metrics_active": True
    })
    write_json(path, "security_metadata.json", {
        "trace_id": trace_id,
        "critical_vulnerabilities": 0,
        "high_vulnerabilities": 0,
        "signature_verified": True
    })
    
    # Recovery metadata is missing -> non-critical missing context (score drops)
    
    write_json(path, "dependency_graph.json", {
        "trace_id": trace_id,
        "dependencies": {
            "accounts-api": ["db-lib", "auth-utils"],
            "db-lib": [],
            "auth-utils": []
        }
    })

def create_rejected_system():
    trace_id = "trace-prod-rejected"
    path = os.path.join(TRACES_DIR, trace_id)
    
    # 1. Pratham
    write_json(path, "evidence_bundle.json", {
        "trace_id": trace_id,
        "files": [{"path": "app.py", "hash": "8f8e8d8c8b8a", "size": 1024}],
        "checksum": "a1b2c3d4e5f6",
        "timestamp": _utcnow()
    })
    write_json(path, "replay_bundle.json", {
        "trace_id": trace_id,
        "replay_script": "pytest tests/",
        "replay_status": "SUCCESS",
        "replay_logs": "test_app.py . [100%]\n1 passed in 0.05s"
    })
    write_json(path, "lineage_bundle.json", {
        "trace_id": trace_id,
        "parent_trace_id": "trace-parent-111",
        "lineage_path": ["trace-parent-111"],
        "integrity_hash": "lin-hash-111"
    })
    write_json(path, "handover_bundle.json", {
        "trace_id": trace_id,
        "recipient": "TANTRA_CORE",
        "handover_status": "COMPLETE"
    })
    
    # 2. Shakti (Ansh)
    write_json(path, "governance_record.json", {
        "trace_id": trace_id,
        "governor": "Akash",
        "authority_level": "Level_3_Governor",
        "valid_authority": True
    })
    write_json(path, "validation_decision.json", {
        "trace_id": trace_id,
        "decision": "APPROVED",
        "signed_by": "Akash",
        "signature": "sig-governor-akash-approved-789"
    })
    write_json(path, "replay_verification.json", {
        "trace_id": trace_id,
        "verified_status": "VERIFIED"
    })
    write_json(path, "constitutional_history.json", {
        "trace_id": trace_id,
        "violations_count": 0,
        "has_blocker": False
    })
    write_json(path, "consumer_registration.json", {
        "trace_id": trace_id,
        "consumer_id": "accounts-api-service",
        "registered": True
    })
    
    # 3. MDU
    write_json(path, "registration_reference.json", {
        "trace_id": trace_id,
        "registration_id": "reg-mdu-111",
        "schema_version": "v1.0"
    })
    write_json(path, "lineage_registration.json", {
        "trace_id": trace_id,
        "lineage_root": "trace-parent-111",
        "registered": True
    })
    write_json(path, "lineage_chain.json", {
        "trace_id": trace_id,
        "chain": [trace_id, "trace-parent-111"],
        "valid_chain": True
    })
    write_json(path, "schema_metadata.json", {
        "trace_id": trace_id,
        "schema_version": "v1.0",
        "schema_drift": False
    })
    
    # 4. TMS
    write_json(path, "tms_convergence_status.json", {
        "trace_id": trace_id,
        "convergence_status": "CONVERGED",
        "registration_exists": True
    })
    write_json(path, "ecosystem_placement.json", {
        "trace_id": trace_id,
        "layer": "Core",
        "authority_boundary": "bhiv.core.accounts",
        "ownership_declaration": {"owner_team": "account-devs"}
    })
    write_json(path, "architectural_participation.json", {
        "trace_id": trace_id,
        "runtime_participants": ["accounts-api"],
        "upstream_systems": ["auth-gate"],
        "downstream_systems": ["ledger-writer"]
    })
    
    # 5. Core Checklist with critical failures
    write_json(path, "observability_telemetry.json", {
        "trace_id": trace_id,
        "otel_initialized": True,
        "metrics_active": True
    })
    
    # Critical security failure: critical vulnerabilities > 0
    write_json(path, "security_metadata.json", {
        "trace_id": trace_id,
        "critical_vulnerabilities": 3,
        "high_vulnerabilities": 0,
        "signature_verified": True
    })
    
    write_json(path, "recovery_metadata.json", {
        "trace_id": trace_id,
        "recovery_tested": True,
        "rollback_anchors_count": 3,
        "recovery_status": "SUCCESS"
    })
    
    # Dependency graph circular cycle: A -> B -> A
    write_json(path, "dependency_graph.json", {
        "trace_id": trace_id,
        "dependencies": {
            "accounts-api": ["db-lib"],
            "db-lib": ["accounts-api"]
        }
    })

def main():
    print("Seeding traces directory with systems...")
    create_ready_system()
    create_needs_review_system()
    create_rejected_system()
    print("Seeding complete.")

    # Run Certification Engine on the 3 systems
    from production_certification_engine import ProductionCertificationEngine
    engine = ProductionCertificationEngine(TRACES_DIR)
    
    ensure_dir(PROOFS_DIR)
    
    systems = ["trace-prod-ready", "trace-prod-needs-review", "trace-prod-rejected"]
    for sys in systems:
        report = engine.certify_system(sys)
        # Update certified_at timestamp
        report["system_information"]["certified_at"] = _utcnow()
        
        # Save json standard report
        with open(os.path.join(PROOFS_DIR, f"{sys.replace('trace-prod-', '')}_system_report.json"), "w") as f:
            json.dump(report, f, indent=4)
            
        # Write printable text proof block
        # We can construct a small readable proof text file
        proof_lines = []
        proof_lines.append(f"Trace ID: {sys}")
        proof_lines.append("="*45)
        for dim, status in report["dimensions"].items():
            dots = "." * (30 - len(dim))
            proof_lines.append(f"{dim} {dots} {status}")
        proof_lines.append("="*45)
        proof_lines.append(f"Production Score: {report['production_score']}%")
        proof_lines.append(f"Final Verdict:    {report['certification_decision']}")
        proof_lines.append(f"Risk Summary:     {report['risk_summary']}\n")
        
        with open(os.path.join(PROOFS_DIR, f"{sys.replace('trace-prod-', '')}_system_proof.txt"), "w") as f:
            f.write("\n".join(proof_lines))
            
    print(f"Certification reports successfully written to /{PROOFS_DIR}!")

if __name__ == "__main__":
    main()
