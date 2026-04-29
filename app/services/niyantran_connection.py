"""
Niyantran Connection Service - Task Orchestration Interface
Accepts tasks from Niyantran and returns review + next task
Ensures end-to-end flow works seamlessly
"""
from typing import Dict, Any, Optional
import logging
from datetime import datetime
from dataclasses import dataclass

from .final_convergence import final_convergence
from .production_decision_engine import production_decision_engine
from .bucket_integration import bucket_integration
from .task_selection_engine import task_selection_engine
from .mandala_mapper import mandala_mapper

logger = logging.getLogger("niyantran_connection")

# Phase 5 — Trace governance constants
_TRACE_ID_FIELD = "trace_id"
_TRACE_ID_MIN_LEN = 8

@dataclass
class NiyantranTask:
    """Task received from Niyantran"""
    task_id: str
    task_title: str
    task_description: str
    submitted_by: str
    repository_url: Optional[str] = None
    module_id: str = "task-review-agent"
    schema_version: str = "v1.0"
    pdf_text: str = ""
    priority: str = "normal"
    deadline: Optional[str] = None
    trace_id: str = ""  # Phase 5: must come from Niyantran
    product_context: Optional[Dict[str, Any]] = None  # Phase 3: injected by Mandala Mapper
    current_task_id: Optional[str] = None  # Gap 1: enables graph traversal when provided by Niyantran
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NiyantranTask":
        """Create NiyantranTask from dictionary. Enforces trace_id presence."""
        trace_id = data.get("trace_id", "").strip()
        if not trace_id or len(trace_id) < _TRACE_ID_MIN_LEN:
            raise ValueError(
                f"[NIYANTRAN] REJECT: trace_id missing or too short "
                f"(got '{trace_id}', min {_TRACE_ID_MIN_LEN} chars). "
                "trace_id must come from Niyantran."
            )
        # Phase 3: map task to BHIV product context via Mandala Mapper
        product_context = mandala_mapper.map_task_to_context(
            data.get("task_title", ""),
            data.get("task_description", "")
        )
        return cls(
            task_id=data.get("task_id", ""),
            task_title=data.get("task_title", ""),
            task_description=data.get("task_description", ""),
            submitted_by=data.get("submitted_by", "unknown"),
            repository_url=data.get("repository_url"),
            module_id=data.get("module_id", "task-review-agent"),
            schema_version=data.get("schema_version", "v1.0"),
            pdf_text=data.get("pdf_text", ""),
            priority=data.get("priority", "normal"),
            deadline=data.get("deadline"),
            trace_id=trace_id,
            product_context=product_context,
            current_task_id=data.get("current_task_id")
        )

@dataclass
class NiyantranResponse:
    """Response to Niyantran with review + next task"""
    task_id: str
    trace_id: str
    
    # Review results
    review: Dict[str, Any]
    
    # Next task assignment
    next_task: Dict[str, Any]
    
    # Processing metadata
    processing_time_ms: int
    timestamp: str
    status: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response"""
        return {
            "task_id": self.task_id,
            "trace_id": self.trace_id,
            "review": self.review,
            "next_task": self.next_task,
            "processing_metadata": {
                "processing_time_ms": self.processing_time_ms,
                "timestamp": self.timestamp,
                "status": self.status
            }
        }

class NiyantranConnectionService:
    """
    Connection service for Niyantran integration
    Handles task intake, processing, and response generation
    """
    
    def __init__(self):
        self.service_name = "niyantran_connection"
        self.version = "1.0"
        
    def process_niyantran_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process task from Niyantran and return complete response
        
        Args:
            task_data: Task data from Niyantran
            
        Returns:
            Complete response with review + next task
        """
        start_time = datetime.now()
        logger.info(f"[NIYANTRAN] Processing task from Niyantran: {task_data.get('task_title', 'Unknown')[:50]}...")
        
        try:
            # Step 1: Parse Niyantran task — enforces trace_id + injects context
            niyantran_task = NiyantranTask.from_dict(task_data)
            trace_id = niyantran_task.trace_id
            product_context = niyantran_task.product_context  # Phase 3
            logger.info(
                f"[NIYANTRAN] Context: product={product_context.get('product')} "
                f"layer={product_context.get('layer')} "
                f"confidence={product_context.get('mapping_confidence')}"
            )

            # Step 2: Execute full evaluation pipeline
            convergence_result = final_convergence.process_with_convergence(
                task_title=niyantran_task.task_title,
                task_description=niyantran_task.task_description,
                repository_url=niyantran_task.repository_url,
                module_id=niyantran_task.module_id,
                schema_version=niyantran_task.schema_version,
                pdf_text=niyantran_task.pdf_text,
                submitted_by=niyantran_task.submitted_by,
                trace_id=trace_id
            )

            # Step 3: Build response directly from convergence output
            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)

            response = NiyantranResponse(
                task_id=niyantran_task.task_id,
                trace_id=trace_id,
                review={
                    "evaluation_result": convergence_result["evaluation_result"],
                    "failure_type":      convergence_result["failure_type"],
                    "decision":          "APPROVED" if convergence_result["evaluation_result"] == "PASS" else "REJECTED",
                    "selected_task_id":  convergence_result["selected_task_id"],
                    "selection_reason":  convergence_result["selection_reason"],
                    "source":            convergence_result["source"],
                },
                next_task={
                    "task_id":          convergence_result["selected_task_id"],
                    "selection_reason": convergence_result["selection_reason"],
                    "source":           convergence_result["source"],
                },
                processing_time_ms=processing_time,
                timestamp=datetime.now().isoformat(),
                status="completed"
            )
            
            logger.info(f"[NIYANTRAN] Task processed successfully: trace_id={trace_id}, decision={decision_result.get('decision')}")
            return response.to_dict()
            
        except Exception as e:
            logger.error(f"[NIYANTRAN] Task processing failed: {e}")
            raise RuntimeError(f"NIYANTRAN_HARD_REJECT: Task processing failed — {e}")
    
    def _execute_evaluation_pipeline(self, niyantran_task: NiyantranTask) -> Dict[str, Any]:
        """Execute the full evaluation pipeline"""
        
        # Use final convergence orchestrator
        convergence_result = final_convergence.process_with_convergence(
            task_title=niyantran_task.task_title,
            task_description=niyantran_task.task_description,
            repository_url=niyantran_task.repository_url,
            module_id=niyantran_task.module_id,
            schema_version=niyantran_task.schema_version,
            pdf_text=niyantran_task.pdf_text
        )
        
        return {
            "evaluation": convergence_result,
            "supporting_signals": convergence_result.get("supporting_signals", {}),
            "packet_data": convergence_result.get("packet_data", {})
        }
    
    def _generate_next_task(
        self, 
        evaluation_result: Dict[str, Any], 
        decision_result: Dict[str, Any],
        niyantran_task: NiyantranTask
    ) -> Dict[str, Any]:
        """Generate next task based on evaluation and decision"""
        
        # Extract next task data from evaluation result
        base_next_task = {
            "next_task_id": evaluation_result.get("next_task_id", f"next-{datetime.now().strftime('%Y%m%d%H%M%S')}"),
            "task_type": decision_result.get("task_type", "correction"),
            "title": evaluation_result.get("title", "Assignment Task"),
            "objective": evaluation_result.get("objective", "Complete assigned task"),
            "focus_area": evaluation_result.get("focus_area", "general"),
            "difficulty": evaluation_result.get("difficulty", "beginner"),
            "reason": evaluation_result.get("reason", "Based on evaluation results")
        }
        
        # Enhance with decision context
        if decision_result.get("decision") == "approve":
            base_next_task["title"] = f"Advanced {base_next_task['focus_area']} Challenge"
            base_next_task["difficulty"] = "advanced"
        elif decision_result.get("decision") == "conditional":
            base_next_task["title"] = f"{base_next_task['focus_area']} Reinforcement Task"
            base_next_task["difficulty"] = "intermediate"
        
        # Add Niyantran-specific fields
        base_next_task.update({
            "assigned_to": niyantran_task.submitted_by,
            "priority": niyantran_task.priority,
            "parent_task_id": niyantran_task.task_id,
            "confidence": decision_result.get("confidence", 0.0),
            "quality_grade": decision_result.get("quality_rubric", {}).get("quality_grade", "D")
        })
        
        return base_next_task
    
    def _format_review_for_niyantran(
        self,
        evaluation_result: Dict[str, Any],
        decision_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        evaluation = evaluation_result.get("evaluation_result")
        failure_type = evaluation_result.get("failure_type")
        decision = decision_result.get("decision")

        if evaluation not in ("PASS", "FAIL"):
            raise ValueError(f"NIYANTRAN_HARD_REJECT: invalid evaluation_result '{evaluation}'")
        if decision not in ("APPROVED", "REJECTED"):
            raise ValueError(f"NIYANTRAN_HARD_REJECT: invalid decision '{decision}'")

        return {
            "evaluation_result":  evaluation,
            "failure_type":       failure_type,
            "decision":           decision,
            "task_type":          decision_result.get("task_type"),
            "pac":                evaluation_result.get("pac", {}),
            "rubric":             evaluation_result.get("rubric", {}),
            "strengths":          decision_result.get("strengths", []),
            "failures":           decision_result.get("failures", []),
            "root_cause":         decision_result.get("root_cause", ""),
            "learning_feedback":  decision_result.get("learning_feedback", []),
            "next_direction":     decision_result.get("next_direction", ""),
            "evaluation_summary": evaluation_result.get("evaluation_summary", ""),
            "canonical_authority": evaluation_result.get("canonical_authority", False),
        }
    
    def _format_next_task_for_niyantran(
        self,
        next_task_result: Dict[str, Any],
        decision_result: Dict[str, Any],
        product_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Format next task for Niyantran — includes product context."""
        return {
            "task_id":            next_task_result.get("next_task_id"),
            "task_type":          next_task_result.get("task_type"),
            "title":              next_task_result.get("title"),
            "difficulty":         next_task_result.get("difficulty"),
            "selection_reason":   next_task_result.get("selection_reason"),
            "source":             next_task_result.get("source"),
            "decision_band":      next_task_result.get("decision_band"),
            "difficulty_band":    next_task_result.get("difficulty_band"),
            # Phase 5: context-aware fields
            "product":            next_task_result.get("product"),
            "layer":              next_task_result.get("layer"),
            "context_source":     next_task_result.get("context_source"),
            # Decision context
            "derived_from_decision": decision_result.get("decision"),
            "approval_threshold_met": decision_result.get("decision_criteria", {}).get("approval_threshold_met", False),
            "evidence_driven":    True,
            # Product context passthrough
            "product_context":    product_context or {},
        }
    
    def health_check(self) -> Dict[str, Any]:
        bucket_stats = bucket_integration.get_bucket_stats()
        return {
            "status":      "healthy",
            "service":     self.service_name,
            "version":     self.version,
            "timestamp":   datetime.now().isoformat(),
            "bucket_stats": bucket_stats
        }

# Global Niyantran connection service
niyantran_connection = NiyantranConnectionService()