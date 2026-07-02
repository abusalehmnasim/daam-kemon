"""
Scraper runner.

Wires a per-store scraper into the database pipeline:

    raw listing
       -> normalize()                  (extract category/brand/size/etc)
       -> find-or-create canonical Product
       -> upsert StoreProduct (link to Product, update price)
       -> append PriceHistory row if price changed

Usage:
    python -m scrapers.runner --store chaldal
    python -m scrapers.runner --store all --categories cooking_oil rice

Exits non-zero if any store run fails entirely; partial failures are logged
but treated as success-with-warnings (status='partial' on scrape_runs).
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from datetime import datetime, timezone
from typing import Iterable

from sqlalchemy import select

from app.core.matcher import CandidateProduct, match
from app.core.normalizer import normalize
from app.database import session_scope
from app.models import PriceHistory, Product, ScrapeRun, StoreProduct

from . import SCRAPERS
from .base import RawListing, StoreScraper

logger = logging.getLogger(__name__)


async def _get_or_create_product(session, np) -> tuple[Product | None, float, str]:
    """Find an existing canonical Product that matches `np`, or create one.

    Returns (product, match_confidence, match_method). The confidence/method are
    the *real* matcher verdict — 0.85/"brand", 1.0/"exact", or "new" for a freshly
    created canonical — so the persisted columns are honest and auditable. (This
    used to always store 1.0/"exact" because a redundant second matcher pass in
    the caller excluded the very product it compared against.)
    """
    if not np.category:
        # Can't decide a category — store as orphan (no product link).
        return None, 0.0, "unmatched"

    res = await session.execute(
        select(Product).where(Product.category == np.category)
    )
    candidates = [
        CandidateProduct(
            id=p.id,
            normalized_name=p.normalized_name,
            brand=p.brand,
            category=p.category,
            subcategory=p.subcategory,
            size_value=float(p.size_value) if p.size_value else None,
            size_unit=p.size_unit,
            base_unit_qty=float(p.base_unit_qty) if p.base_unit_qty else None,
            is_loose=p.is_loose,
        )
        for p in res.scalars().unique().all()
    ]
    result = match(np, candidates)

    # Ingest is stricter than search: only attach the listing to an existing
    # canonical when the match is brand-confident (>= 0.85). Category-tier
    # matches (0.70) would otherwise let unknown brands hijack a famous one's
    # canonical row (real bug: "Starship Soyabean 5L" was attaching to the
    # Rupchanda canonical). New canonicals fragment cleanly and the search-time
    # aggregation re-collapses them under "5L Soybean Oil".
    if result.product_id is not None and result.confidence >= 0.85:
        res = await session.execute(select(Product).where(Product.id == result.product_id))
        return res.scalar_one(), result.confidence, result.method

    # Build a sensible canonical name. We want it readable, not the raw scrape.
    parts = []
    if np.brand:
        parts.append(np.brand.title())
    if np.subcategory:
        parts.append(np.subcategory.title())
    parts.append({
        "cooking_oil": "Oil", "rice": "Rice", "sugar": "Sugar", "eggs": "Eggs",
        "milk": "Milk", "lentils": "Dal", "flour": "Flour",
        "soap": "Soap", "detergent": "Detergent",
        "spices": "Spices", "salt": "Salt", "garam_masala": "Masala",
        "molasses": "Gur", "biscuits": "Biscuits", "noodles": "Noodles",
        "tea": "Tea", "powdered_milk": "Powdered Milk",
    }.get(np.category, np.category.replace("_", " ").title()))
    if np.size_value and np.size_unit:
        v = int(np.size_value) if float(np.size_value).is_integer() else np.size_value
        parts.append(f"{v}{np.size_unit}")
    # Check if a product with the exact same dedupe key attributes already exists
    # to avoid unique constraint violations on product creation.
    dup_stmt = select(Product).where(
        Product.category == np.category,
        Product.subcategory == np.subcategory,
        Product.brand == np.brand,
        Product.size_unit == np.size_unit,
        Product.size_value == np.size_value,
        Product.is_loose == np.is_loose
    )
    dup_res = await session.execute(dup_stmt)
    existing_dup = dup_res.scalar_one_or_none()
    if existing_dup is not None:
        # Same (brand, subcategory, size, loose) spec by construction — exact.
        return existing_dup, 1.0, "exact"

    canonical_name = " ".join(parts)

    product = Product(
        name=canonical_name,
        normalized_name=np.normalized_name,
        brand=np.brand,
        category=np.category,
        subcategory=np.subcategory,
        size_value=np.size_value,
        size_unit=np.size_unit,
        base_unit_qty=np.base_unit_qty,
        is_loose=np.is_loose,
    )
    session.add(product)
    await session.flush()
    # Freshly created from this listing: exact by definition, but tag as "new"
    # so audits can distinguish spawned canonicals from matched ones.
    return product, 1.0, "new"


async def _upsert_store_product(session, scraper: StoreScraper, listing: RawListing,
                                product_id: int | None, confidence: float, method: str) -> bool:
    """Insert or update a StoreProduct. Returns True if the price changed (or is new)."""
    res = await session.execute(
        select(StoreProduct)
        .where(StoreProduct.store_name == scraper.store_name)
        .where(StoreProduct.store_product_id == listing.store_product_id)
    )
    existing = res.scalar_one_or_none()
    now = datetime.now(timezone.utc)

    if existing is None:
        sp = StoreProduct(
            product_id=product_id,
            store_name=scraper.store_name,
            store_product_id=listing.store_product_id,
            store_product_name=listing.name,
            store_product_url=listing.url,
            image_url=listing.image_url,
            price=listing.price,
            original_price=listing.original_price,
            in_stock=listing.in_stock,
            match_confidence=confidence,
            match_method=method,
            raw=listing.raw,
        )
        session.add(sp)
        await session.flush()
        session.add(PriceHistory(store_product_id=sp.id, price=listing.price, in_stock=listing.in_stock))
        return True

    price_changed = float(existing.price) != float(listing.price) or existing.in_stock != listing.in_stock
    existing.price = listing.price
    existing.original_price = listing.original_price
    existing.in_stock = listing.in_stock
    existing.last_seen_at = now
    existing.store_product_name = listing.name
    if product_id is not None:
        existing.product_id = product_id
        existing.match_confidence = confidence
        existing.match_method = method
    if price_changed:
        session.add(PriceHistory(
            store_product_id=existing.id, price=listing.price, in_stock=listing.in_stock,
        ))
    return price_changed


async def run_store(scraper_cls, categories: list[str] | None) -> None:
    scraper = scraper_cls()
    async with session_scope() as session:
        run = ScrapeRun(store_name=scraper.store_name, status="running")
        session.add(run)
        await session.flush()
        run_id = run.id

    scraped = 0
    matched = 0
    error: str | None = None

    try:
        async with session_scope() as session:
            async for listing in scraper.run(categories=categories):
                scraped += 1
                np = normalize(listing.name)
                # If the scraper observed a category hint and the normalizer
                # couldn't figure it out from the name alone, trust the hint.
                if not np.category and listing.category_hint:
                    np.category = listing.category_hint  # type: ignore[misc]

                # Each listing runs in its own savepoint so an IntegrityError on
                # one row (e.g. dedupe collision because the normalizer couldn't
                # extract enough attributes) doesn't poison the whole run.
                try:
                    async with session.begin_nested():
                        product, confidence, method = await _get_or_create_product(session, np)
                        if product is None:
                            await _upsert_store_product(session, scraper, listing, None, 0.0, "unmatched")
                            continue

                        await _upsert_store_product(session, scraper, listing, product.id, confidence, method)
                        matched += 1
                except Exception as per_item_exc:  # noqa: BLE001
                    logger.warning("[%s] skipping %r: %s",
                                   scraper.store_name, listing.store_product_id, per_item_exc)
                    import sqlalchemy.exc
                    is_conn_err = False
                    if isinstance(per_item_exc, sqlalchemy.exc.PendingRollbackError):
                        is_conn_err = True
                    elif isinstance(per_item_exc, sqlalchemy.exc.DBAPIError):
                        if isinstance(per_item_exc, sqlalchemy.exc.OperationalError):
                            is_conn_err = True
                        else:
                            err_msg = str(per_item_exc).lower()
                            if any(k in err_msg for k in ("connection", "closed", "disconnect", "shutdown")):
                                is_conn_err = True

                    if is_conn_err or not session.is_active:
                        logger.warning("[%s] Database transaction is invalid or connection lost. Resetting session...", scraper.store_name)
                        try:
                            await session.rollback()
                        except Exception as rollback_exc:
                            logger.warning("[%s] Rollback failed: %s", scraper.store_name, rollback_exc)
                    continue

                # Commit every 50 items so a crash mid-run doesn't lose everything.
                if scraped % 50 == 0:
                    await session.commit()

        status = "success"
    except Exception as exc:  # noqa: BLE001
        logger.exception("[%s] run failed: %s", scraper.store_name, exc)
        status = "failed"
        error = str(exc)

    # Update the run record
    async with session_scope() as session:
        res = await session.execute(select(ScrapeRun).where(ScrapeRun.id == run_id))
        run = res.scalar_one()
        run.finished_at = datetime.now(timezone.utc)
        run.status = "partial" if (status == "success" and scraped > 0 and matched < scraped) else status
        run.items_scraped = scraped
        run.items_matched = matched
        run.error = error

    logger.info("[%s] done: scraped=%d matched=%d status=%s", scraper.store_name, scraped, matched, status)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run Daam Kemon scrapers")
    p.add_argument("--store", default="all", help="Store key (chaldal/shwapno/pandamart) or 'all'")
    p.add_argument("--categories", nargs="*", default=None,
                   help="Optional category filter; defaults to all categories the store supports")
    return p.parse_args(argv)


async def main_async(args: argparse.Namespace) -> int:
    targets: Iterable
    if args.store == "all":
        targets = SCRAPERS.values()
    else:
        if args.store not in SCRAPERS:
            print(f"Unknown store: {args.store}", file=sys.stderr)
            return 2
        targets = [SCRAPERS[args.store]]

    rc = 0
    for cls in targets:
        try:
            await run_store(cls, args.categories)
        except Exception as exc:  # noqa: BLE001
            logger.error("Store %s failed at top level: %s", cls.__name__, exc)
            rc = 1
    return rc


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    args = _parse_args(argv)
    return asyncio.run(main_async(args))


if __name__ == "__main__":
    sys.exit(main())
