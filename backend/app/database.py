"""Async SQLAlchemy engine + session factory."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from .config import settings

# Trigram match threshold for the pg_trgm `%` operator used by search. Must match
# search_service.TRGM_THRESHOLD; kept here (not imported) to avoid a circular
# import, and pinned equal by tests/test_search.py.
TRGM_SIMILARITY_THRESHOLD = 0.15


class Base(DeclarativeBase):
    pass


_engine = create_async_engine(settings().database_url, pool_pre_ping=True, future=True)
_SessionLocal = async_sessionmaker(_engine, expire_on_commit=False, class_=AsyncSession)


@event.listens_for(_engine.sync_engine, "connect")
def _set_trgm_threshold(dbapi_connection, _record):
    """Set pg_trgm's match threshold once per physical connection.

    search_service uses the `%` operator, whose threshold is the per-session GUC
    pg_trgm.similarity_threshold (default 0.3). We want 0.15 (looser recall), and
    `%` — unlike `similarity() > x` — can use the GIN trgm indexes. Setting it on
    connect amortizes the cost to ~zero (no per-query round-trip). Relies on a
    session-mode connection (the Supabase :5432 pooler); re-setting is harmless.
    """
    dbapi_connection.run_async(
        lambda conn: conn.execute(f"SET pg_trgm.similarity_threshold = {TRGM_SIMILARITY_THRESHOLD}")
    )


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency."""
    async with _SessionLocal() as session:
        yield session


@asynccontextmanager
async def session_scope() -> AsyncIterator[AsyncSession]:
    """For scripts / scrapers / tests."""
    async with _SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def dispose() -> None:
    await _engine.dispose()
