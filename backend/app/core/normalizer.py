"""
Product normalization: messy store listing string -> structured product attrs.

A scraped listing on Chaldal might be:
    "Rupchanda Soyabean Oil (5 Litre)"
On Shwapno:
    "Rupchanda Soybean Oil 5L"
On Pandamart:
    "তেল রূপচাঁদা সয়াবিন ৫ লিটার"

The normalizer's job: produce the same NormalizedProduct dict for all three,
so the matcher can group them. It is intentionally NOT smart — every rule is
explicit and easy to read. ML/embeddings live in matcher.py, on top of this.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import asdict, dataclass
from typing import Optional

from .categories import find_brand, find_category, find_subcategory

# --- Bangla numeral & unit translation -------------------------------------

BENGALI_DIGITS = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")

BENGALI_UNIT_TO_EN = {
    "লিটার": "litre",
    "মিলি":  "ml",
    "কেজি":  "kg",
    "গ্রাম": "g",
    "টা":    "pcs",
    "টি":    "pcs",
    "পিস":   "pcs",
    "প্যাকেট": "pack",
    "ডজন":   "dozen",
}

# Unit canonicalization. We always normalize to ml / g / pcs for math.
UNIT_ALIASES = {
    "l":      ("L",   1000.0),
    "lt":     ("L",   1000.0),
    "ltr":    ("L",   1000.0),
    "litre":  ("L",   1000.0),
    "litres": ("L",   1000.0),
    "liter":  ("L",   1000.0),
    "liters": ("L",   1000.0),
    "ml":     ("ML",  1.0),
    "milliliter":  ("ML", 1.0),
    "milliliters": ("ML", 1.0),
    "kg":     ("KG",  1000.0),
    "kgs":    ("KG",  1000.0),
    "kilogram":  ("KG", 1000.0),
    "kilograms": ("KG", 1000.0),
    "g":      ("G",   1.0),
    "gm":     ("G",   1.0),
    "gms":    ("G",   1.0),
    "gram":   ("G",   1.0),
    "grams":  ("G",   1.0),
    "pc":     ("PCS", 1.0),
    "pcs":    ("PCS", 1.0),
    "piece":  ("PCS", 1.0),
    "pieces": ("PCS", 1.0),
}

# When the count is "1 dozen", convert.
COUNT_WORDS = {"dozen": ("PCS", 12.0), "ডজন": ("PCS", 12.0)}


# --- Regexes ---------------------------------------------------------------

# Captures things like: "5 L", "500ml", "1.5 kg", "12 pcs", "১ লিটার"
_SIZE_RE = re.compile(
    r"""
    (?P<value>\d+(?:[.,]\d+)?)        # number, allow decimal w/ . or ,
    \s*
    (?P<unit>
        litres?|liters?|ltrs?|ltr|lt|l |
        millilit(?:re|er)s?|ml |
        kgs?|kilograms?|kg |
        grams?|gms?|gm|g |
        pieces?|pcs?|pc |
        dozen
    )\b
    """,
    re.IGNORECASE | re.VERBOSE,
)

# Strip the typical noise tokens stores tack onto names
_NOISE_RE = re.compile(
    r"\b(?:premium|imported|local|new|special|combo|offer|pack of \d+|family pack|"
    r"value pack|economy pack|jar|bottle|pouch|tin|can|polybag|polythene)\b",
    re.IGNORECASE,
)
_PUNCT_RE = re.compile(r"[()\[\]\"'.,;:/\\!?]")
_MULTI_SPACE_RE = re.compile(r"\s+")


@dataclass
class NormalizedProduct:
    """Structured view of a noisy store listing."""
    raw_name: str
    normalized_name: str         # the cleaned, lowercased, deduped name w/o size
    category: Optional[str]
    subcategory: Optional[str]
    brand: Optional[str]
    size_value: Optional[float]
    size_unit: Optional[str]     # canonical: L, ML, KG, G, PCS
    base_unit_qty: Optional[float]   # quantity in base unit (ml/g/pcs) for per-unit math
    is_loose: bool

    def to_dict(self) -> dict:
        return asdict(self)


def _translate_bangla(text: str) -> str:
    """Replace Bangla digits + common units with English equivalents."""
    text = text.translate(BENGALI_DIGITS)
    for bn, en in BENGALI_UNIT_TO_EN.items():
        text = text.replace(bn, " " + en + " ")
    return text


def _clean(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = _translate_bangla(text)
    text = text.lower()
    text = _PUNCT_RE.sub(" ", text)
    text = _NOISE_RE.sub(" ", text)
    text = _MULTI_SPACE_RE.sub(" ", text).strip()
    return text


def _extract_size(text: str) -> tuple[Optional[float], Optional[str], Optional[float], str]:
    """Find the first plausible size and return (value, canonical_unit, base_qty, text_without_size).

    Multiple matches: we take the *largest* match by base quantity. Store names
    sometimes include packaging text ("12 x 1 L"); the real-world size is the
    larger figure most of the time.
    """
    best = None  # (base_qty, value, canonical_unit, match)
    for m in _SIZE_RE.finditer(text):
        try:
            value = float(m.group("value").replace(",", "."))
        except ValueError:
            continue
        unit_raw = m.group("unit").lower()
        if unit_raw in COUNT_WORDS:
            canonical, mult = COUNT_WORDS[unit_raw]
            base_qty = value * mult
        else:
            canonical, mult = UNIT_ALIASES[unit_raw]
            base_qty = value * mult
        cand = (base_qty, value, canonical, m)
        if best is None or base_qty > best[0]:
            best = cand

    if best is None:
        return None, None, None, text

    base_qty, value, canonical, match = best
    stripped = (text[: match.start()] + " " + text[match.end():]).strip()
    stripped = _MULTI_SPACE_RE.sub(" ", stripped)
    return value, canonical, base_qty, stripped


# Hints that a listing is loose / unpackaged
_LOOSE_HINTS = ("loose", "open", "khola", "খোলা", "কাঁচা")


def normalize(raw_name: str) -> NormalizedProduct:
    """Top-level entry point: messy listing string -> NormalizedProduct."""
    cleaned = _clean(raw_name)
    size_value, size_unit, base_qty, cleaned_no_size = _extract_size(cleaned)

    category = find_category(cleaned)
    subcategory = find_subcategory(category, cleaned) if category else None
    brand = find_brand(cleaned, category)

    is_loose = any(h in cleaned for h in _LOOSE_HINTS)

    # The normalized_name is what we'll trigram-match on. Strip the brand from
    # it so two listings of the same product under different brand spellings
    # still trigram-collide. Order tokens deterministically.
    tokens = cleaned_no_size.split()
    if brand:
        brand_tokens = brand.split()
        tokens = [t for t in tokens if t not in brand_tokens]
    # Drop one-character noise and de-dup while preserving order
    seen: set[str] = set()
    deduped: list[str] = []
    for t in tokens:
        if len(t) <= 1 or t in seen:
            continue
        seen.add(t)
        deduped.append(t)
    normalized_name = " ".join(deduped)

    return NormalizedProduct(
        raw_name=raw_name,
        normalized_name=normalized_name,
        category=category,
        subcategory=subcategory,
        brand=brand,
        size_value=size_value,
        size_unit=size_unit,
        base_unit_qty=base_qty,
        is_loose=is_loose,
    )
