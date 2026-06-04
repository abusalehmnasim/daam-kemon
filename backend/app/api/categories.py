"""Read-only view of the category vocabulary, plus a "what's actually stocked"
endpoint backed by store_products."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.categories import CATEGORIES, categories_grouped
from ..database import get_session
from ..models import Product, StoreProduct

router = APIRouter(prefix="/categories", tags=["categories"])


class SubcategoryOut(BaseModel):
    key: str
    display: str


class CategoryOut(BaseModel):
    key: str
    display: str
    product_count: int = 0          # # of canonical products in this category
    listing_count: int = 0          # # of store_products attached
    subcategories: list[SubcategoryOut] = []


class CategoryGroupOut(BaseModel):
    group: str
    categories: list[CategoryOut]


@router.get("", response_model=list[CategoryGroupOut])
async def list_categories(session: AsyncSession = Depends(get_session)) -> list[CategoryGroupOut]:
    """Return the full category tree grouped by `group`, annotated with how
    many products & listings each category currently has in the catalog.

    Categories with zero products are still returned — they should appear in
    the browse UI as empty placeholders, signalling that we know about that
    category but haven't ingested any data for it yet."""
    # Count canonical products per category
    prod_counts = dict(
        (await session.execute(
            select(Product.category, func.count(Product.id)).group_by(Product.category)
        )).all()
    )
    # Count store listings per category (joined via product_id)
    listing_counts_q = (
        select(Product.category, func.count(StoreProduct.id))
        .join(StoreProduct, StoreProduct.product_id == Product.id)
        .group_by(Product.category)
    )
    listing_counts = dict((await session.execute(listing_counts_q)).all())

    tree = categories_grouped()
    out: list[CategoryGroupOut] = []
    for g in tree:
        cats: list[CategoryOut] = []
        for c in g["categories"]:
            cats.append(CategoryOut(
                key=c["key"],
                display=c["display"],
                product_count=prod_counts.get(c["key"], 0),
                listing_count=listing_counts.get(c["key"], 0),
                subcategories=[SubcategoryOut(**s) for s in c["subcategories"]],
            ))
        out.append(CategoryGroupOut(group=g["group"], categories=cats))
    return out
