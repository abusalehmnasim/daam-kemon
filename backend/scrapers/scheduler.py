"""
Daam Kemon scrape scheduler.

Runs in its own container and triggers `run_store(...)` for every active store
on a fixed interval. The interval defaults to 6 hours (spec: "every 6-12 hours")
and is configurable via SCRAPE_INTERVAL_HOURS.

Also runs a daily cleanup that drops StoreProduct rows we haven't seen in
STALE_DAYS days, so dropped products fall out of search results.

Run:
    python -m scrapers.scheduler
"""

from __future__ import annotations

import asyncio
import logging
import os
import random
from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import delete, select

from app.database import session_scope
from app.models import StoreProduct

from . import SCRAPERS
from .runner import run_store

logger = logging.getLogger(__name__)


# --- Config -----------------------------------------------------------------

SCRAPE_INTERVAL_HOURS = float(os.getenv("SCRAPE_INTERVAL_HOURS", "6"))
INTER_STORE_DELAY_S   = int(os.getenv("INTER_STORE_DELAY_S", "60"))   # be polite between stores
STALE_DAYS            = int(os.getenv("STALE_DAYS", "7"))
RUN_ON_STARTUP        = os.getenv("RUN_ON_STARTUP", "true").lower() == "true"


# --- Jobs -------------------------------------------------------------------

async def scrape_all_stores() -> None:
    """Walk every registered scraper, running them serially with a small delay.

    Serial (not concurrent) so we don't slam the network from one IP or trip
    rate limits across stores at the same time. The delay also jitters runs
    against fixed-cadence anti-bot heuristics.
    """
    store_names = list(SCRAPERS.keys())
    random.shuffle(store_names)  # avoid alphabetical predictability
    logger.info("Starting scheduled scrape: %s", store_names)

    for i, name in enumerate(store_names):
        cls = SCRAPERS[name]
        try:
            await run_store(cls, categories=None)
        except Exception:  # noqa: BLE001
            logger.exception("[%s] run_store crashed at top level", name)
        if i < len(store_names) - 1:
            jitter = random.uniform(0, 30)
            await asyncio.sleep(INTER_STORE_DELAY_S + jitter)

    logger.info("Scheduled scrape complete")


async def cleanup_stale_listings() -> None:
    """Delete StoreProduct rows we haven't seen in STALE_DAYS days.

    If a store drops a SKU we should stop showing it. PriceHistory rows cascade.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=STALE_DAYS)
    async with session_scope() as session:
        # Count first for the log line
        n = (await session.execute(
            select(StoreProduct).where(StoreProduct.last_seen_at < cutoff)
        )).scalars().unique().all()
        count = len(n)
        if count == 0:
            logger.info("Cleanup: no stale listings")
            return
        await session.execute(delete(StoreProduct).where(StoreProduct.last_seen_at < cutoff))
        logger.info("Cleanup: deleted %d listings not seen since %s", count, cutoff.isoformat())


# --- Entry point ------------------------------------------------------------

_scheduler = None


def start_scheduler_in_background() -> AsyncIOScheduler:
    """Start the APScheduler on the running asyncio event loop."""
    global _scheduler
    if _scheduler is not None:
        return _scheduler

    _scheduler = AsyncIOScheduler(timezone="UTC")

    # Periodic scrape
    _scheduler.add_job(
        scrape_all_stores,
        trigger=IntervalTrigger(hours=SCRAPE_INTERVAL_HOURS),
        id="scrape_all_stores",
        name=f"Scrape all stores every {SCRAPE_INTERVAL_HOURS}h",
        max_instances=1,            # never overlap with itself
        coalesce=True,
    )
    # Daily cleanup at 03:00 UTC (~09:00 BST) — outside likely scrape windows
    _scheduler.add_job(
        cleanup_stale_listings,
        trigger=CronTrigger(hour=3, minute=0),
        id="cleanup_stale_listings",
        name=f"Delete listings unseen for {STALE_DAYS}+ days",
        max_instances=1,
        coalesce=True,
    )

    _scheduler.start()
    logger.info("Scheduler started in background. Jobs: %s",
                [{"id": j.id, "next": str(j.next_run_time)} for j in _scheduler.get_jobs()])

    if RUN_ON_STARTUP:
        asyncio.create_task(_kick_initial_run())

    return _scheduler


async def main_async() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    start_scheduler_in_background()

    # Block forever — APScheduler runs as background tasks in the asyncio loop.
    while True:
        await asyncio.sleep(3600)


async def _kick_initial_run() -> None:
    await asyncio.sleep(5)  # let the DB finish coming up if we started in parallel

    # Smart throttle check: don't run if we had a successful scrape recently
    try:
        async with session_scope() as session:
            from sqlalchemy import text
            result = await session.execute(
                text("SELECT MAX(finished_at) FROM scrape_runs WHERE status = 'success'")
            )
            last_finished = result.scalar()

        if last_finished:
            # Ensure it is timezone-aware
            if last_finished.tzinfo is None:
                last_finished = last_finished.replace(tzinfo=timezone.utc)
            else:
                last_finished = last_finished.astimezone(timezone.utc)

            elapsed = datetime.now(timezone.utc) - last_finished
            interval = timedelta(hours=SCRAPE_INTERVAL_HOURS)
            if elapsed < interval:
                logger.info("Skipping startup scrape: last successful run was %s ago (threshold is %s)", elapsed, interval)
                return
    except Exception as check_err:
        logger.warning(f"Could not check last scrape run status: {check_err}. Proceeding with startup run.")

    logger.info("Running initial scrape on startup (RUN_ON_STARTUP=true)")
    try:
        await scrape_all_stores()
    except Exception:  # noqa: BLE001
        logger.exception("Initial scrape failed")


def main() -> None:
    try:
        asyncio.run(main_async())
    except (KeyboardInterrupt, SystemExit):
        pass


if __name__ == "__main__":
    main()
