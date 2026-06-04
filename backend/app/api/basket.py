from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..schemas.basket import BasketOptimizeRequest, BasketOptimizeResponse
from ..services.basket_service import optimize_basket

router = APIRouter(prefix="/basket", tags=["basket"])


@router.post("/optimize", response_model=BasketOptimizeResponse)
async def optimize(
    payload: BasketOptimizeRequest,
    session: AsyncSession = Depends(get_session),
) -> BasketOptimizeResponse:
    return await optimize_basket(session, payload.items, payload.stores)
