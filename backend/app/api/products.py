from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..models import Product
from ..schemas.product import ProductGroupOut, ProductOut
from ..services.search_service import _build_group, _store_display_map

router = APIRouter(prefix="/products", tags=["products"])


class ProductSlugOut(BaseModel):
    """Minimal fields the frontend needs to build a slug + sitemap URL."""
    id: int
    name: str
    brand: str | None = None
    category: str
    subcategory: str | None = None


# Declared before /{product_id} so "sitemap" isn't parsed as an int id.
@router.get("/sitemap", response_model=list[ProductSlugOut])
async def products_for_sitemap(session: AsyncSession = Depends(get_session)) -> list[ProductSlugOut]:
    """Every canonical product, minimal fields — powers the Next.js sitemap.

    Unbounded on purpose: a sitemap needs all URLs. Google allows 50k per file;
    revisit with sharding if the catalog ever exceeds that."""
    res = await session.execute(select(Product).order_by(Product.id))
    return [
        ProductSlugOut(
            id=p.id, name=p.name, brand=p.brand,
            category=p.category, subcategory=p.subcategory,
        )
        for p in res.scalars().unique().all()
    ]


@router.get("/{product_id}", response_model=ProductGroupOut)
async def get_product(product_id: int, session: AsyncSession = Depends(get_session)) -> ProductGroupOut:
    res = await session.execute(select(Product).where(Product.id == product_id))
    p = res.scalar_one_or_none()
    if p is None:
        raise HTTPException(status_code=404, detail="Product not found")
    display = await _store_display_map(session)
    return await _build_group(session, p, display)


@router.get("", response_model=list[ProductOut])
async def list_products(
    category: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
) -> list[ProductOut]:
    stmt = select(Product).order_by(Product.category, Product.name).limit(limit)
    if category:
        stmt = stmt.where(Product.category == category)
    res = await session.execute(stmt)
    return [
        ProductOut(
            id=p.id, name=p.name, brand=p.brand, category=p.category,
            subcategory=p.subcategory,
            size_value=float(p.size_value) if p.size_value else None,
            size_unit=p.size_unit, is_loose=p.is_loose,
        )
        for p in res.scalars().unique().all()
    ]
