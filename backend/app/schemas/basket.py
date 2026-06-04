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
    query: Optional[str] = None
    quantity: float = 1


class BasketOptimizeRequest(BaseModel):
    items: list[BasketItemIn]
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
