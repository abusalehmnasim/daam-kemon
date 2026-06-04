"""
Seed the database with store settings and clear old catalog listings.

Run with:
    python -m seed.seed_data
"""

from __future__ import annotations

import asyncio
import logging

from sqlalchemy import delete
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.database import session_scope
from app.models import Product, Store, StoreProduct

logger = logging.getLogger(__name__)


STORES = [
    {
        "name": "chaldal",
        "display_name": "Chaldal",
        "base_url": "https://chaldal.com",
        "delivery_config": {"tiers": [{"min": 0, "fee": 89}, {"min": 1500, "fee": 0}]},
        "affiliate_config": {},
    },
    {
        "name": "shwapno",
        "display_name": "Shwapno",
        "base_url": "https://www.shwapno.com",
        "delivery_config": {"tiers": [{"min": 0, "fee": 70}, {"min": 2000, "fee": 0}]},
        "affiliate_config": {},
    },
    {
        "name": "othoba",
        "display_name": "Othoba",
        "base_url": "https://othoba.com",
        "delivery_config": {"flat": 80},
        "affiliate_config": {},
    },
]


async def seed() -> None:
    async with session_scope() as session:
        # Stores: upsert
        for s in STORES:
            stmt = pg_insert(Store).values(**s).on_conflict_do_update(
                index_elements=["name"],
                set_={"display_name": s["display_name"], "base_url": s["base_url"],
                      "delivery_config": s["delivery_config"], "active": True},
            )
            await session.execute(stmt)

        logger.info("Initialized stores in the database")


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    asyncio.run(seed())


if __name__ == "__main__":
    main()
