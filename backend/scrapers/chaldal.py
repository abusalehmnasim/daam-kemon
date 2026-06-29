"""
Chaldal scraper.

Chaldal uses a JSON API endpoint:
  POST https://catalog.chaldal.com/searchPersonalized
which handles catalog queries and returns paginated search/category results.

We query this API directly via Python's `httpx` client. This is faster and avoids
any browser evaluation hangs while correctly retrieving out-of-stock items.
"""

from __future__ import annotations

import logging
from typing import AsyncIterator

import httpx

from .base import RawListing, StoreScraper

logger = logging.getLogger(__name__)


# Selectors and regexes — retained for reference or compatibility
CARD_SEL = "div.productV2Catalog"
IMG_SEL = "img"
OUT_OF_STOCK_TEXT = "sold out"


class ChaldalScraper(StoreScraper):
    store_name = "chaldal"
    display_name = "Chaldal"
    base_url = "https://chaldal.com"

    # Category-ID targets. Mapped from route paths to active category IDs
    # verified against the live client state.
    category_targets = {
        "cooking_oil": ["108"],
        "rice":        ["80"],
        "sugar":       ["111"],
        "eggs":        ["61"],
        "milk":        ["1380"],
        "lentils":     ["198"],
        "flour":       ["103"],
        "soap":        ["1620", "1608"],
        "detergent":   ["86"],
        # Backfilled categories:
        "spices":      ["107"],
        "salt":        ["111"],
        "garam_masala":["107"],
        "molasses":    ["77"],
        "biscuits":    ["1619", "1621", "1625"],
        "noodles":     ["93"],
        "tea":         ["1597"],
        "powdered_milk":["1580"],
    }

    async def scrape_category(self, page, category: str, target: str) -> AsyncIterator[RawListing]:
        url = "https://catalog.chaldal.com/searchPersonalized"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        page_index = 0
        async with httpx.AsyncClient() as client:
            while True:
                logger.info("[chaldal] fetching category %s (ID %s) page %d", category, target, page_index)

                payload = {
                    "apiKey": "e964fc2d51064efa97e94db7c64bf3d044279d4ed0ad4bdd9dce89fecc9156f0",
                    "storeId": 1,
                    "warehouseId": 8, # Default main warehouse for Dhaka
                    "pageSize": 100,
                    "currentPageIndex": page_index,
                    "metropolitanAreaId": 1,
                    "query": "",
                    "productVariantId": -1,
                    "bundleId": {"case":"None"},
                    "canSeeOutOfStock": "true", # Retrieve both in-stock and out-of-stock items
                    "filters": ["recursiveCategories=" + target],
                    "maxOutOfStockCount": {"case":"Some","fields":[100]},
                    "shouldShowAlternateProductsForAllOutOfStock": {"case":"Some","fields":["true"]},
                    "customerGuid": {"case":"None"},
                    "deliveryAreaId": {"case":"None"},
                    "shouldShowCategoryBasedRecommendations": {"case":"None"}
                }

                try:
                    res = await client.post(url, json=payload, headers=headers, timeout=20.0)
                    if res.status_code != 200:
                        logger.warning("[chaldal] API query returned status %d for category ID %s page %d", res.status_code, target, page_index)
                        break
                    data = res.json()
                except Exception as exc:
                    logger.warning("[chaldal] API query failed for category ID %s page %d: %s", target, page_index, exc)
                    break

                hits = data.get("hits", [])
                hits_per_page = data.get("hitsPerPage", 100)

                if not hits:
                    break

                for h in hits:
                    listing = self._extract_api_hit(h)
                    if listing:
                        yield listing

                # Stop if we received fewer hits than the page size (reached the end)
                # or if we exceed 3 pages (cap at 300 products per target ID to prevent runaways)
                if len(hits) < hits_per_page or page_index >= 2:
                    break
                page_index += 1

    def _extract_api_hit(self, h: dict) -> RawListing | None:
        try:
            slug = h.get("slug")
            name = h.get("name")
            price = h.get("price")

            if not slug or not name or price is None:
                return None

            price = float(price)
            url = f"{self.base_url}/{slug}"
            sku = f"chaldal:{slug}"

            # Stock status based on availability lists per warehouse
            avail = h.get("productAvailabilityForSelectedWarehouse", [])
            in_stock = len(avail) > 0

            # Image URL extraction
            images = h.get("picturesUrls", [])
            image_url = images[0] if images else None

            return RawListing(
                store_product_id=sku,
                name=name,
                price=price,
                url=url,
                image_url=image_url,
                in_stock=in_stock,
            )
        except Exception as exc:
            logger.debug("[chaldal] API hit extraction failed: %s", exc)
            return None
