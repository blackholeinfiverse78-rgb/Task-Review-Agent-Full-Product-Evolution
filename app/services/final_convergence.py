"""
FINAL CONVERGENCE Orchestrator - Enforces True Hierarchy
Assignment Authority > Signal Support > Validation Gate

This orchestrator ensures:
1. Sri Satya (Assignment) = AUTHORITATIVE
2. Ishan (Signals) = SUPPORTING ONLY
3. Shraddha (Validation) = FINAL WRAPPER
"""
from typing import Dict, Any, Optional
import logging
from datetime import datetime

from .assignment_engine import assignment_engine
from .shraddha_validation import validation_gate
from .signal_engine import signal_engine as signal_collector
from .validator import validator as registry_validator, ValidationStatus
from .review_packet_parser import review_packet_parser
from .production_decision_engine import production_decision_engine
from .bucket_integration import bucket_integration
from .human_in_loop import human_in_loop
from .domain_router import domain_router
from .task_selection_engine import task_selection_engine
from .task_selector import task_selector
from .graph_engine import graph_engine

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from engine.task_graph_engine import task_graph_engine
from engine.mandala_mapper import mandala_mapper

logger = logging.getLogger("final_convergence")

class FinalConvergenceOrchestrator:
    """
    FINAL CONVERGENCE Orchestrator
    
    Enforces the true hierarchy:
    1. Assignment Authority (Sri Satya) = PRIMARY DECISION MAKER
    2. Signal Evaluation (Ishan) = SUPPORTING DATA ONLY
    3. Validation Layer (Shraddha) = FINAL QUALITY GATE
    
    NO parallel logic paths - single unified flow
    """
    
    def __init__(self):
        self.hierarchy_level = "CONVERGENCE_ORCHESTRATOR"
        # NO evaluation engine - only signal collector
        self.convergence_enforced = True
        self.authority_hierarchy = {
            "PRIMARY": "assignment_authority",
            "SUPPORTING": "signal_engine", 
            "FINAL_GATE": "validation_gate"
        }
    
    def process_with_convergence(
        self,
        task_title: str,
        task_description: str,
        repository_url: Optional[str] = None,
        module_id: str = "task-review-agent",
        schema_version: str = "v1.0",
        pdf_text: str = "",
        current_task_id: Optional[str] = None,
        submitted_by: str = ""
    ) -> Dict[str, Any]:
        """
        FINAL CONVERGENCE processing with enforced hierarchy
        
        Flow:
        1. Registry Validation (Structural Discipline)
        2. Assignment Authority Evaluation (PRIMARY)
        3. Signal Support (SUPPORTING ONLY)
        4. Validation Gate (FINAL WRAPPER)
        
        Args:
            task_title: Task title
            task_description: Task description
            repository_url: GitHub repository URL
            module_id: Blueprint Registry module ID
            schema_version: Schema version
            pdf_text: PDF content if any
            
        Returns:
            Final converged evaluation result
        """
        logger.info(f"[FINAL CONVERGENCE] Starting convergence processing for: {task_title[:50]}...")
        
        # STEP 0: Review Packet Hard Gate Enforcement
        logger.info("[FINAL CONVERGENCE] Step 0: Review Packet Hard Gate")
        packet_result = review_packet_parser.enforce_packet_requirement(".")
        
        if not packet_result["valid"]:
            logger.error(f"[FINAL CONVERGENCE] Review packet validation failed: {packet_result['reason']}")
            import hashlib
            content_hash = hashlib.md5(f"{task_title}{task_description}".encode(), usedforsecurity=False).hexdigest()[:12]
            rejection_result = {
                "submission_id": f"packet-rejected-{content_hash}",
                "score": 0,
                "status": "fail",
                "readiness_percent": 0,
                "next_task_id": f"packet-fix-{content_hash}",
                "task_type": "correction",
                "title": "Review Packet Creation Task",
                "difficulty": "foundational",
                "failure_reasons": [f"Review Packet Missing: {packet_result['reason']}"],
                "packet_rejection": True
            }
            return validation_gate.validate_final_output(rejection_result, "packet_rejection")
        
        # STEP 1: Registry Validation (Structural Discipline Enforcement)
        logger.info("[FINAL CONVERGENCE] Step 1: Registry Validation")
        registry_result = registry_validator.validate_complete(module_id, schema_version)
        
        if registry_result.status == ValidationStatus.INVALID:
            logger.warning(f"[FINAL CONVERGENCE] Registry validation failed: {registry_result.reason}")
            import hashlib
            content_hash = hashlib.md5(f"{task_title}{task_description}{module_id}{schema_version}".encode(), usedforsecurity=False).hexdigest()[:12]
            rejection_result = {
                "submission_id": f"rejected-{content_hash}",
                "score": 0,
                "status": "fail",
                "readiness_percent": 0,
                "next_task_id": f"registry-correction-{content_hash}",
                "task_type": "correction",
                "title": "Registry Compliance Task",
                "difficulty": "foundational",
                "failure_reasons": [f"Registry Validation Failed: {registry_result.reason}"],
                "registry_rejection": True
            }
            return validation_gate.validate_final_output(rejection_result, "registry_rejection")

        # STEP 1.5: Prerequisite Gate (Gap 4)
        if current_task_id:
            prerequisites = graph_engine.get_prerequisites(current_task_id)
            if prerequisites:
                from ..models.persistent_storage import product_storage
                completed_ids = set()
                if submitted_by:
                    for sub in product_storage.submissions.values():
                        if sub.submitted_by == submitted_by:
                            completed_ids.add(sub.task_id)
                unmet = [p for p in prerequisites if p not in completed_ids]
                if unmet:
                    logger.warning(f"[FINAL CONVERGENCE] Prerequisites not met for {current_task_id}: {unmet}")
                    import hashlib
                    content_hash = hashlib.md5(f"{task_title}{task_description}".encode(), usedforsecurity=False).hexdigest()[:12]
                    prereq_task = graph_engine.get_task(unmet[0])
                    rejection_result = {
                        "submission_id": f"prereq-blocked-{content_hash}",
                        "score": 0,
                        "status": "fail",
                        "readiness_percent": 0,
                        "next_task_id": unmet[0],
                        "task_type": "correction",
                        "title": prereq_task.get("title", "Prerequisite Task") if prereq_task else "Prerequisite Task",
                        "difficulty": "beginner",
                        "failure_reasons": [f"Prerequisites not met: complete {unmet} first"],
                        "prerequisite_rejection": True
                    }
                    return validation_gate.validate_final_output(rejection_result, "prerequisite_rejection")
        
        # STEP 2: Signal Collection (SUPPORTING DATA ONLY)
        logger.info("[FINAL CONVERGENCE] Step 2: Signal Collection (Supporting Data)")
        supporting_signals = signal_collector.collect_supporting_signals(
            task_title=task_title,
            task_description=task_description,
            repository_url=repository_url,
            pdf_text=pdf_text
        )

        # STEP 2.5: Domain Routing — enrich signals with domain context
        logger.info("[FINAL CONVERGENCE] Step 2.5: Domain Routing")
        supporting_signals = domain_router.enrich_signals(
            supporting_signals, task_title, task_description
        )
        logger.info(f"[FINAL CONVERGENCE] Domain detected: {supporting_signals.get('domain', 'unknown')}")
        
        try:
            # STEP 3: Sri Satya Intelligence Evaluation (SINGLE AUTHORITY)
            logger.info("[FINAL CONVERGENCE] Step 3: Sri Satya Intelligence Evaluation (SINGLE AUTHORITY)")
            canonical_result = assignment_engine.evaluate_and_assign(
                task_title=task_title,
                task_description=task_description,
                supporting_signals=supporting_signals
            )
            
            logger.info(f"[FINAL CONVERGENCE] Sri Satya result: Score={canonical_result.get('score')}, Status={canonical_result.get('status')}")
            
        except Exception as e:
            logger.error(f"[FINAL CONVERGENCE] Sri Satya evaluation failed: {e}")
            import traceback
            logger.error(f"[FINAL CONVERGENCE] Full traceback: {traceback.format_exc()}")
            
            # Create fallback result with component scores from signals
            title_score = supporting_signals.get("title_signals", {}).get("score", 0)
            desc_score = supporting_signals.get("description_signals", {}).get("score", 0)
            repo_score = 0  # No repo in this case
            fallback_score = int(title_score + desc_score + repo_score)
            
            canonical_result = {
                "score": fallback_score,
                "status": "fail" if fallback_score < 50 else "borderline" if fallback_score < 80 else "pass",
                "task_type": "correction",
                "title": "System Recovery Task",
                "difficulty": "foundational",
                "reason": f"Evaluation system error: {str(e)}",
                "title_score": title_score,
                "description_score": desc_score,
                "repository_score": repo_score,
                "error_recovery": True
            }
        
        try:
            # STEP 4: Production Decision Engine
            logger.info("[FINAL CONVERGENCE] Step 4: Production Decision Engine")
            decision_result = production_decision_engine.make_decision(
                canonical_result, supporting_signals, packet_result.get("parsed_data")
            )
            
            # STEP 5: Human-in-Loop Processing
            logger.info("[FINAL CONVERGENCE] Step 5: Human-in-Loop Processing")
            enhanced_result = human_in_loop.process_with_human_loop(
                canonical_result, decision_result, supporting_signals, 
                f"trace-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            )
            
            # STEP 6: Validation Gate (FINAL WRAPPER)
            logger.info("[FINAL CONVERGENCE] Step 6: Validation Gate (Final Wrapper)")
            
            # Convert canonical result to API format
            api_format_result = self._convert_canonical_to_api_format(
                enhanced_result, supporting_signals, task_title, task_description, module_id, schema_version, current_task_id
            )
            
            final_result = validation_gate.validate_final_output(
                api_format_result, "production_pipeline"
            )
            
            # STEP 7: Bucket Logging
            logger.info("[FINAL CONVERGENCE] Step 7: Bucket Logging")
            trace_id = bucket_integration.log_evaluation(
                enhanced_result, supporting_signals, decision_result,
                final_result, {
                    "task_title": task_title,
                    "task_description": task_description,
                    "submitted_by": "system",
                    "github_repo_link": repository_url
                }
            )
            
        except Exception as e:
            logger.error(f"[FINAL CONVERGENCE] Validation gate failed: {e}")
            import traceback
            logger.error(f"[FINAL CONVERGENCE] Validation traceback: {traceback.format_exc()}")
            print("EXCEPTION CAUGHT:", e)
            print(traceback.format_exc())
            
            # Create emergency response
            final_result = {
                "submission_id": f"emergency-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "score": canonical_result.get("score", 0),
                "status": canonical_result.get("status", "fail"),
                "readiness_percent": canonical_result.get("score", 0),
                "next_task_id": f"emergency-next-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "task_type": "correction",
                "title": "Emergency Recovery Task",
                "difficulty": "foundational",
                "failure_reasons": [f"Validation error: {str(e)}"],
                "title_score": canonical_result.get("title_score", 0),
                "description_score": canonical_result.get("description_score", 0),
                "repository_score": canonical_result.get("repository_score", 0),
                "emergency_response": True
            }
        
        # STEP 5: Add Convergence Metadata
        converged_result = self._add_convergence_metadata(final_result, supporting_signals)
        
        logger.info(f"[FINAL CONVERGENCE] Convergence complete - Final Status: {converged_result.get('status')}")
        return converged_result
    
    def _convert_canonical_to_api_format(
        self, 
        canonical_result: Dict[str, Any], 
        supporting_signals: Dict[str, Any],
        task_title: str,
        task_description: str,
        module_id: str,
        schema_version: str,
        current_task_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Convert Canonical Intelligence result to API format
        
        Args:
            canonical_result: Result from Canonical Intelligence Engine
            supporting_signals: Supporting signals for reference
            
        Returns:
            API-formatted result
        """
        # Extract canonical data
        score = canonical_result.get("score", 0)
        score_10 = canonical_result.get("score_10", score / 10 if score else 0)
        status = canonical_result.get("status", "fail")
        decision = "APPROVED" if score_10 >= 6.0 else "REJECTED"

        # Phase 5 Flow Execution
        try:
            mapped_context = mandala_mapper.resolve_context(task_title, task_description)
        except ValueError as e:
            logger.error(f"[FINAL CONVERGENCE] Mandala mapping failed: {e}")
            mapped_context = {
                "product": "Unknown",
                "layer": "Unknown",
                "subsystem": "Unknown",
                "capability": "Unknown"
            }
            
        active_task_id = current_task_id or "T-GOV-001"
        next_task_id = task_graph_engine.resolve_next_task(active_task_id, score_10)
        next_task = task_graph_engine.get_task(next_task_id)
        
        selection_reason = f"Score is {score_10}. Proceeding to {'next task' if score_10 >= 6.0 else 'failure recovery task'}."
        
        # Generate DETERMINISTIC IDs based on content hash + timestamp for traceability
        import hashlib
        import time
        
        # Create deterministic base from content
        content_base = f"{task_title}{task_description}{module_id}{schema_version}"
        content_hash = hashlib.md5(content_base.encode(), usedforsecurity=False).hexdigest()[:12]
        
        # Add attempt tracking for Vinayak testing protocol
        timestamp_ms = int(time.time() * 1000)
        attempt_hash = hashlib.md5(f"{content_base}{timestamp_ms}".encode(), usedforsecurity=False).hexdigest()[:8]
        
        submission_id = f"sub-{content_hash}-{attempt_hash}"
        
        task_type = "correction"
        if status == "pass":
            task_type = "advancement"
        elif status == "borderline":
            task_type = "reinforcement"
            
        # Convert to API format with proper score breakdown
        api_result = {
            "submission_id": submission_id,
            "submission_timestamp": datetime.now().isoformat(),
            "attempt_number": 1,
            "score": score,
            "status": status,
            "readiness_percent": canonical_result.get("readiness_percent", score),
            "next_task_id": next_task_id,
            "task_type": task_type,
            "title": next_task.get("capability", "Task"),
            "difficulty": "intermediate",
            "objective": next_task.get("dharma", ""),
            "product": mapped_context["product"],
            "layer": mapped_context["layer"],
            "subsystem": mapped_context["subsystem"],
            "capability": mapped_context["capability"],
            "selection_reason": selection_reason,
            "source": "task_graph",
            
            "dharma": next_task.get("dharma", ""),
            "completion_signals": next_task.get("completion_signals", []),
            
            # Evidence and metadata
            "missing_features": supporting_signals.get("missing_features", []),
            "failure_reasons": [str(f) for f in supporting_signals.get("failure_indicators", [])],
            "expected_vs_delivered": supporting_signals.get("expected_vs_delivered_evidence", {}),
            "evaluation_summary": f"Sri Satya Intelligence Evaluation: {status} (Score: {score})",
            "improvement_hints": self._generate_improvement_hints(canonical_result, supporting_signals),
            
            # Add traceability metadata
            "traceability": {
                "content_hash": content_hash,
                "attempt_hash": attempt_hash,
                "submission_timestamp": datetime.now().isoformat(),
                "deterministic_base": content_base[:100] + "...",
                "vinayak_testing_ready": True
            },
            
            # CRITICAL: Mark as canonical authority to preserve scores
            "canonical_authority": True,
            "evaluation_basis": "sri_satya_assignment_engine",
            "evidence_summary": canonical_result.get("evidence_summary", {}),
            
            # CRITICAL: Pass through Sri Satya's CANONICAL component scores
            "supporting_signals": {
                **supporting_signals,
                "technical_signals": {
                    "title_score": canonical_result.get("title_score", 0),
                    "description_score": canonical_result.get("description_score", 0),
                    "repository_score": canonical_result.get("repository_score", 0)
                },
                "implementation_signals": supporting_signals.get("implementation_signals", {}),
                "requirement_match": supporting_signals.get("feature_match_ratio", 0.0),
                "documentation_alignment": supporting_signals.get("documentation_alignment", "low")
            },
            
            # Add component scores to top level for direct access
            "title_score": canonical_result.get("title_score", 0),
            "description_score": canonical_result.get("description_score", 0),
            "repository_score": canonical_result.get("repository_score", 0)
        }
        
        return api_result
    
    def _generate_improvement_hints(
        self, 
        canonical_result: Dict[str, Any], 
        supporting_signals: Dict[str, Any]
    ) -> list:
        """
        Generate improvement hints based on canonical evaluation
        """
        hints = []
        
        evidence = canonical_result.get("evidence_summary", {})
        missing_count = evidence.get("missing_features_count", 0)
        delivery_ratio = evidence.get("delivery_ratio", 0.0)
        
        if not supporting_signals.get("repository_available"):
            hints.append("Provide valid GitHub repository with implementation")
        
        if missing_count > 0:
            hints.append(f"Implement {missing_count} missing features")
        
        if delivery_ratio < 0.5:
            hints.append("Increase feature delivery ratio - implement more requirements")
        
        failure_indicators = supporting_signals.get("failure_indicators", [])
        if "low_feature_match_ratio" in str(failure_indicators):
            hints.append("Improve implementation to match requirements more closely")
        
        if "insufficient_implementation_scope" in str(failure_indicators):
            hints.append("Expand implementation scope to meet complexity requirements")
        
        return hints if hints else ["Continue with current implementation approach"]
    
    def _generate_assignment_title(self, next_assignment: Dict[str, Any]) -> str:
        """Generate assignment title based on assignment type and focus area"""
        assignment_type = next_assignment.get("assignment_type", "correction")
        focus_area = next_assignment.get("focus_area", "general")
        
        title_templates = {
            "advancement": f"Advanced {focus_area.replace('_', ' ').title()} Challenge",
            "reinforcement": f"{focus_area.replace('_', ' ').title()} Reinforcement",
            "correction": f"{focus_area.replace('_', ' ').title()} Correction Task"
        }
        
        return title_templates.get(assignment_type, "Task Assignment")
    
    def _add_convergence_metadata(self, result: Dict[str, Any], supporting_signals: Dict[str, Any]) -> Dict[str, Any]:
        """Add convergence metadata to final result"""
        converged_result = result.copy()
        
        converged_result["convergence_metadata"] = {
            "orchestrator": "final_convergence",
            "hierarchy_enforced": True,
            "assignment_engine": "SINGLE_AUTHORITY",
            "signal_evaluation": "SUPPORTING",
            "validation_layer": "FINAL_WRAPPER",
            "convergence_timestamp": datetime.now().isoformat(),
            "authority_hierarchy": self.authority_hierarchy,
            "signal_authority_level": supporting_signals.get("signal_authority", "unknown"),
            "no_parallel_paths": True
        }
        
        return converged_result

# Global final convergence orchestrator
final_convergence = FinalConvergenceOrchestrator()