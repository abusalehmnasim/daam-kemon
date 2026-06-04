from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class StoreOfferingOut(BaseModel):
    """One store's listing of a product, surfaced to the UI."""
    store_product_id: int
    store_name: str
    store_display_name: str
    name: str
    price: float
    original_price: Optional[float] = None
    in_stock: bool
    url: Optional[str] = None
    image_url: Optional[str] = None
    delivery_fee: Optional[float] = None
    match_confidence: Optional[float] = None
    match_method: Optional[str] = None
    is_sponsored: bool = False


class ProductOut(BaseModel):
    id: int
    name: str
    brand: Optional[str] = None
    category: str
    subcategory: Optional[str] = None
    size_value: Optional[float] = None
    size_unit: Optional[str] = None
    is_loose: bool = False


class ProductGroupOut(BaseModel):
    """A single canonical product alongside every store offering for it."""
    product: ProductOut
    offerings: list[StoreOfferingOut] = Field(default_factory=list)
    cheapest_price: Optional[float] = None
    cheapest_store: Optional[str] = None
    # Alternatives are *other* canonical products in the same category/subcategory,
    # included when the matcher's confidence on the primary group was below 1.0
    # or the user searched by category.
    alternatives: list["ProductGroupOut"] = Field(default_factory=list)


ProductGroupOut.model_rebuild()
