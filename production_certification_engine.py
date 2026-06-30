"""
Production Certification Engine — Parikshak Phase IV
Determines whether a system is ready to become a governed participant inside the TANTRA ecosystem.
"""
import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional
from ecosystem_participation_validator import EcosystemParticipationValidator

logger = logging.getLogger("production_certification_engine")

AUTHORIZED_GOVERNORS = ["Akash", "Ansh", "Saarthi_Governor"]

DIMENSION_WEIGHTS = {
    "Runtime": 0.10,
    "Observability": 0.10,
    "Replayability": 0.10,
    "Governance": 0.10,
    "Provenance": 0.10,
    "Security": 0.10,
    "Versioning": 0.05,
    "Recovery": 0.05,
    "Human Approval": 0.10,
    "Layer Placement": 0.05,
    "Dependency Integrity": 0.05,
    "Ecosystem Participation": 0.10
}

class ProductionCertificationEngine:
    def __init__(self, traces_dir: str = "storage/traces"):
        self.traces_dir = traces_dir
        self.eco_validator = EcosystemParticipationValidator(traces_dir)

    def _read_json(self, trace_path: str, filename: str) -> Optional[Dict[str, Any]]:
        filepath = os.path.join(trace_path, filename)
        if not os.path.exists(filepath):
            return None
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Error parsing json file {filename}: {e}")
            return None

    def check_runtime(self, trace_path: str, trace_id: str) -> str:
        evidence = self._read_json(trace_path, "evidence_bundle.json")
        handover = self._read_json(trace_path, "handover_bundle.json")
        
        if not evidence or not handover:
            return "UNKNOWN"
            
        if evidence.get("trace_id") != trace_id or handover.get("trace_id") != trace_id:
            return "FAIL"
            
        if handover.get("handover_status") == "COMPLETE":
            return "PASS"
        elif handover.get("handover_status") == "FAILED":
            return "FAIL"
            
        return "UNKNOWN"

    def check_observability(self, trace_path: str) -> str:
        telemetry = self._read_json(trace_path, "observability_telemetry.json")
        replay = self._read_json(trace_path, "replay_bundle.json")
        
        # Fallback to checking replay logs for OpenTelemetry markers if observability file is missing
        otel_markers = ["otel.span", "tracer", "OpenTelemetry", "trace_id", "telemetry"]
        
        if not telemetry:
            if replay and replay.get("replay_logs"):
                logs = replay.get("replay_logs", "")
                if any(marker in logs for marker in otel_markers):
                    return "PASS"
            return "UNKNOWN"
            
        if telemetry.get("observability_disabled", False):
            return "FAIL"
            
        if telemetry.get("otel_initialized", False) and telemetry.get("metrics_active", False):
            return "PASS"
            
        return "WARNING"

    def check_replayability(self, trace_path: str) -> str:
        replay = self._read_json(trace_path, "replay_bundle.json")
        verification = self._read_json(trace_path, "replay_verification.json")
        
        if not replay or not verification:
            return "UNKNOWN"
            
        if replay.get("replay_status") == "FAILURE" or verification.get("verified_status") == "FAILED":
            return "FAIL"
            
        if replay.get("replay_status") == "SUCCESS" and verification.get("verified_status") == "VERIFIED":
            return "PASS"
            
        return "WARNING"

    def check_governance(self, trace_path: str) -> str:
        gov_rec = self._read_json(trace_path, "governance_record.json")
        decision = self._read_json(trace_path, "validation_decision.json")
        history = self._read_json(trace_path, "constitutional_history.json")
        
        if not gov_rec or not decision:
            return "UNKNOWN"
            
        dec_val = decision.get("decision")
        if dec_val in ("REJECTED", "FAIL"):
            return "FAIL"
        if not gov_rec.get("valid_authority", False):
            return "FAIL"
            
        # Check constitutional history for block triggers
        if history and history.get("violations_count", 0) > 0:
            if history.get("has_blocker", False):
                return "FAIL"
            return "WARNING"
            
        if dec_val in ("APPROVED", "PASS"):
            return "PASS"
            
        return "UNKNOWN"

    def check_provenance(self, trace_path: str) -> str:
        lineage = self._read_json(trace_path, "lineage_bundle.json")
        lineage_reg = self._read_json(trace_path, "lineage_registration.json")
        chain = self._read_json(trace_path, "lineage_chain.json") or self._read_json(trace_path, "provenance_chain.json")
        
        if not lineage or not chain:
            return "UNKNOWN"
            
        if chain.get("valid_chain") is False or lineage_reg and lineage_reg.get("registered") is False:
            return "FAIL"
            
        # Check lineage list is intact
        chain_list = chain.get("chain", [])
        if not chain_list or len(chain_list) < 1:
            return "FAIL"
            
        return "PASS"

    def check_security(self, trace_path: str) -> str:
        security = self._read_json(trace_path, "security_metadata.json")
        decision = self._read_json(trace_path, "validation_decision.json")
        
        if not security and not decision:
            return "UNKNOWN"
            
        if security:
            critical_vulns = security.get("critical_vulnerabilities", 0)
            high_vulns = security.get("high_vulnerabilities", 0)
            medium_vulns = security.get("medium_vulnerabilities", 0)
            
            if critical_vulns > 0 or high_vulns > 0:
                return "FAIL"
            if medium_vulns > 0:
                return "WARNING"
            if security.get("signature_verified", True) is False:
                return "FAIL"
                
        if decision:
            sig = decision.get("signature")
            signed_by = decision.get("signed_by")
            if not sig or not signed_by:
                return "FAIL"
            if not (sig.startswith("sig-") or sig.startswith("token-")):
                return "FAIL"
                
        return "PASS"

    def check_versioning(self, trace_path: str) -> str:
        schema = self._read_json(trace_path, "schema_metadata.json")
        ref = self._read_json(trace_path, "registration_reference.json") or self._read_json(trace_path, "mdu_registration.json")
        
        if not schema or not ref:
            return "UNKNOWN"
            
        if schema.get("schema_drift", False) is True:
            return "FAIL"
            
        if schema.get("schema_version") != ref.get("schema_version"):
            return "WARNING"
            
        return "PASS"

    def check_recovery(self, trace_path: str) -> str:
        recovery = self._read_json(trace_path, "recovery_metadata.json")
        
        if not recovery:
            return "UNKNOWN"
            
        if recovery.get("recovery_tested", False) is False:
            return "FAIL"
            
        if recovery.get("rollback_anchors_count", 0) == 0:
            return "WARNING"
            
        if recovery.get("recovery_status") == "SUCCESS":
            return "PASS"
            
        return "FAIL"

    def verify_trust_chain(self, trace_id: str) -> Tuple[bool, str]:
        """
        Verify the constitutional trust chain by traversing the lineage chain
        and verifying governance approvals at each node in the lineage.
        """
        trace_path = os.path.join(self.traces_dir, trace_id)
        lineage = self._read_json(trace_path, "lineage_chain.json")
        
        if not lineage:
            return True, "No lineage chain found; starting root trust."
            
        chain = lineage.get("chain", [])
        if not chain:
            return True, "Empty lineage chain; starting root trust."
            
        for t_id in chain:
            if t_id == trace_id:
                continue
            p_path = os.path.join(self.traces_dir, t_id)
            if not os.path.exists(p_path):
                continue
                
            p_dec = self._read_json(p_path, "validation_decision.json")
            p_gov = self._read_json(p_path, "governance_record.json")
            
            if not p_dec or not p_gov:
                return False, f"Missing governance evidence for lineage node: {t_id}"
                
            dec_val = p_dec.get("decision")
            if dec_val not in ("APPROVED", "PASS"):
                return False, f"Lineage node {t_id} decision is not APPROVED/PASS: {dec_val}"
                
            if not p_gov.get("valid_authority", False):
                return False, f"Lineage node {t_id} does not have valid authority"
                
            signer = p_dec.get("signed_by")
            if signer not in AUTHORIZED_GOVERNORS:
                return False, f"Lineage node {t_id} signed by unauthorized governor: {signer}"
                
        return True, "Constitutional trust chain verified"

    def check_human_approval(self, trace_path: str) -> str:
        decision = self._read_json(trace_path, "validation_decision.json")
        gov_rec = self._read_json(trace_path, "governance_record.json")
        
        if not decision or not gov_rec:
            return "UNKNOWN"
            
        signed_by = decision.get("signed_by")
        if not signed_by:
            return "FAIL"
            
        if signed_by not in AUTHORIZED_GOVERNORS:
            return "FAIL"
            
        if not gov_rec.get("valid_authority", False):
            return "FAIL"
            
        # Verify trust chain
        trace_id = os.path.basename(trace_path)
        valid_chain, reason = self.verify_trust_chain(trace_id)
        if not valid_chain:
            logger.warning(f"Trust chain verification failed: {reason}")
            return "FAIL"
            
        dec_val = decision.get("decision")
        if dec_val in ("APPROVED", "PASS"):
            return "PASS"
            
        return "FAIL"

    def check_layer_placement(self, trace_path: str) -> str:
        # Delegate to ecosystem validator
        report = self.eco_validator.validate_placement(trace_path)
        return report.get("status", "UNKNOWN")

    def check_dependency_integrity(self, trace_path: str) -> str:
        # Delegate to ecosystem validator
        report = self.eco_validator.validate_dependencies(trace_path)
        return report.get("status", "UNKNOWN")

    def check_ecosystem_participation(self, trace_path: str) -> str:
        # Delegate to ecosystem validator
        report = self.eco_validator.validate_participation(trace_path)
        return report.get("status", "UNKNOWN")

    def certify_system(self, trace_id: str) -> Dict[str, Any]:
        trace_path = os.path.join(self.traces_dir, trace_id)
        
        report = {
            "system_information": {
                "trace_id": trace_id,
                "certified_at": None,
                "verifier": "Parikshak Production Certification Engine v1.0"
            },
            "dimensions": {},
            "production_score": 0.0,
            "certification_decision": "UNKNOWN",
            "critical_failures": [],
            "warnings": [],
            "risk_summary": ""
        }
        
        if not os.path.exists(trace_path) or not os.path.isdir(trace_path):
            report["risk_summary"] = f"Trace folder {trace_path} not found on disk."
            report["certification_decision"] = "NOT PRODUCTION READY"
            return report

        # Collect dimension statuses
        report["dimensions"]["Runtime"] = self.check_runtime(trace_path, trace_id)
        report["dimensions"]["Observability"] = self.check_observability(trace_path)
        report["dimensions"]["Replayability"] = self.check_replayability(trace_path)
        report["dimensions"]["Governance"] = self.check_governance(trace_path)
        report["dimensions"]["Provenance"] = self.check_provenance(trace_path)
        report["dimensions"]["Security"] = self.check_security(trace_path)
        report["dimensions"]["Versioning"] = self.check_versioning(trace_path)
        report["dimensions"]["Recovery"] = self.check_recovery(trace_path)
        report["dimensions"]["Human Approval"] = self.check_human_approval(trace_path)
        report["dimensions"]["Layer Placement"] = self.check_layer_placement(trace_path)
        report["dimensions"]["Dependency Integrity"] = self.check_dependency_integrity(trace_path)
        report["dimensions"]["Ecosystem Participation"] = self.check_ecosystem_participation(trace_path)

        # Calculate score
        score = 0.0
        for dim, status in report["dimensions"].items():
            weight = DIMENSION_WEIGHTS[dim]
            if status == "PASS":
                score += weight
            elif status == "WARNING":
                score += weight * 0.5
                report["warnings"].append(f"Dimension '{dim}' returned WARNING status.")
            elif status == "FAIL":
                report["critical_failures"].append(f"Critical failure in dimension '{dim}'.")
            elif status == "UNKNOWN":
                report["warnings"].append(f"Dimension '{dim}' status is UNKNOWN (missing evidence).")
                
        production_score_pct = round(score * 100)
        report["production_score"] = production_score_pct

        # Decision rules
        critical_dims = ["Runtime", "Replayability", "Governance", "Security", "Human Approval"]
        has_critical_failure = any(report["dimensions"][d] == "FAIL" for d in report["dimensions"])
        has_critical_unknown = any(report["dimensions"][d] == "UNKNOWN" for d in critical_dims)
        
        if has_critical_failure or production_score_pct < 50:
            decision = "NOT PRODUCTION READY"
        elif has_critical_unknown:
            decision = "NEEDS REVIEW"
        elif production_score_pct >= 90:
            decision = "READY"
        elif production_score_pct >= 75:
            decision = "READY WITH OBSERVATIONS"
        else:
            decision = "NEEDS REVIEW"
            
        report["certification_decision"] = decision
        
        # Dynamic Risk Summary
        if decision == "READY":
            report["risk_summary"] = "System demonstrates compliant architectural boundaries, verified replay safety, and full ecosystem integration. Approved for governed TANTRA production."
        elif decision == "READY WITH OBSERVATIONS":
            report["risk_summary"] = "System meets core requirements, but contains non-blocking warnings or unknown dimensions (e.g. secondary recovery checks or non-critical schema differences)."
        elif decision == "NEEDS REVIEW":
            report["risk_summary"] = "System lacks critical runtime evidence (e.g. missing security reports or human approval records) and must be manually evaluated."
        else:
            report["risk_summary"] = f"Production readiness certification rejected. Found {len(report['critical_failures'])} critical dimension failures."

        # PERSIST TO DATABASE
        try:
            from db.db_config import SessionLocal
            from db.models import CertificationModel, DimensionResultModel, Product
            import uuid

            db = SessionLocal()
            
            # Find or create product associated with this trace (default to prod-tantra)
            product_id = "prod-tantra"
            product_obj = db.query(Product).filter(Product.id == product_id).first()
            if not product_obj:
                product_obj = Product(id=product_id, name="TANTRA Core", description="Primary Governance and Consensus Layer")
                db.add(product_obj)
                db.commit()

            cert_id = f"cert-{uuid.uuid4().hex[:12]}"
            db_cert = CertificationModel(
                id=cert_id,
                trace_id=trace_id,
                product_id=product_id,
                certification_type="Production Readiness",
                status=decision,
                score=production_score_pct,
                certified_at=datetime.utcnow()
            )
            db.add(db_cert)

            # Persist Dimension results
            for dim, status in report["dimensions"].items():
                dim_id = f"dim-{uuid.uuid4().hex[:12]}"
                passed_bool = (status == "PASS")
                
                # Check for matching review record
                from db.models import ReviewModel
                review_id = f"rev-{trace_id}"
                rev_rec = db.query(ReviewModel).filter(ReviewModel.trace_id == trace_id).first()
                if rev_rec:
                    review_id = rev_rec.review_id

                db_dim = DimensionResultModel(
                    id=dim_id,
                    review_id=review_id,
                    dimension_name=dim,
                    score=1.0 if status == "PASS" else (0.5 if status == "WARNING" else 0.0),
                    detail=f"Status: {status}",
                    passed=passed_bool
                )
                db.add(db_dim)
            
            db.commit()
            
            # Automatically generate assignments if failed/degraded
            if decision in ("NEEDS_REVIEW", "NOT PRODUCTION READY"):
                from task_selector.assignment_generator import automatic_assignment_engine
                rev_id = None
                rev_rec = db.query(ReviewModel).filter(ReviewModel.trace_id == trace_id).first()
                if rev_rec:
                    rev_id = rev_rec.review_id
                automatic_assignment_engine.generate_assignments(report, review_id=rev_id)

            db.close()
        except Exception as e:
            logger.error(f"Failed to persist certification in DB: {e}", exc_info=True)

        return report

    def print_grid_output(self, report: Dict[str, Any]):
        dimensions = report.get("dimensions", {})
        if not dimensions:
            print("No trace data processed.")
            return
            
        print("\nBHIV Production Readiness Certification Report")
        print("="*45)
        for dim, status in dimensions.items():
            dots = "." * (30 - len(dim))
            print(f"{dim} {dots} {status}")
        print("="*45)
        print(f"Production Score: {report.get('production_score')}%")
        print(f"Verdict:          {report.get('certification_decision')}")
        print(f"Risk Summary:     {report.get('risk_summary')}\n")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python production_certification_engine.py <trace_id> [traces_dir]")
        sys.exit(1)
        
    trace_id = sys.argv[1]
    traces_dir = sys.argv[2] if len(sys.argv) > 2 else "storage/traces"
    
    engine = ProductionCertificationEngine(traces_dir)
    report = engine.certify_system(trace_id)
    engine.print_grid_output(report)
