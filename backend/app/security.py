"""Auth dependencies.

Currently just a shared-secret guard for /admin/*. The admin endpoints expose
operational state (scrape status, freshness) that shouldn't be public once
deployed.
"""

from __future__ import annotations

import secrets

from fastapi import Header, HTTPException, status

from .config import settings


async def require_admin(x_admin_key: str | None = Header(default=None)) -> None:
    """Require a valid X-Admin-Key header.

    Behaviour by configuration:
      - ADMIN_API_KEY set        -> header must match it (constant-time), else 401.
      - ADMIN_API_KEY unset, dev -> allowed (local convenience).
      - ADMIN_API_KEY unset, prod-> 503, fail closed rather than expose admin
                                    data because someone forgot to set the key.
    """
    key = settings().admin_api_key
    if not key:
        if settings().environment == "production":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Admin API key not configured",
            )
        return  # development: allow

    if not x_admin_key or not secrets.compare_digest(x_admin_key, key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing admin API key",
        )
