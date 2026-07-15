"""
Production data-freshness alert.

Answers one question: *is the live site serving stale prices?* — independently of
whether the scrape job reported success. A run can finish `status='success'` with
`items_scraped=0` (site redesign, anti-bot block, paused DB) and quietly leave the
catalog frozen; the June 2026 ~3-week silent gap was exactly this. So this check
looks at the DATA, not the job log: the age of each active store's newest listing.

Run from `backend/` (same env as the scraper — it just needs DATABASE_URL):

    python -m scripts.check_freshness

Exit codes:
  0  every active store has a listing seen within MAX_AGE_HOURS
  1  at least one active store is stale or has no listings  (the alert)
  2  could not evaluate (DB unreachable, schema missing, etc.)

Env:
  MAX_AGE_HOURS  Staleness threshold in hours (default 36). Production scrapes
                 daily, so 36h tolerates one missed nightly run and alerts on the
                 second consecutive miss — noise-resistant, catches real outages
                 within ~1.5 days.
"""

from __future__ import annotations

import asyncio
import os
import sys
from datetime import datetime, timezone

from sqlalchemy import func, select

from app.database import dispose, session_scope
from app.models import Store, StoreProduct

MAX_AGE_HOURS = float(os.getenv("MAX_AGE_HOURS", "36"))


async def _check() -> int:
    now = datetime.now(timezone.utc)

    async with session_scope() as session:
        # Active stores are the contract: each one is expected to be fresh.
        active = (
            (
                await session.execute(
                    select(Store.name).where(Store.active.is_(True)).order_by(Store.name)
                )
            )
            .scalars()
            .all()
        )

        # Newest sighting + total listings per store, in one round-trip.
        rows = (
            await session.execute(
                select(
                    StoreProduct.store_name,
                    func.max(StoreProduct.last_seen_at).label("most_recent"),
                    func.count().label("total"),
                ).group_by(StoreProduct.store_name)
            )
        ).all()

    seen = {r.store_name: (r.most_recent, int(r.total)) for r in rows}

    if not active:
        print(
            "FRESHNESS: no active stores in the `stores` table — is this the right database?",
            file=sys.stderr,
        )
        return 2

    stale: list[str] = []
    print(f"Freshness check @ {now.isoformat()}  (threshold: {MAX_AGE_HOURS:.0f}h)\n")
    print(f"{'store':<12} {'listings':>8} {'newest_seen':>26} {'age_h':>8}  status")
    print("-" * 72)

    for store in active:
        most_recent, total = seen.get(store, (None, 0))
        if most_recent is None:
            print(f"{store:<12} {total:>8} {'(never)':>26} {'--':>8}  STALE (no listings)")
            stale.append(store)
            continue
        if most_recent.tzinfo is None:  # be robust to naive timestamps
            most_recent = most_recent.replace(tzinfo=timezone.utc)
        age_h = (now - most_recent).total_seconds() / 3600.0
        bad = age_h > MAX_AGE_HOURS
        flag = "STALE" if bad else "ok"
        print(f"{store:<12} {total:>8} {most_recent.isoformat():>26} {age_h:>8.1f}  {flag}")
        if bad:
            stale.append(store)

    print("-" * 72)
    if stale:
        print(
            f"\nFAIL: {len(stale)} of {len(active)} active store(s) stale (> {MAX_AGE_HOURS:.0f}h): "
            f"{', '.join(stale)}.\n"
            "The site may be serving stale prices. Check the latest 'Scrape prices' "
            "Actions run and whether the Supabase project is paused.",
            file=sys.stderr,
        )
        return 1

    print(f"\nOK: all {len(active)} active store(s) fresh within {MAX_AGE_HOURS:.0f}h.")
    return 0


async def _main() -> int:
    try:
        return await _check()
    except Exception as exc:  # DB unreachable, missing tables, bad URL, etc.
        print(f"FRESHNESS: could not evaluate freshness: {exc!r}", file=sys.stderr)
        return 2
    finally:
        await dispose()


if __name__ == "__main__":
    sys.exit(asyncio.run(_main()))
