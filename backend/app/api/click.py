"""Outbound click tracking — monetization hook only, no attribution logic yet."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..models import OutboundClick, Store, StoreProduct

router = APIRouter(prefix="/click", tags=["click"])


@router.get("/{store_product_id}")
async def track_click(
    store_product_id: int,
    session_id: str | None = None,
    referrer: str | None = None,
    session: AsyncSession = Depends(get_session),
):
    res = await session.execute(select(StoreProduct).where(StoreProduct.id == store_product_id))
    sp = res.scalar_one_or_none()
    if sp is None:
        raise HTTPException(status_code=404, detail="Listing not found")

    session.add(OutboundClick(
        store_product_id=sp.id,
        store_name=sp.store_name,
        session_id=session_id,
        referrer=referrer,
    ))
    await session.commit()

    # If the store config defines an affiliate template, wrap the URL.
    res2 = await session.execute(select(Store).where(Store.name == sp.store_name))
    store = res2.scalar_one_or_none()
    target = sp.store_product_url or (store.base_url if store else "/")
    if store and store.affiliate_config:
        template = store.affiliate_config.get("redirect_template")
        if template and sp.store_product_url:
            target = template.replace("{url}", sp.store_product_url)

    return RedirectResponse(target, status_code=302)
