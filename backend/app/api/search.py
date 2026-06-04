from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..schemas.search import SearchResponse
from ..services.search_service import aggregated_search

router = APIRouter(prefix="/search", tags=["search"])


@router.get("", response_model=SearchResponse)
async def search_endpoint(
    q: str = Query("", description="Free-text query, e.g. '5L oil'. Can be empty when browsing by filter."),
    category: str | None = Query(None, description="Restrict to a single category key (e.g. 'cooking_oil')"),
    subcategory: str | None = Query(None, description="Restrict to a single subcategory key (e.g. 'soybean')"),
    limit: int = Query(60, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
) -> SearchResponse:
    groups, canonical, eff_category, size = await aggregated_search(
        session, q, limit=limit, category_filter=category, subcategory_filter=subcategory,
    )
    return SearchResponse(
        query=q,
        parsed_category=eff_category,
        parsed_size=size,
        groups=groups,
        total_groups=len(groups),
        canonical_groups=canonical,
    )
