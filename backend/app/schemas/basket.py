from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class BasketItemIn(BaseModel):
    """One thing the user wants to buy.

    `product_id` is preferred. `query` is a fallback — when the user adds an
    item by typing ("5L oil"), we resolve it to a category-level bucket and
    let the optimizer pick the cheapest qualifying offering per store.
    """
    product_id: Optional[int] = None
    query: Optional[str] = Field(None, max_length=200)
    # Bounded + finite: an unbounded/NaN quantity flows into line_total and
    # produces garbage or NaN cart totals.
    quantity: float = Field(1, gt=0, le=1000, allow_inf_nan=False)


class BasketOptimizeRequest(BaseModel):
    # Cap the basket size: each item triggers a DB round-trip, so an unbounded
    # list is a cheap anonymous DoS on the single free-tier worker.
    items: list[BasketItemIn] = Field(max_length=100)
    stores: Optional[list[str]] = None        # restrict to these stores; default = all active


class StoreLineItemOut(BaseModel):
    item_key: str
    label: str
    store_product_id: int
    store_product_name: str
    unit_price: float
    quantity: float
    line_total: float


class StorePlanOut(BaseModel):
    store: str
    store_display_name: str
    items: list[StoreLineItemOut]
    items_subtotal: float
    delivery_fee: float
    total: float
    missing_items: list[str] = Field(default_factory=list)


class BasketOptimizeResponse(BaseModel):
    single_store: Optional[StorePlanOut]
    split: list[StorePlanOut] = Field(default_factory=list)
    split_savings: float = 0.0
    all_single_store: list[StorePlanOut] = Field(default_factory=list)
    unresolved_items: list[str] = Field(default_factory=list)
