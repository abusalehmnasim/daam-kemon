"""Runtime configuration. Reads from environment with sensible local defaults."""

from __future__ import annotations

import os
from functools import lru_cache


class Settings:
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://daamkemon:daamkemon@localhost:5432/daamkemon",
    )
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    cors_origins: list[str] = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    environment: str = os.getenv("ENVIRONMENT", "development")
    # If True, the search service will live-match scraped names against canonical
    # products. False (default) trusts the matcher run at ingest time.
    live_match: bool = os.getenv("LIVE_MATCH", "false").lower() == "true"


@lru_cache(maxsize=1)
def settings() -> Settings:
    return Settings()
