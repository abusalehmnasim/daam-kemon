"""Outbound click tracking — monetization hook only, no attribution logic yet."""

from __future__ import annotations

from urllib.parse import quote, urlparse

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..models import OutboundClick, Store, StoreProduct

router = APIRouter(prefix="/click", tags=["click"])


def _same_host(url: str, base: str | None) -> bool:
    if not base:
        return False
    try:
        return urlparse(url).netloc == urlparse(base).netloc
    except ValueError:
        return False


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

    res2 = await session.execute(select(Store).where(Store.name == sp.store_name))
    store = res2.scalar_one_or_none()
    base_url = store.base_url if store else None

    # Validate the scraped product URL: it must be http(s) AND on the store's own
    # domain. A poisoned scrape or tampered URL must not turn /click into an open
    # redirect off our domain. Fall back to the store's base URL otherwise.
    raw_url = sp.store_product_url or ""
    if raw_url.startswith(("http://", "https://")) and _same_host(raw_url, base_url):
        dest = raw_url
    else:
        dest = base_url or "/"

    # If an affiliate template is configured (trusted config), wrap the URL —
    # URL-encoding it so a "?a=1&b=2" product URL can't smuggle extra params
    # into the affiliate host or truncate the landing page.
    target = dest
    if store and store.affiliate_config and dest.startswith("http"):
        template = store.affiliate_config.get("redirect_template")
        if template:
            target = template.replace("{url}", quote(dest, safe=""))

    return RedirectResponse(target, status_code=302)
