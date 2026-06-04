"""Search orchestration: parse user query, fetch candidate products, build groups."""

from __future__ import annotations

from typing import Optional

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.categories import CATEGORIES
from ..core.normalizer import normalize
from ..models import Product, Store, StoreProduct
from ..schemas.product import ProductGroupOut, ProductOut, StoreOfferingOut
from ..schemas.search import AggregatedGroup, AggregatedOffering


# Trigram similarity threshold for "fuzzy text matches the user's query"
TRGM_THRESHOLD = 0.15


async def _store_display_map(session: AsyncSession) -> dict[str, str]:
    res = await session.execute(select(Store.name, Store.display_name))
    return {n: d for n, d in res.all()}


def _build_offering(sp: StoreProduct, store_display: str) -> StoreOfferingOut:
    return StoreOfferingOut(
        store_product_id=sp.id,
        store_name=sp.store_name,
        store_display_name=store_display,
        name=sp.store_product_name,
        price=float(sp.price),
        original_price=float(sp.original_price) if sp.original_price else None,
        in_stock=sp.in_stock,
        url=sp.store_product_url,
        image_url=sp.image_url,
        delivery_fee=float(sp.delivery_fee) if sp.delivery_fee else None,
        match_confidence=float(sp.match_confidence) if sp.match_confidence else None,
        match_method=sp.match_method,
        is_sponsored=bool(sp.raw.get("sponsored", False)) if sp.raw else False,
    )


async def _build_group(session: AsyncSession, product: Product, store_display: dict[str, str]) -> ProductGroupOut:
    offerings = [_build_offering(sp, store_display.get(sp.store_name, sp.store_name)) for sp in product.store_listings]
    in_stock = [o for o in offerings if o.in_stock]
    cheapest = min(in_stock, key=lambda o: o.price) if in_stock else None
    return ProductGroupOut(
        product=ProductOut(
            id=product.id,
            name=product.name,
            brand=product.brand,
            category=product.category,
            subcategory=product.subcategory,
            size_value=float(product.size_value) if product.size_value else None,
            size_unit=product.size_unit,
            is_loose=product.is_loose,
        ),
        offerings=sorted(offerings, key=lambda o: (not o.in_stock, o.price)),
        cheapest_price=cheapest.price if cheapest else None,
        cheapest_store=cheapest.store_display_name if cheapest else None,
    )


async def search(
    session: AsyncSession,
    query: str,
    *,
    limit: int = 30,
    category_filter: Optional[str] = None,
    subcategory_filter: Optional[str] = None,
) -> tuple[list[ProductGroupOut], Optional[str], Optional[str]]:
    """Run a user query against the catalog.

    Optional `category_filter` / `subcategory_filter` constrain the result to
    one branch of the taxonomy — used by the /categories browse page and the
    search filter chips. They override whatever the normalizer parsed out of
    the query: an explicit user choice beats a heuristic.
    """
    np = normalize(query)
    store_display = await _store_display_map(session)

    effective_category = category_filter or np.category
    effective_subcategory = subcategory_filter or np.subcategory
    products: list[Product] = []

    if effective_category and np.base_unit_qty is not None:
        target = float(np.base_unit_qty)
        stmt = (
            select(Product)
            .where(Product.category == effective_category)
            .where(Product.base_unit_qty.is_not(None))
            .order_by(func.abs(Product.base_unit_qty - target), Product.name)
            .limit(limit)
        )
        if effective_subcategory:
            stmt = stmt.where(
                (Product.subcategory == effective_subcategory) | (Product.subcategory.is_(None))
            )
        result = await session.execute(stmt)
        products = list(result.scalars().unique().all())
    elif effective_category:
        stmt = (
            select(Product)
            .where(Product.category == effective_category)
            .order_by(Product.name)
            .limit(limit)
        )
        if effective_subcategory:
            stmt = stmt.where(Product.subcategory == effective_subcategory)
        result = await session.execute(stmt)
        products = list(result.scalars().unique().all())
    elif query.strip():
        # Pure trigram fallback against normalized_name (no filter, no parsed category)
        stmt = text(
            """
            SELECT id FROM products
            WHERE similarity(normalized_name, :q) > :thr
               OR similarity(name, :q) > :thr
            ORDER BY GREATEST(similarity(normalized_name, :q), similarity(name, :q)) DESC
            LIMIT :lim
            """
        )
        rows = (await session.execute(stmt, {"q": np.normalized_name or query.lower(), "thr": TRGM_THRESHOLD, "lim": limit})).all()
        if rows:
            ids = [r[0] for r in rows]
            res2 = await session.execute(select(Product).where(Product.id.in_(ids)))
            by_id = {p.id: p for p in res2.scalars().unique().all()}
            products = [by_id[i] for i in ids if i in by_id]

    canonical = [await _build_group(session, p, store_display) for p in products]
    canonical = [g for g in canonical if g.offerings]

    parsed_size = f"{np.size_value}{np.size_unit}" if np.size_value and np.size_unit else None
    # Report the effective category back to the client so the UI can show the
    # active filter chip even when the user didn't type a category in the query.
    return canonical, effective_category, parsed_size


# ---- Aggregation by (subcategory, size) -----------------------------------

def _category_display(category: str) -> str:
    cfg = CATEGORIES.get(category, {})
    return cfg.get("display", category.replace("_", " ").title())


_BRAND_STOPWORDS = {
    "pure", "premium", "fortified", "natural", "fresh", "best", "the", "and",
    "with", "extra", "value", "pack", "buy", "save", "offer", "loose", "open",
}


def _brand_hint_from_name(store_product_name: str) -> str | None:
    """Best-effort brand guess from a listing name when the canonical row
    doesn't have one. Takes the first 1-2 alphabetic words, skipping common
    marketing stopwords. Lowercased."""
    if not store_product_name:
        return None
    tokens = [t for t in store_product_name.replace("(", " ").replace(")", " ").split() if t]
    out: list[str] = []
    for t in tokens[:4]:
        lt = t.lower().strip(".,:")
        if not lt.isalpha():
            continue
        if lt in _BRAND_STOPWORDS:
            continue
        out.append(lt)
        if len(out) == 1:
            break
    return out[0] if out else None


def _aggregate_groups(canonical: list[ProductGroupOut]) -> list[AggregatedGroup]:
    """Collapse per-brand canonical groups into shopping buckets.

    Two products go into the same bucket iff they share
        (category, subcategory, size_value, size_unit, is_loose).
    Brand becomes a per-offering attribute. Within each bucket, offerings are
    sorted cheapest-in-stock first.
    """
    buckets: dict[tuple, AggregatedGroup] = {}
    for pg in canonical:
        p = pg.product
        key = (p.category, p.subcategory, p.size_value, p.size_unit, p.is_loose)
        bucket = buckets.get(key)
        if bucket is None:
            display = _format_aggregate_name(p)
            bucket = AggregatedGroup(
                category=p.category,
                subcategory=p.subcategory,
                display_name=display,
                size_value=p.size_value,
                size_unit=p.size_unit,
                is_loose=p.is_loose,
            )
            buckets[key] = bucket
        for off in pg.offerings:
            # Prefer the canonical brand; fall back to a hint parsed from the
            # listing name (e.g. "Starship Soyabean Oil" -> "starship") so
            # unknown-brand listings still show a useful label.
            brand = p.brand or _brand_hint_from_name(off.name)
            bucket.offerings.append(AggregatedOffering(
                store_product_id=off.store_product_id,
                store_name=off.store_name,
                store_display_name=off.store_display_name,
                brand=brand,
                product_name=p.name,
                store_product_name=off.name,
                price=off.price,
                original_price=off.original_price,
                in_stock=off.in_stock,
                url=off.url,
                image_url=off.image_url,
                match_confidence=off.match_confidence,
                match_method=off.match_method,
                is_sponsored=off.is_sponsored,
            ))

    out: list[AggregatedGroup] = []
    for bucket in buckets.values():
        # Sort offerings: in-stock first, then by price ascending. Cheapest is the
        # first in-stock row.
        bucket.offerings.sort(key=lambda o: (not o.in_stock, o.price))
        cheapest = next((o for o in bucket.offerings if o.in_stock), None)
        if cheapest:
            bucket.cheapest_price = cheapest.price
            bucket.cheapest_brand = (cheapest.brand or "—").title()
            bucket.cheapest_store = cheapest.store_display_name
        out.append(bucket)
    # Sort buckets by size ascending (closest to the user's parsed size already
    # comes first thanks to the SQL ORDER BY in search()), then by display name.
    out.sort(key=lambda b: (b.size_value or 0, b.display_name))
    return out


def _format_aggregate_name(p: ProductOut) -> str:
    """Build a human-friendly bucket title like "5L Soybean Oil" or
    "1kg Sugar (loose)"."""
    parts: list[str] = []
    if p.size_value is not None and p.size_unit:
        v = int(p.size_value) if float(p.size_value).is_integer() else p.size_value
        parts.append(f"{v}{p.size_unit}")
    if p.subcategory:
        parts.append(p.subcategory.replace("_", " ").title())
    parts.append(_category_display(p.category).replace("Cooking Oil", "Oil"))
    name = " ".join(parts)
    if p.is_loose:
        name += " (loose)"
    return name


async def aggregated_search(
    session: AsyncSession,
    query: str,
    *,
    limit: int = 60,
    category_filter: Optional[str] = None,
    subcategory_filter: Optional[str] = None,
):
    """Public entry point: run the canonical search, then collapse to buckets."""
    canonical, category, size = await search(
        session,
        query,
        limit=limit,
        category_filter=category_filter,
        subcategory_filter=subcategory_filter,
    )
    groups = _aggregate_groups(canonical)
    return groups, canonical, category, size
