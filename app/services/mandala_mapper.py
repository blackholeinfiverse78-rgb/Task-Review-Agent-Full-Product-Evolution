"""
Parikshak Mandala Mapping Engine — Phase 3
Deterministic task → context mapping.

input  → task_title + task_description
output → ProductContext (product, layer, subsystem, ...)

BOUNDARY RULES:
  - Keyword matching only — no LLM, no ML, no inference
  - Same input ALWAYS produces same context (deterministic)
  - Falls back to default_product if no match found
  - Does NOT modify scoring logic
  - Does NOT bypass Niyantran
"""
from typing import Dict, Any, Optional, Tuple
import logging

from .context_registry import context_registry, ProductContext

logger = logging.getLogger("mandala_mapper")


class MandalaMapper:
    """
    Maps a task to its BHIV product context using keyword scoring.

    Algorithm (deterministic):
      1. Combine task_title + task_description → lowercase text
      2. For each product in registry, count keyword hits in text
      3. Product with highest hit count wins (ties broken by registry order)
      4. If no hits → return default_product context
      5. Same input → same output always
    """

    def map_task_to_context(
        self,
        task_title: str,
        task_description: str
    ) -> Dict[str, Any]:
        """
        Map task to BHIV product context.

        Returns:
            {
              product, layer, subsystem, role,
              tantra_layers, dependencies,
              allowed_next_tasks, difficulty_levels,
              mapping_confidence, matched_keywords, mapping_source
            }
        """
        combined = (task_title + " " + task_description).lower()

        best_product, best_score, matched_kws = self._score_products(combined)

        if best_product is None or best_score == 0:
            logger.error(
                f"[MANDALA] HARD REJECT — no keyword match for input: '{combined[:80]}'"
            )
            raise ValueError(
                "MANDALA_HARD_REJECT: No product context match found. "
                "Submission must contain recognisable product keywords. "
                "No fallback mapping permitted."
            )
        else:
            mapping_source = "keyword_match"
            logger.info(
                f"[MANDALA] Mapped to '{best_product.product}' "
                f"(score={best_score}, keywords={matched_kws[:3]})"
            )

        # mapping_confidence: fraction of product keywords matched (0.0–1.0)
        total_kws = len(best_product.keywords) if best_product.keywords else 1
        mapping_confidence = round(min(best_score / total_kws, 1.0), 3)

        return {
            **best_product.to_dict(),
            "mapping_confidence": mapping_confidence,
            "matched_keywords":   matched_kws,
            "mapping_source":     mapping_source,
        }

    def get_context_for_product(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Direct lookup by product_id. Returns None if not found."""
        ctx = context_registry.get_product(product_id)
        if ctx is None:
            return None
        return {
            **ctx.to_dict(),
            "mapping_confidence": 1.0,
            "matched_keywords":   [],
            "mapping_source":     "direct_lookup",
        }

    # ── Private ───────────────────────────────────────────────────────────

    def _score_products(
        self, text: str
    ) -> Tuple[Optional[ProductContext], int, list]:
        """
        Score all products by keyword hits in text.
        Returns (best_product, best_score, matched_keywords).
        Deterministic: ties broken by registry insertion order.
        """
        best_product: Optional[ProductContext] = None
        best_score = 0
        best_matched: list = []

        for pid, product in context_registry.get_all_products().items():
            matched = [kw for kw in product.keywords if kw in text]
            score = len(matched)
            if score > best_score:
                best_score = score
                best_product = product
                best_matched = matched

        return best_product, best_score, best_matched


# Global instance
mandala_mapper = MandalaMapper()
