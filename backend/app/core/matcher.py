"""
Matching engine.

The normalizer turns a raw listing into a NormalizedProduct.
The matcher decides: "is this the same canonical product as one we already have?"

We do this in tiers and assign a confidence score:

    1.00  EXACT     same category + brand + (size value & unit) + loose flag
    0.85  BRAND     same category + brand + same size-bucket but different sub-spelling
    0.70  CATEGORY  same category + subcategory + same size-bucket (no brand match)
    0.55  LOOSE     loose-goods bucket (sugar/rice without packaging, sized in kg)
    < 0.55          weak text similarity fallback (trigram); not auto-linked

The "size bucket" is a small tolerance window in base units (ml/g/pcs) so that
"5L" and "5000ml" listings collapse, and "1kg" / "1000g" likewise.
"""

from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Optional, Sequence

from .normalizer import NormalizedProduct


# Tolerance for "same size" — store sizes are typically exact, but allow 2%
# slop for human-reported weights (e.g. rice 1000g vs 998g).
SIZE_TOLERANCE = 0.02


@dataclass
class MatchResult:
    product_id: Optional[int]
    confidence: float
    method: str        # "exact" | "brand" | "category" | "loose" | "unmatched"
    reason: str        # short, human-readable, used in /products debug output


class CandidateProduct:
    """Lightweight view of a canonical product row used during matching.

    We pass a Sequence[CandidateProduct] into match() so the matcher is
    storage-agnostic (the tests can hand it a list; production hands it
    a result set from Postgres).
    """
    __slots__ = ("id", "normalized_name", "brand", "category", "subcategory",
                 "size_value", "size_unit", "base_unit_qty", "is_loose")

    def __init__(self, id, normalized_name, brand, category, subcategory,
                 size_value, size_unit, base_unit_qty, is_loose):
        self.id = id
        self.normalized_name = normalized_name
        self.brand = brand
        self.category = category
        self.subcategory = subcategory
        self.size_value = size_value
        self.size_unit = size_unit
        self.base_unit_qty = base_unit_qty
        self.is_loose = is_loose


def _sizes_equivalent(a: Optional[float], b: Optional[float]) -> bool:
    if a is None or b is None:
        return False
    if a == 0 or b == 0:
        return a == b
    return abs(a - b) / max(a, b) <= SIZE_TOLERANCE


def _name_similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


def match(np: NormalizedProduct, candidates: Sequence[CandidateProduct]) -> MatchResult:
    """Match a NormalizedProduct against canonical candidates.

    `candidates` should already be pre-filtered by category for efficiency
    (in production, the SQL query restricts by category + size_unit family).
    """
    if not np.category:
        return MatchResult(None, 0.0, "unmatched", "no category detected")

    same_cat = [c for c in candidates if c.category == np.category and c.is_loose == np.is_loose]
    if not same_cat:
        return MatchResult(None, 0.0, "unmatched", f"no candidates in category {np.category}")

    # --- Tier 1: EXACT ------------------------------------------------------
    # Subcategory must agree too — otherwise "Fresh Rice Bran Oil 5L" and
    # "Fresh Soybean Oil 5L" collapse, which is wrong: same brand and size,
    # but different products. None==None is fine (e.g. plain "sugar 1kg").
    if np.brand and np.base_unit_qty is not None:
        for c in same_cat:
            if (c.brand == np.brand
                    and c.subcategory == np.subcategory
                    and _sizes_equivalent(c.base_unit_qty, np.base_unit_qty)
                    and c.size_unit == np.size_unit):
                return MatchResult(c.id, 1.00, "exact",
                                   f"brand={np.brand}, sub={np.subcategory}, size={np.size_value}{np.size_unit}")

    # --- Tier 2: BRAND ------------------------------------------------------
    # Same brand + same subcategory + roughly same size, but the size unit
    # family differs (e.g. one listing says 5L, the other says 5000ml).
    if np.brand and np.base_unit_qty is not None:
        for c in same_cat:
            if (c.brand == np.brand
                    and c.subcategory == np.subcategory
                    and _sizes_equivalent(c.base_unit_qty, np.base_unit_qty)):
                return MatchResult(c.id, 0.85, "brand",
                                   f"brand={np.brand}, sub={np.subcategory} (cross-unit size match)")

    # --- Tier 3: CATEGORY ---------------------------------------------------
    # The user (or scraper) didn't pin down a brand match. We'll suggest the
    # canonical at category level — *unless* both sides have brands and they
    # differ. Without this guard, ingest of "Pusti Soybean 5L" would silently
    # latch onto the existing "Rupchanda Soybean 5L" canonical and corrupt
    # brand attribution.
    if np.base_unit_qty is not None:
        for c in same_cat:
            if (c.subcategory == np.subcategory
                    and _sizes_equivalent(c.base_unit_qty, np.base_unit_qty)
                    and not (np.brand and c.brand and np.brand != c.brand)):
                return MatchResult(c.id, 0.70, "category",
                                   f"subcategory={np.subcategory} same size, brand-compatible")

    # --- Tier 4: LOOSE ------------------------------------------------------
    # Loose goods (sugar/rice/dal sold by kg without brand) — anyone selling
    # at the same size in the same subcategory is a fair comparison.
    if np.is_loose and np.base_unit_qty is not None:
        for c in same_cat:
            if c.is_loose and _sizes_equivalent(c.base_unit_qty, np.base_unit_qty):
                return MatchResult(c.id, 0.55, "loose",
                                   "loose goods, same subcat and size")

    # --- Fallback: trigram-style fuzzy name match (low confidence) ----------
    # Same brand-compat guard as the CATEGORY tier.
    best = None
    best_score = 0.0
    for c in same_cat:
        if np.brand and c.brand and np.brand != c.brand:
            continue
        score = _name_similarity(np.normalized_name, c.normalized_name)
        if score > best_score:
            best, best_score = c, score
    if best and best_score >= 0.75 and _sizes_equivalent(best.base_unit_qty, np.base_unit_qty):
        return MatchResult(best.id, 0.50, "category",
                           f"fuzzy name match score={best_score:.2f}")

    return MatchResult(None, 0.0, "unmatched", "no tier matched")
