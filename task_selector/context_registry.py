"""
Parikshak Context Registry — Phase 1 + Phase 2 + Phase 6
Loads the BHIV product registry from a versioned JSON file.

BOUNDARY RULES:
  - Static registry only — no dynamic updates at runtime
  - No learning, no inference, no LLM calls
  - Same product_id always returns same context (deterministic)
  - Registry is versioned and editable via context_registry.json
"""
import json
import os
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
import logging

logger = logging.getLogger("context_registry")

_REGISTRY_PATH = os.path.join(os.path.dirname(__file__), "context_registry.json")


# ── Context schema (Phase 1) ──────────────────────────────────────────────

@dataclass
class ProductContext:
    """
    Phase 1 context schema — exactly as specified.
    Immutable once loaded from registry.
    """
    product: str
    layer: str
    subsystem: str
    role: str
    tantra_layers: List[str]
    keywords: List[str]
    dependencies: List[str]
    allowed_next_tasks: List[str]
    difficulty_levels: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "product":            self.product,
            "layer":              self.layer,
            "subsystem":          self.subsystem,
            "role":               self.role,
            "tantra_layers":      self.tantra_layers,
            "keywords":           self.keywords,
            "dependencies":       self.dependencies,
            "allowed_next_tasks": self.allowed_next_tasks,
            "difficulty_levels":  self.difficulty_levels,
        }


# ── Registry loader ───────────────────────────────────────────────────────

class ContextRegistry:
    """
    Loads and exposes the BHIV product registry.
    Read-only at runtime — all mutations go through context_registry.json.
    """

    def __init__(self, registry_path: str = _REGISTRY_PATH):
        self._path = registry_path
        self._data: Dict[str, Any] = {}
        self._products: Dict[str, ProductContext] = {}
        self._load()

    def _load(self) -> None:
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                self._data = json.load(f)
            for pid, pdata in self._data.get("products", {}).items():
                self._products[pid] = ProductContext(
                    product=pdata["product"],
                    layer=pdata["layer"],
                    subsystem=pdata["subsystem"],
                    role=pdata["role"],
                    tantra_layers=pdata.get("tantra_layers", []),
                    keywords=pdata.get("keywords", []),
                    dependencies=pdata.get("dependencies", []),
                    allowed_next_tasks=pdata.get("allowed_next_tasks", []),
                    difficulty_levels=pdata.get("difficulty_levels", []),
                )
            logger.info(
                f"[CONTEXT REGISTRY] Loaded v{self._data.get('version', '?')} "
                f"— {len(self._products)} products"
            )
        except Exception as e:
            logger.error(f"[CONTEXT REGISTRY] Failed to load registry: {e}")
            self._products = {}

    # ── Public API ────────────────────────────────────────────────────────

    def get_product(self, product_id: str) -> Optional[ProductContext]:
        """Return ProductContext for a product_id. None if not found."""
        return self._products.get(product_id.lower())

    def get_all_products(self) -> Dict[str, ProductContext]:
        """Return all registered products."""
        return dict(self._products)

    def get_layer_products(self, layer: str) -> List[str]:
        """Return all product_ids belonging to a TANTRA layer."""
        layer_data = self._data.get("tantra_layers", {}).get(layer.lower(), {})
        return layer_data.get("products", [])

    def get_version(self) -> str:
        return self._data.get("version", "unknown")

    def get_default_product(self) -> str:
        return self._data.get("default_product", "parikshak")

    def get_default_layer(self) -> str:
        return self._data.get("default_layer", "execution")

    def list_product_ids(self) -> List[str]:
        return list(self._products.keys())


# Global instance — loaded once at startup
context_registry = ContextRegistry()
