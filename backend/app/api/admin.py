"""
Admin endpoints — read-only views into operational state.

Guarded by a shared secret: every route here requires a valid X-Admin-Key
header (see app/security.require_admin). Set ADMIN_API_KEY in the environment
to enable enforcement; in production an unset key fails closed.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..models import ScrapeRun, StoreProduct
from ..security import require_admin

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


class ScrapeRunOut(BaseModel):
    id: int
    store_name: str
    status: str
    items_scraped: int
    items_matched: int
    started_at: datetime
    finished_at: Optional[datetime] = None
    error: Optional[str] = None
    duration_seconds: Optional[float] = None


@router.get("/scrape_runs", response_model=list[ScrapeRunOut])
async def list_scrape_runs(
    store: str | None = Query(None, description="Filter by store name"),
    limit: int = Query(30, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
) -> list[ScrapeRunOut]:
    """Last N scrape runs across all stores, newest first."""
    stmt = select(ScrapeRun).order_by(desc(ScrapeRun.started_at)).limit(limit)
    if store:
        stmt = stmt.where(ScrapeRun.store_name == store)
    res = await session.execute(stmt)
    out: list[ScrapeRunOut] = []
    for r in res.scalars().all():
        dur = (r.finished_at - r.started_at).total_seconds() if r.finished_at else None
        out.append(ScrapeRunOut(
            id=r.id,
            store_name=r.store_name,
            status=r.status,
            items_scraped=r.items_scraped,
            items_matched=r.items_matched,
            started_at=r.started_at,
            finished_at=r.finished_at,
            error=r.error,
            duration_seconds=dur,
        ))
    return out


class StoreFreshnessOut(BaseModel):
    store_name: str
    total_listings: int
    fresh_listings_24h: int      # last_seen within 24h
    fresh_listings_3d: int
    most_recent_seen: Optional[datetime] = None


@router.get("/freshness", response_model=list[StoreFreshnessOut])
async def freshness(session: AsyncSession = Depends(get_session)) -> list[StoreFreshnessOut]:
    """Per-store freshness summary. Tells you at a glance whether scrapers are running."""
    from datetime import timedelta, timezone

    from sqlalchemy import case, func

    now = datetime.now(timezone.utc)
    d1 = now - timedelta(days=1)
    d3 = now - timedelta(days=3)

    stmt = (
        select(
            StoreProduct.store_name,
            func.count().label("total"),
            func.sum(case((StoreProduct.last_seen_at >= d1, 1), else_=0)).label("fresh24"),
            func.sum(case((StoreProduct.last_seen_at >= d3, 1), else_=0)).label("fresh3d"),
            func.max(StoreProduct.last_seen_at).label("most_recent"),
        )
        .group_by(StoreProduct.store_name)
        .order_by(StoreProduct.store_name)
    )
    res = await session.execute(stmt)
    return [
        StoreFreshnessOut(
            store_name=r.store_name,
            total_listings=int(r.total),
            fresh_listings_24h=int(r.fresh24 or 0),
            fresh_listings_3d=int(r.fresh3d or 0),
            most_recent_seen=r.most_recent,
        )
        for r in res.all()
    ]
