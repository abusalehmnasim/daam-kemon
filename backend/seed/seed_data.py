"""
Seed the database with stores + a hand-curated MVP product catalog.

This lets the app be useful immediately (before scrapers run) and gives us
a stable dataset to develop the matcher against.

Run with:
    python -m seed.seed_data
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.core.normalizer import normalize
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
        # Othoba's delivery fee is dynamic per-vendor and not exposed pre-cart;
        # use a conservative flat estimate. Real scraper output can refine this.
        "delivery_config": {"flat": 80},
        "affiliate_config": {},
    },
]

# Seed listings don't have real product URLs, so we point "Visit" at each store's
# search page for the product name. Real scraper output will overwrite with the
# actual product page. {q} = url-encoded product name.
STORE_SEARCH_URL = {
    "chaldal": "https://chaldal.com/search/{q}",
    "shwapno": "https://www.shwapno.com/search?search_query={q}",
    "othoba":  "https://othoba.com/quick-search/{q}",
}


# Each entry: (canonical_name, [listing_per_store]).
# Listings reuse the same name across stores when the store happens to call
# it identically; differences are intentional so we exercise the normalizer.
CATALOG: list[dict[str, Any]] = [
    # ---- Cooking oil ----
    # `url` (optional) overrides the per-store search-URL fallback. Verified
    # against each store's live product page where present.
    {
        "name": "Rupchanda Soybean Oil 5L",
        "listings": [
            {"store": "chaldal",   "name": "Rupchanda Soyabean Oil 5 Litre",       "price": 920, "sku": "rupchanda-soyabean-5l",
             "url": "https://chaldal.com/rupchanda-soyabean-oil-5-ltr-5"},
            {"store": "shwapno",   "name": "Rupchanda Soybean Oil 5L",             "price": 905, "sku": "rupchanda-soybean-oil-5l",
             "url": "https://www.shwapno.com/rupchanda-soyabean-oil-5liter"},
        ],
    },
    {
        "name": "Fresh Soybean Oil 5L",
        "listings": [
            {"store": "chaldal",   "name": "Fresh Soyabean Oil (5L)",  "price": 905, "sku": "fresh-soyabean-5l",
             "url": "https://chaldal.com/fresh-fortified-soyabean-oil-5-ltr"},
            {"store": "shwapno",   "name": "Fresh Soybean Oil 5 Litre", "price": 890, "sku": "fresh-soybean-5l",
             "url": "https://www.shwapno.com/fresh-soyabean-oil-5liter"},
        ],
    },
    {
        "name": "Teer Soybean Oil 5L",
        "listings": [
            {"store": "chaldal", "name": "Teer Soyabean Oil 5 Litre", "price": 910, "sku": "teer-soyabean-5l",
             "url": "https://chaldal.com/teer-soyabean-oil-5-ltr-5"},
            {"store": "shwapno", "name": "Teer Soybean Oil 5L",       "price": 900, "sku": "teer-5l",
             "url": "https://www.shwapno.com/teer-soyabean-oil-5liter"},
        ],
    },
    {
        "name": "Rupchanda Soybean Oil 2L",
        "listings": [
            {"store": "chaldal",   "name": "Rupchanda Soyabean Oil 2 Litre", "price": 380, "sku": "rupchanda-2l",
             "url": "https://chaldal.com/rupchanda-soyabean-oil-2-ltr-5"},
            {"store": "shwapno",   "name": "Rupchanda Soybean Oil 2L",       "price": 372, "sku": "rupchanda-soybean-2l",
             "url": "https://www.shwapno.com/rupchanda-soyabean-oil-2liter"},
        ],
    },

    # ---- Rice ----
    {
        "name": "ACI Pure Miniket Rice 5kg",
        "listings": [
            {"store": "chaldal", "name": "ACI Pure Miniket Rice 5kg",          "price": 410, "sku": "aci-miniket-5kg",
             "url": "https://chaldal.com/aci-pure-miniket-rice-5-kg"},
            # Shwapno doesn't list ACI Miniket in 5kg; link to the closest brand-match
            {"store": "shwapno", "name": "ACI Pure Miniket 5 KG",              "price": 405, "sku": "aci-miniket-5"},
        ],
    },
    {
        "name": "Rashid Miniket Rice 5kg",
        "listings": [
            # Chaldal carries Teer/Aarong/Foodela in this slot â€” link the Teer variant for "Miniket 5kg from a different brand"
            {"store": "chaldal",   "name": "Rashid Miniket Rice 5 KG",  "price": 425, "sku": "rashid-miniket-5",
             "url": "https://chaldal.com/teer-miniket-rice-5-kg"},
            {"store": "shwapno",   "name": "Rashid Miniket 5kg",        "price": 420, "sku": "rashid-5kg",
             "url": "https://www.shwapno.com/rupchanda-miniket-rice-5kg"},
        ],
    },
    {
        "name": "Miniket Rice (loose) 1kg",
        "is_loose": True,
        "listings": [
            {"store": "chaldal", "name": "Miniket Rice (Loose) 1 KG", "price": 78, "sku": "miniket-loose-1kg",
             "url": "https://chaldal.com/miniket-rice-premium-boiled-200-gm-25-kg"},
            {"store": "shwapno", "name": "Open Miniket 1 KG",         "price": 75, "sku": "shwapno-miniket-loose"},
        ],
    },
    {
        "name": "Najirshail Rice 5kg",
        "listings": [
            {"store": "chaldal", "name": "Najirshail Rice 5 KG", "price": 520, "sku": "najir-5kg",
             "url": "https://chaldal.com/pran-nazirshail-rice-5-kg"},
            {"store": "shwapno", "name": "Najirshail 5kg",      "price": 510, "sku": "najirshail-5",
             "url": "https://www.shwapno.com/aci-pure-premium-najirshail-rice-5kg"},
        ],
    },

    # ---- Sugar ----
    {
        "name": "Fresh White Sugar 1kg",
        "listings": [
            {"store": "chaldal",   "name": "Fresh Refined Sugar 1 KG", "price": 135, "sku": "fresh-sugar-1kg",
             "url": "https://chaldal.com/fresh-refined-sugar-1-kg"},
            {"store": "shwapno",   "name": "Fresh Sugar 1kg",          "price": 132, "sku": "fresh-sugar-1",
             "url": "https://www.shwapno.com/fresh-refined-sugar-1kg"},
        ],
    },
    {
        "name": "City White Sugar 1kg",
        "listings": [
            # City Sugar isn't currently on Chaldal; link to Teer Sugar as the nearest packaged alternative.
            {"store": "chaldal", "name": "City Refined Sugar 1kg", "price": 130, "sku": "city-sugar-1",
             "url": "https://chaldal.com/teer-sugar-1-kg"},
            {"store": "shwapno", "name": "City Sugar 1 KG",        "price": 128, "sku": "city-sugar-1k"},
        ],
    },
    {
        "name": "Sugar (loose) 1kg",
        "is_loose": True,
        "listings": [
            {"store": "chaldal", "name": "Sugar (Loose) 1 KG", "price": 122, "sku": "loose-sugar-1kg",
             "url": "https://chaldal.com/loose-white-sugar-1-kg"},
            {"store": "shwapno", "name": "Open Sugar 1kg",     "price": 120, "sku": "shwapno-loose-sugar",
             "url": "https://www.shwapno.com/sugar-loose-refined-6"},
        ],
    },

    # ---- Eggs ----
    {
        "name": "Kazi Farms Chicken Eggs 12pcs",
        "listings": [
            # Chaldal's brand-name "Kazi Farms" egg listing is the generic layer 12pcs SKU.
            {"store": "chaldal",   "name": "Kazi Farms Chicken Egg 12pcs",  "price": 155, "sku": "kazi-egg-12",
             "url": "https://chaldal.com/tatka-egg-pack-12-pcs"},
            {"store": "shwapno",   "name": "Kazi Farms Egg (12 Pcs)",       "price": 152, "sku": "kazi-egg-12-shwap",
             "url": "https://www.shwapno.com/kfk-branded-egg-12-pcs-pack"},
        ],
    },
    {
        "name": "Paragon Chicken Eggs 12pcs",
        "listings": [
            {"store": "chaldal", "name": "Paragon Chicken Egg 12 Pcs", "price": 150, "sku": "paragon-egg-12",
             "url": "https://chaldal.com/paragon-omega-3-eggs-12-pcs"},
            {"store": "shwapno", "name": "Paragon Egg 12pcs",          "price": 148, "sku": "paragon-12-shwap"},
        ],
    },
    {
        "name": "Desi Chicken Eggs 12pcs",
        "listings": [
            {"store": "chaldal", "name": "Deshi Chicken Egg 12pcs", "price": 195, "sku": "desi-egg-12",
             "url": "https://chaldal.com/chicken-eggs-discounted-12-pcs"},
            {"store": "shwapno", "name": "Desi Egg 12 Pcs",         "price": 190, "sku": "desi-egg-12-shwap"},
        ],
    },

    # ---- Milk ----
    {
        "name": "Pran UHT Milk 1L",
        "listings": [
            {"store": "chaldal", "name": "Pran UHT Milk 1 Litre", "price": 110, "sku": "pran-uht-1l",
             "url": "https://chaldal.com/pran-uht-milk-1-ltr"},
            {"store": "shwapno", "name": "PRAN UHT Milk 1L",      "price": 108, "sku": "pran-uht-1"},
        ],
    },
    {
        "name": "Milk Vita Powder Milk 500g",
        "listings": [
            {"store": "chaldal", "name": "Milk Vita Full Cream Milk Powder 500gm", "price": 415, "sku": "milkvita-500"},
            {"store": "shwapno", "name": "Milk Vita Powder Milk 500g",             "price": 410, "sku": "milkvita-500g"},
        ],
    },

    # ---- Lentils ----
    {
        "name": "Pran Masoor Dal 1kg",
        "listings": [
            {"store": "chaldal", "name": "Pran Mosur Dal 1 KG",   "price": 135, "sku": "pran-masoor-1kg",
             "url": "https://chaldal.com/pran-moshur-dal-deshi-1-kg"},
            {"store": "shwapno", "name": "PRAN Masoor Dal 1kg",   "price": 132, "sku": "pran-masoor-1"},
        ],
    },
    {
        "name": "Masoor Dal (loose) 1kg",
        "is_loose": True,
        "listings": [
            {"store": "chaldal", "name": "Mosur Dal (Loose) 1 KG", "price": 118, "sku": "loose-masoor-1"},
            {"store": "shwapno", "name": "Open Masoor Dal 1kg",    "price": 115, "sku": "shwapno-loose-masoor"},
        ],
    },

    # ---- Flour ----
    {
        "name": "Teer Atta 2kg",
        "listings": [
            {"store": "chaldal",   "name": "Teer Atta 2 KG",  "price": 130, "sku": "teer-atta-2kg",
             "url": "https://chaldal.com/teer-atta-2-kg"},
            {"store": "shwapno",   "name": "Teer Atta 2kg",   "price": 128, "sku": "teer-atta-2",
             "url": "https://www.shwapno.com/teer-atta-2kg"},
        ],
    },
    {
        "name": "Fresh Maida 1kg",
        "listings": [
            {"store": "chaldal", "name": "Fresh Maida 1 KG", "price": 70, "sku": "fresh-maida-1",
             "url": "https://chaldal.com/fresh-whole-wheat-atta-2-kg"},
            {"store": "shwapno", "name": "Fresh Maida 1kg",  "price": 68, "sku": "fresh-maida-1kg-shwap"},
        ],
    },

    # ---- Soap ----
    {
        "name": "Lux Beauty Soap 100g",
        "listings": [
            {"store": "chaldal",   "name": "Lux Beauty Bar 100g", "price": 55, "sku": "lux-100",
             "url": "https://chaldal.com/lux-soap-bar-velvet-glow-100-gm"},
            {"store": "shwapno",   "name": "Lux Soap 100g",       "price": 53, "sku": "lux-100-shwap",
             "url": "https://www.shwapno.com/lux-soap-rose-and-vitamin-e-soap-100gm-2"},
        ],
    },
    {
        "name": "Lifebuoy Soap 100g",
        "listings": [
            {"store": "chaldal", "name": "Lifebuoy Total 10 Soap 100g", "price": 50, "sku": "lifebuoy-100"},
            {"store": "shwapno", "name": "Lifebuoy Soap 100g",          "price": 49, "sku": "lifebuoy-100-shwap"},
        ],
    },

    # ---- Detergent ----
    {
        "name": "Surf Excel Detergent Powder 1kg",
        "listings": [
            {"store": "chaldal",   "name": "Surf Excel Easy Wash 1 KG", "price": 245, "sku": "surf-excel-1kg",
             "url": "https://chaldal.com/surf-excel-washing-powder-1-1-kg"},
            {"store": "shwapno",   "name": "Surf Excel 1kg",            "price": 240, "sku": "surf-1",
             "url": "https://www.shwapno.com/surf-excel-1-kg"},
        ],
    },
    {
        "name": "Rin Detergent Powder 1kg",
        "listings": [
            {"store": "chaldal", "name": "Rin Power Bright 1 KG", "price": 175, "sku": "rin-1kg"},
            {"store": "shwapno", "name": "Rin 1kg",               "price": 170, "sku": "rin-1-shwap"},
        ],
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

        # Wipe and recreate the catalog. Seed data is replaceable by design;
        # production data will arrive from scrapers and won't go through this path.
        await session.execute(delete(StoreProduct))
        await session.execute(delete(Product))

        for entry in CATALOG:
            np = normalize(entry["name"])
            # Use the curated name as both canonical name and normalized hint
            product = Product(
                name=entry["name"],
                normalized_name=np.normalized_name,
                brand=np.brand,
                category=np.category or "uncategorized",
                subcategory=np.subcategory,
                size_value=np.size_value,
                size_unit=np.size_unit,
                base_unit_qty=np.base_unit_qty,
                is_loose=entry.get("is_loose", np.is_loose),
            )
            session.add(product)
            await session.flush()

            for L in entry["listings"]:
                from urllib.parse import quote_plus
                # Prefer the listing's verified product URL; fall back to a
                # per-store search URL so "Visit" always lands somewhere useful.
                if L.get("url"):
                    product_url = L["url"]
                else:
                    url_tmpl = STORE_SEARCH_URL.get(L["store"], "")
                    product_url = url_tmpl.format(q=quote_plus(L["name"])) if url_tmpl else None
                sp = StoreProduct(
                    product_id=product.id,
                    store_name=L["store"],
                    store_product_id=f"{L['store']}:{L['sku']}",
                    store_product_name=L["name"],
                    store_product_url=product_url,
                    price=L["price"],
                    in_stock=True,
                    match_confidence=1.0,
                    match_method="exact",
                    raw={},
                )
                session.add(sp)
        logger.info("Seeded %d products, %d store listings", len(CATALOG),
                    sum(len(e["listings"]) for e in CATALOG))


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    asyncio.run(seed())


if __name__ == "__main__":
    main()
