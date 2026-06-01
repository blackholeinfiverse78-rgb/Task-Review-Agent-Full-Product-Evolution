"""
Review Packet Parser — Phase 1 Hard Gate (v2)
Fixes all 7 evaluation gaps:
  1. Structure-aware header detection (## heading only, not paragraph text)
  2. Strict header validation (exact ## pattern, not substring match)
  3. Section quality validation (min words + required sub-elements per section)
  4. Strict JSON parsing (fenced block only, no greedy regex fallback)
  5. output_sample schema validation against required contract keys
  6. Section ordering enforcement (must appear in spec order)
  7. Confidence + validation_depth signal returned in parsed result
"""
import os
import re
import json
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
import logging

logger = logging.getLogger("review_packet_parser")

# ── Spec constants ────────────────────────────────────────────────────────

# Required sections in EXACT order
REQUIRED_SECTIONS: List[str] = [
    "ENTRY POINT",
    "CORE FLOW",
    "LIVE FLOW",
    "OUTPUT SAMPLE",
]

# Minimum word count per section body (after stripping header line)
SECTION_MIN_WORDS: Dict[str, int] = {
    "ENTRY POINT":   10,
    "CORE FLOW":     30,
    "LIVE FLOW":     20,
    "OUTPUT SAMPLE":  5,   # JSON block counts as words
}

# Required sub-elements per section (at least one must be present)
SECTION_REQUIRED_ELEMENTS: Dict[str, List[str]] = {
    "ENTRY POINT":   ["file", "route", "endpoint", "app", "main", "api"],
    "CORE FLOW":     ["step", "->", "pipeline", "flow", "engine", "gate", "rule"],
    "LIVE FLOW":     ["endpoint", "request", "response", "submit", "post", "get", "http"],
    "OUTPUT SAMPLE": ["{", "evaluation_result", "failure_type", "trace_id"],
}

# Required keys in output_sample JSON
OUTPUT_SAMPLE_REQUIRED_KEYS: List[str] = [
    "evaluation_result",
    "failure_type",
    "trace_id",
]

# Header pattern: ## followed by the section name (case-insensitive)
# Must be at start of line, not inside paragraph
_HEADER_PATTERN = re.compile(
    r"^#{1,3}\s+(.+)$",
    re.MULTILINE
)


# ── Data model ────────────────────────────────────────────────────────────

@dataclass
class SectionValidation:
    name: str
    found: bool
    is_proper_header: bool       # appeared as ## heading, not paragraph text
    body_word_count: int
    meets_min_words: bool
    has_required_elements: bool
    missing_elements: List[str]
    order_position: int          # actual position in file (-1 if not found)
    order_correct: bool          # matches expected spec order


@dataclass
class ReviewPacketData:
    """Fully validated, structured parsed object from REVIEW_PACKET.md"""
    entry_point: str
    core_flow: str
    live_flow: str
    output_sample: Dict[str, Any]
    raw_content: str

    # Validation signals
    sections_found: List[str]
    section_validations: List[SectionValidation]
    output_sample_valid: bool
    output_sample_missing_keys: List[str]
    ordering_correct: bool
    validation_depth: str        # "full" | "partial" | "minimal"
    confidence: float            # 0.0–1.0 — how trustworthy the parsed data is
    validation_warnings: List[str]


# ── Parser ────────────────────────────────────────────────────────────────

class ReviewPacketParser:
    """
    Phase 1 Hard Gate — structure-aware REVIEW_PACKET.md enforcement.
    All 7 evaluation gaps addressed.
    """

    def __init__(self, packet_path: str = "REVIEW_PACKET.md"):
        self.packet_path = packet_path
        self.required_sections = REQUIRED_SECTIONS

    # ── Public entry point ────────────────────────────────────────────────

    def enforce_packet_requirement(self, project_root: str) -> Dict[str, Any]:
        """
        Hard gate. Returns dict with valid=True/False.
        On valid=True also returns confidence, validation_depth, warnings.
        """
        # Resolve relative to this file's directory (project root) so it works
        # regardless of the process CWD (local vs Render/Docker deployment).
        _this_dir = os.path.dirname(os.path.abspath(__file__))
        _repo_root = os.path.dirname(_this_dir)
        packet_file = os.path.join(_repo_root, self.packet_path)
        # Fallback to caller-supplied root if the above doesn't exist
        if not os.path.exists(packet_file):
            packet_file = os.path.join(project_root, self.packet_path)

        # Gate 1: file exists
        if not os.path.exists(packet_file):
            return self._reject("REVIEW_PACKET.md file missing",
                                required_action="Create REVIEW_PACKET.md with sections: "
                                + ", ".join(REQUIRED_SECTIONS))

        # Gate 2: readable + non-trivially short
        try:
            with open(packet_file, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            return self._reject(f"REVIEW_PACKET.md unreadable: {e}")

        if len(content.strip()) < 50:
            return self._reject("REVIEW_PACKET.md is empty or too short (< 50 chars)")

        # Gate 3: all required sections present as proper ## headers
        header_check = self._check_headers(content)
        if not header_check["all_present"]:
            return self._reject(
                f"Missing required section headers: {', '.join(header_check['missing'])}",
                missing_sections=header_check["missing"],
                detail="Sections must appear as markdown headers (## SECTION NAME), "
                       "not inside paragraph text"
            )

        if header_check["malformed"]:
            return self._reject(
                f"Sections found in paragraph text but not as proper headers: "
                f"{', '.join(header_check['malformed'])}",
                malformed_sections=header_check["malformed"],
                detail="Each section must start with ## at the beginning of a line"
            )

        # Gate 4: section ordering
        ordering = self._check_ordering(content)
        if not ordering["correct"]:
            return self._reject(
                f"Section ordering violation: expected {REQUIRED_SECTIONS}, "
                f"got {ordering['actual_order']}",
                expected_order=REQUIRED_SECTIONS,
                actual_order=ordering["actual_order"]
            )

        # Gate 5: section quality (min words + required elements)
        quality = self._check_section_quality(content)
        failing_quality = [sv for sv in quality if not sv.meets_min_words or not sv.has_required_elements]
        if failing_quality:
            reasons = []
            for sv in failing_quality:
                if not sv.meets_min_words:
                    reasons.append(
                        f"{sv.name}: too short ({sv.body_word_count} words, "
                        f"min {SECTION_MIN_WORDS[sv.name]})"
                    )
                if not sv.has_required_elements:
                    reasons.append(
                        f"{sv.name}: missing required elements: "
                        f"{', '.join(sv.missing_elements)}"
                    )
            return self._reject(
                f"Section quality failure: {'; '.join(reasons)}",
                quality_failures=reasons
            )

        # Gate 6: parse + output_sample schema validation
        try:
            parsed = self._parse(content, quality)
        except Exception as e:
            return self._reject(f"Packet parse failed: {e}")

        if not parsed.output_sample_valid:
            return self._reject(
                f"OUTPUT SAMPLE JSON missing required contract keys: "
                f"{', '.join(parsed.output_sample_missing_keys)}",
                missing_output_keys=parsed.output_sample_missing_keys,
                detail=f"OUTPUT SAMPLE must contain: {OUTPUT_SAMPLE_REQUIRED_KEYS}"
            )

        logger.info(
            f"[PACKET] Validated — depth={parsed.validation_depth} "
            f"confidence={parsed.confidence:.2f} "
            f"warnings={len(parsed.validation_warnings)}"
        )

        return {
            "valid":            True,
            "parsed_data":      parsed,
            "content_length":   len(content),
            "sections_found":   parsed.sections_found,
            "validation_depth": parsed.validation_depth,
            "confidence":       parsed.confidence,
            "warnings":         parsed.validation_warnings,
        }

    # ── Gate 3: structure-aware header detection ──────────────────────────

    def _check_headers(self, content: str) -> Dict[str, Any]:
        """
        Detect which required sections appear as proper ## headers
        vs. only in paragraph text (malformed).
        """
        # Extract all actual markdown headers
        actual_headers = {
            m.group(1).strip().upper()
            for m in _HEADER_PATTERN.finditer(content)
        }

        content_upper = content.upper()

        present_as_header  = []
        present_in_text    = []  # in content but NOT as a header
        missing            = []
        malformed          = []

        for section in self.required_sections:
            in_header = any(section in h for h in actual_headers)
            in_text   = section in content_upper

            if in_header:
                present_as_header.append(section)
            elif in_text:
                # Found in content but not as a proper header
                present_in_text.append(section)
                malformed.append(section)
            else:
                missing.append(section)

        return {
            "all_present": len(missing) == 0 and len(malformed) == 0,
            "present_as_header": present_as_header,
            "missing": missing,
            "malformed": malformed,
        }

    # ── Gate 4: ordering enforcement ─────────────────────────────────────

    def _check_ordering(self, content: str) -> Dict[str, Any]:
        """
        Verify required sections appear in the correct spec order.
        """
        positions = {}
        for m in _HEADER_PATTERN.finditer(content):
            header_upper = m.group(1).strip().upper()
            for section in self.required_sections:
                if section in header_upper and section not in positions:
                    positions[section] = m.start()

        # Build actual order list
        actual_order = sorted(
            [s for s in self.required_sections if s in positions],
            key=lambda s: positions[s]
        )

        correct = actual_order == self.required_sections

        return {
            "correct":      correct,
            "actual_order": actual_order,
            "positions":    positions,
        }

    # ── Gate 5: section quality ───────────────────────────────────────────

    def _check_section_quality(self, content: str) -> List[SectionValidation]:
        """
        For each required section, validate:
        - minimum word count in body
        - presence of at least one required sub-element
        """
        ordering = self._check_ordering(content)
        positions = ordering["positions"]
        sorted_sections = sorted(
            [s for s in self.required_sections if s in positions],
            key=lambda s: positions[s]
        )

        validations = []
        for i, section in enumerate(self.required_sections):
            if section not in positions:
                validations.append(SectionValidation(
                    name=section, found=False, is_proper_header=False,
                    body_word_count=0, meets_min_words=False,
                    has_required_elements=False,
                    missing_elements=SECTION_REQUIRED_ELEMENTS.get(section, []),
                    order_position=-1, order_correct=False
                ))
                continue

            # Extract body: from this header to next header
            body = self._extract_section_body(content, section, positions, sorted_sections)
            body_lower = body.lower()
            word_count = len(body.split())
            min_words  = SECTION_MIN_WORDS.get(section, 10)

            required_els = SECTION_REQUIRED_ELEMENTS.get(section, [])
            missing_els  = [el for el in required_els if el.lower() not in body_lower]
            has_elements = len(missing_els) < len(required_els)  # at least one present

            actual_pos   = sorted_sections.index(section) if section in sorted_sections else -1
            order_correct = actual_pos == i

            validations.append(SectionValidation(
                name=section,
                found=True,
                is_proper_header=True,
                body_word_count=word_count,
                meets_min_words=word_count >= min_words,
                has_required_elements=has_elements,
                missing_elements=missing_els,
                order_position=actual_pos,
                order_correct=order_correct
            ))

        return validations

    def _extract_section_body(
        self,
        content: str,
        section: str,
        positions: Dict[str, int],
        sorted_sections: List[str]
    ) -> str:
        """Extract body text of a section (between its header and the next header)."""
        start_pos = positions.get(section, -1)
        if start_pos == -1:
            return ""

        # Move past the header line
        newline = content.find("\n", start_pos)
        if newline == -1:
            return ""
        body_start = newline + 1

        # Find next section header position
        idx = sorted_sections.index(section) if section in sorted_sections else -1
        if idx == -1 or idx + 1 >= len(sorted_sections):
            body_end = len(content)
        else:
            next_section = sorted_sections[idx + 1]
            body_end = positions.get(next_section, len(content))

        return content[body_start:body_end].strip()

    # ── Gate 6: parse + JSON schema validation ────────────────────────────

    def _parse(self, content: str, quality: List[SectionValidation]) -> ReviewPacketData:
        ordering  = self._check_ordering(content)
        positions = ordering["positions"]
        sorted_sections = sorted(
            [s for s in self.required_sections if s in positions],
            key=lambda s: positions[s]
        )

        entry_point   = self._extract_section_body(content, "ENTRY POINT",   positions, sorted_sections)
        core_flow     = self._extract_section_body(content, "CORE FLOW",     positions, sorted_sections)
        live_flow     = self._extract_section_body(content, "LIVE FLOW",     positions, sorted_sections)
        output_raw    = self._extract_section_body(content, "OUTPUT SAMPLE", positions, sorted_sections)

        # Strict JSON: fenced block only
        output_sample, json_error = self._parse_json_strict(output_raw)

        # Schema validation
        missing_keys = [k for k in OUTPUT_SAMPLE_REQUIRED_KEYS if k not in output_sample]
        output_valid = len(missing_keys) == 0

        # Confidence + validation_depth calculation
        confidence, depth, warnings = self._calculate_confidence(
            quality, output_valid, missing_keys, json_error, ordering["correct"]
        )

        return ReviewPacketData(
            entry_point=entry_point,
            core_flow=core_flow,
            live_flow=live_flow,
            output_sample=output_sample,
            raw_content=content,
            sections_found=[sv.name for sv in quality if sv.found],
            section_validations=quality,
            output_sample_valid=output_valid,
            output_sample_missing_keys=missing_keys,
            ordering_correct=ordering["correct"],
            validation_depth=depth,
            confidence=confidence,
            validation_warnings=warnings,
        )

    def _parse_json_strict(self, text: str) -> Tuple[Dict[str, Any], Optional[str]]:
        """
        Strict JSON extraction — fenced ```json block only.
        No greedy {.*} regex fallback.
        Returns (parsed_dict, error_message_or_None).
        """
        # Try ```json ... ``` block first
        match = re.search(r"```json\s*\n(.*?)\n```", text, re.DOTALL | re.IGNORECASE)
        if not match:
            # Try ``` ... ``` without language tag
            match = re.search(r"```\s*\n(\{.*?\})\s*\n```", text, re.DOTALL)

        if match:
            raw = match.group(1).strip()
            try:
                return json.loads(raw), None
            except json.JSONDecodeError as e:
                return {}, f"JSON parse error in fenced block: {e}"

        return {}, "No fenced JSON code block found in OUTPUT SAMPLE"

    # ── Confidence + validation_depth ────────────────────────────────────

    def _calculate_confidence(
        self,
        quality: List[SectionValidation],
        output_valid: bool,
        missing_keys: List[str],
        json_error: Optional[str],
        ordering_correct: bool
    ) -> Tuple[float, str, List[str]]:
        """
        Calculate confidence (0.0–1.0) and validation_depth.
        Returns (confidence, depth, warnings).
        """
        warnings = []
        score = 1.0

        # Ordering
        if not ordering_correct:
            score -= 0.05
            warnings.append("Section ordering does not match spec — may indicate copy-paste structure")

        # Per-section quality
        for sv in quality:
            if not sv.found:
                score -= 0.20
                warnings.append(f"{sv.name}: section not found")
                continue
            if not sv.meets_min_words:
                score -= 0.08
                warnings.append(
                    f"{sv.name}: body too short ({sv.body_word_count} words, "
                    f"min {SECTION_MIN_WORDS[sv.name]})"
                )
            if not sv.has_required_elements:
                score -= 0.06
                warnings.append(
                    f"{sv.name}: missing expected elements: {', '.join(sv.missing_elements)}"
                )

        # JSON / output_sample
        if json_error:
            score -= 0.10
            warnings.append(f"OUTPUT SAMPLE: {json_error}")
        elif not output_valid:
            score -= 0.08
            warnings.append(f"OUTPUT SAMPLE missing contract keys: {missing_keys}")

        confidence = round(max(0.0, min(1.0, score)), 3)

        if confidence >= 0.90:
            depth = "full"
        elif confidence >= 0.70:
            depth = "partial"
        else:
            depth = "minimal"

        return confidence, depth, warnings

    # ── Helpers ───────────────────────────────────────────────────────────

    def _reject(self, reason: str, **extra) -> Dict[str, Any]:
        logger.error(f"[PACKET] HARD REJECT — {reason}")
        return {
            "valid":          False,
            "reason":         reason,
            "rejection_type": "HARD_GATE_FAILURE",
            **extra
        }


# Global instance
review_packet_parser = ReviewPacketParser()
