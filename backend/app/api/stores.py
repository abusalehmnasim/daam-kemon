from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..models import Store

router = APIRouter(prefix="/stores", tags=["stores"])


class StoreOut(BaseModel):
    name: str
    display_name: str
    base_url: str
    active: bool


@router.get("", response_model=list[StoreOut])
async def list_stores(session: AsyncSession = Depends(get_session)) -> list[StoreOut]:
    res = await session.execute(select(Store).order_by(Store.display_name))
    return [
        StoreOut(name=s.name, display_name=s.display_name, base_url=s.base_url, active=s.active)
        for s in res.scalars().all()
    ]
