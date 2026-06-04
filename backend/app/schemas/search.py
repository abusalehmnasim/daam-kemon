from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from .product import ProductGroupOut


class AggregatedOffering(BaseModel):
    """A single store's offering, surfaced inside an aggregated group.

    `brand` is included so the row can render as "Rupchanda · Chaldal" instead
    of forcing the user to read the long store_product_name.
    """
    store_product_id: int
    store_name: str
    store_display_name: str
    brand: Optional[str] = None
    product_name: str             # the canonical name we curated
    store_product_name: str        # what the store calls it
    price: float
    original_price: Optional[float] = None
    in_stock: bool
    url: Optional[str] = None
    image_url: Optional[str] = None
    match_confidence: Optional[float] = None
    match_method: Optional[str] = None
    is_sponsored: bool = False


class AggregatedGroup(BaseModel):
    """One shopping bucket: a kind of product at a given size.

    Example: {category=cooking_oil, subcategory=soybean, size=5L} contains
    every (brand × store) offering of 5L soybean oil. The user picks across
    brands AND stores in one view.
    """
    category: str                  # e.g. "cooking_oil"
    subcategory: Optional[str]     # e.g. "soybean"
    display_name: str              # e.g. "5L Soybean Oil"
    size_value: Optional[float] = None
    size_unit: Optional[str] = None
    is_loose: bool = False
    offerings: list[AggregatedOffering] = Field(default_factory=list)
    cheapest_price: Optional[float] = None
    cheapest_brand: Optional[str] = None
    cheapest_store: Optional[str] = None


class SearchResponse(BaseModel):
    query: str
    parsed_category: Optional[str] = None
    parsed_size: Optional[str] = None
    # New: aggregated by (subcategory + size). This is what the UI renders.
    groups: list[AggregatedGroup] = Field(default_factory=list)
    total_groups: int = 0
    # Legacy: per-canonical-product groups. Kept for tests and any client
    # that still wants the old shape, but the UI no longer reads it.
    canonical_groups: list[ProductGroupOut] = Field(default_factory=list)
