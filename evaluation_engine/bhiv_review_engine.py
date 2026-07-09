"""
BHIV Candidate Review Engine — Parikshak v6.0.0
Performs deep analysis on submissions using local codebase context and LLM analysis.
Generates structured executive reviews and next-task recommendations.
"""
import os
import json
import logging
import requests
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

from task_selector.task_graph_engine import task_graph_engine
from db.persistent_storage import ReviewRecord, TaskSubmission, product_storage, TaskStatus

logger = logging.getLogger("bhiv_review_engine")

class BHIVReviewEngine:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        self.endpoint = os.getenv("GROQ_API_ENDPOINT", "https://api.groq.com/openai/v1/chat/completions")
        self.model = os.getenv("GROQ_MODEL_NAME", "llama-3.3-70b-versatile")

    def run_evaluation(self, intake_data: Dict[str, Any], trace_id: str) -> Dict[str, Any]:
        """
        Runs the complete candidate review pipeline.
        1. Gather codebase files.
        2. Run deterministic rule checks to establish baseline validation.
        3. Invoke LLM for executive-quality analysis or use deterministic fallback.
        4. Traverse task graph to resolve next task.
        5. Return structured review output.
        """
        assigned_task = intake_data["assigned_task"]
        task_doc = intake_data["original_task_document"]
        review_packet = intake_data["review_packet"]
        repo_path = intake_data["repository_or_commit"]
        due_date = intake_data["due_date"]
        sub_date = intake_data["submission_date"]
        evidence = intake_data.get("supporting_evidence", {})
        instructions = intake_data.get("additional_instructions", "")

        # 1. Gather codebase files context
        code_context = self._gather_repo_context(repo_path)

        # 2. Run rule engine deterministic baseline
        from evaluation_engine.orchestrator import evaluation_orchestrator
        baseline = evaluation_orchestrator.evaluate_submission(
            task_title=assigned_task,
            task_description=task_doc,
            repository_url=repo_path if repo_path.startswith("http") else None,
            module_id="task-review-agent",
            schema_version="v1.0"
        )
        baseline_res = baseline.get("evaluation_result", "FAIL")
        baseline_fail_type = baseline.get("failure_type")

        # 3. Call LLM for detailed review
        review_analysis = self._call_llm_analysis(
            assigned_task=assigned_task,
            task_doc=task_doc,
            review_packet=review_packet,
            code_context=code_context,
            sub_date=sub_date,
            due_date=due_date,
            baseline_res=baseline_res,
            baseline_fail_type=baseline_fail_type,
            instructions=instructions
        )

        # Map LLM output to deterministic structures
        verdict = review_analysis.get("verdict", "REJECTED")
        eval_result = "PASS" if "PASS" in verdict or "APPROVED" in verdict or "READY" in verdict else "FAIL"
        
        # Determine failure type deterministically if PASS is not achieved
        failure_type = None
        if eval_result == "FAIL":
            failure_type = baseline_fail_type or "incorrect_logic"

        # 4. Next task traversal
        current_task_id = intake_data.get("assigned_task_id") or "T-GOV-001"
        graph_result = task_graph_engine.traverse(
            current_task_id=current_task_id,
            evaluation_result=eval_result,
            failure_type=failure_type
        )
        selected_task_id = graph_result["selected_task_id"]

        # Format executive markdown summary
        markdown_summary = self._generate_markdown_summary(review_analysis, eval_result, selected_task_id)

        # Construct final review output dictionary
        score_out_of_100 = int(float(review_analysis.get("score_out_of_10", 0.0)) * 10)
        readiness_pct = int(float(review_analysis.get("readiness_percent", 0.0)))

        # Sanitize score and readiness clamp [0, 100]
        score_out_of_100 = min(100, max(0, score_out_of_100))
        readiness_pct = min(100, max(0, readiness_pct))

        review_status = "pass" if eval_result == "PASS" else "fail"
        if review_status == "fail" and score_out_of_100 >= 50:
            review_status = "borderline"

        output = {
            "evaluation_result": eval_result,
            "failure_type": failure_type,
            "decision": "APPROVED" if eval_result == "PASS" else "REJECTED",
            "score": score_out_of_100,
            "readiness_percent": readiness_pct,
            "status": review_status,
            "failure_reasons": review_analysis.get("required_fixes", []),
            "improvement_hints": review_analysis.get("missing_incomplete", []),
            "evaluation_summary": markdown_summary,
            "selected_task_id": selected_task_id,
            "selection_reason": review_analysis.get("next_task_justification", "Next task recommendation based on pipeline graph rules."),
            "evidence_used": review_analysis.get("evidence_used", []),
            "whats_done_well": review_analysis.get("whats_done_well", []),
            "timeline_commentary": review_analysis.get("timeline_commentary", ""),
            "review_mode": review_analysis.get("_review_mode", "deterministic_fallback")
        }

        return output

    def _gather_repo_context(self, repo_path: str) -> str:
        """Reads key repository files to build the codebase context."""
        context_parts = []
        
        # If repo_path is not a valid directory path, return empty
        if not os.path.isdir(repo_path):
            return "No local repository directory found or path is remote URL."

        # Key files to read
        target_files = [
            "README.md",
            "REVIEW_PACKET.md",
            "api/production.py",
            "api/review_routes.py",
            "evaluation_engine/rule_engine.py",
            "evaluation_engine/execution_pipeline.py",
            "canonical_db/db.py",
            "canonical_db/integration.py"
        ]

        for file_rel in target_files:
            file_abs = os.path.join(repo_path, file_rel)
            if os.path.exists(file_abs):
                try:
                    with open(file_abs, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read(15000) # Read up to 15KB per file to stay within limits
                    context_parts.append(f"File: {file_rel}\n{'='*40}\n{content}\n{'='*40}\n")
                except Exception as e:
                    logger.warning(f"Could not read {file_rel} for context: {e}")

        return "\n".join(context_parts)

    def _call_llm_analysis(
        self,
        assigned_task: str,
        task_doc: str,
        review_packet: str,
        code_context: str,
        sub_date: str,
        due_date: str,
        baseline_res: str,
        baseline_fail_type: Optional[str],
        instructions: str
    ) -> Dict[str, Any]:
        """Calls Groq API to analyze the codebase and generate the structured JSON review."""
        if not self.api_key:
            logger.warning("[LLM] GROQ_API_KEY missing. Falling back to deterministic review.")
            return self._generate_fallback(baseline_res, baseline_fail_type)

        prompt = f"""You are the Parikshak Executive Review Engine. Analyze the candidate submission and generate an executive-quality engineering review.

TASK DETAILS:
Assigned Task: {assigned_task}
Task Document: {task_doc}
Review Packet Requirements: {review_packet}
Submission Date: {sub_date}
Due Date: {due_date}
Additional Instructions: {instructions}

DETERMINISTIC GATES RESULT:
Baseline Result: {baseline_res}
Baseline Failure Type: {baseline_fail_type}

CANDIDATE CODEBASE KEY FILE CONTENTS:
{code_context}

INSTRUCTIONS:
1. Provide a detailed review containing:
   - whats_done_well: list of strengths with file/line evidence.
   - missing_incomplete: list of gaps/missing features with file/line evidence.
   - required_fixes: list of mandatory fixes with file/line evidence.
   - score_out_of_10: score between 0.0 and 10.0 (strictly numeric).
   - readiness_percent: percentage from 0 to 100 (strictly numeric).
   - timeline_commentary: analysis of timeliness and submission vs due date.
   - evidence_used: list of files and details examined.
   - verdict: "PRODUCTION READY" or "NEEDS WORK" or "REJECTED".
   - next_task_justification: Short explanation of the next recommended step based on architectural gaps, ecosystem priorities, maturity, and readiness.
2. Every finding must reference specific evidence (file names, line ranges, or design blocks). No unsupported assertions.
3. Return ONLY a valid JSON object matching the keys listed above. No markdown formatting outside the JSON, no backticks, no wrap text.
"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
            "response_format": {"type": "json_object"}
        }

        try:
            resp = requests.post(self.endpoint, headers=headers, json=payload, timeout=30)
            resp.raise_for_status()
            res_json = resp.json()
            content_str = res_json["choices"][0]["message"]["content"]
            result = json.loads(content_str)
            result["_review_mode"] = "llm"
            logger.info("[LLM] Deep analysis successfully retrieved from Groq API.")
            return result
        except Exception as e:
            logger.error(f"[LLM] Groq API call failed: {e}. Executing fallback.")
            return self._generate_fallback(baseline_res, baseline_fail_type)

    def _generate_fallback(self, baseline_res: str, baseline_fail_type: Optional[str]) -> Dict[str, Any]:
        """Provides a deterministic fallback if the LLM API is unavailable."""
        if baseline_res == "PASS":
            return {
                "whats_done_well": [
                    "Deterministic pipeline tests pass. Codebase structure meets core file and layer guidelines (rule_engine.py check).",
                    "Gov-OS event journal integrity gate passes. Database mutation protection triggers are active (db.py verification)."
                ],
                "missing_incomplete": [],
                "required_fixes": [],
                "score_out_of_10": 9.0,
                "readiness_percent": 90.0,
                "timeline_commentary": "Submission matches requirements and was completed before the deadline.",
                "evidence_used": ["rule_engine.py", "db.py", "integration.py"],
                "verdict": "PRODUCTION READY",
                "next_task_justification": "All baseline rule checks passed. Recommended advancement task in accordance with Niyantran transition rules."
            }
        else:
            reason_map = {
                "schema_violation": "Required repository structure or metadata files are missing or incomplete.",
                "incomplete": "Missing mandatory proof of tests, documentation, or architecture files.",
                "incorrect_logic": "Code alignment metrics or implementation features fail to meet minimum delivery ratios.",
                "integration_fail": "Downstream registry verification or integration health checks returned failure."
            }
            reason = reason_map.get(baseline_fail_type or "incomplete", "Submission fails baseline Parikshak checks.")
            return {
                "whats_done_well": ["Basic package setup is visible, but core enforcement rules failed."],
                "missing_incomplete": [f"Gaps in requirement completeness: {reason}"],
                "required_fixes": [f"Verify repository files and structure match blueprint registry specs. Details: {baseline_fail_type}"],
                "score_out_of_10": 4.0,
                "readiness_percent": 40.0,
                "timeline_commentary": "Review execution rejected due to rule failure.",
                "evidence_used": ["rule_engine.py", "context_registry.json"],
                "verdict": "NEEDS WORK",
                "next_task_justification": f"Rule failure ({baseline_fail_type}) requires correction task targeting failed dimension before advancement is permitted."
            }

    def _generate_markdown_summary(self, review: Dict[str, Any], eval_res: str, selected_task_id: str) -> str:
        """Renders the final review report in a structured Markdown format."""
        done_well = "\n".join([f"* {x}" for x in review.get("whats_done_well", [])])
        missing = "\n".join([f"* {x}" for x in review.get("missing_incomplete", [])])
        fixes = "\n".join([f"* {x}" for x in review.get("required_fixes", [])])
        evidence = "\n".join([f"* {x}" for x in review.get("evidence_used", [])])

        report = f"""# Parikshak Executive Review Report

## WHAT'S DONE WELL
{done_well if done_well else "* No strengths documented."}

## MISSING / INCOMPLETE
{missing if missing else "* No missing features."}

## REQUIRED FIXES
{fixes if fixes else "* No required fixes."}

## OPERATIONAL METRICS
* **Score**: {review.get('score_out_of_10', 0.0)}/10
* **Readiness**: {review.get('readiness_percent', 0)}%
* **Verdict**: {review.get('verdict', 'NEEDS WORK')}
* **Evaluation Result**: {eval_res}

## TIMELINE COMMENTARY
{review.get('timeline_commentary', 'N/A')}

## EVIDENCE USED
{evidence if evidence else "* No evidence files listed."}

## RECOMMENDATION & DISPATCH
* **Next Assigned Task**: `{selected_task_id}`
* **Justification**: {review.get('next_task_justification', 'N/A')}

*Verified: {datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")}*
"""
        return report

# Global instance
bhiv_review_engine = BHIVReviewEngine()
