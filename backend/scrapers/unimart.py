"""
Unimart scraper.

Unimart is a Flutter web app. Rather than scraping the canvas DOM (which is
impossible with simple CSS selectors), we query their 6amMart-based REST API
directly (https://myadmin.unimart.online/api/v1/).

Verified API parameters:
  - Headers:
      'moduleId': '1'
      'zoneId': '[1]'  (Unimart Gulshan-2 delivery zone)
      'storeId': '1'   (Unimart Gulshan-2 store)
  - Endpoint: `/items/latest`
  - Parameters: `guest_id`, `category_id`, `limit=100`, `offset=1, 2, ...` (page number)
"""

from __future__ import annotations

import logging
from typing import AsyncIterator

import httpx

from .base import RawListing, StoreScraper

logger = logging.getLogger(__name__)


class UnimartScraper(StoreScraper):
    store_name = "unimart"
    display_name = "Unimart"
    base_url = "https://unimart.online"

    # Mapped category targets. Mapped directly from Unimart category list
    # and verified to return products.
    category_targets = {
        "cooking_oil": ["60"],
        "rice":        ["71", "73"],
        "sugar":       ["81"],
        "eggs":        ["136"],
        "milk":        ["49", "68", "82"],
        "lentils":     ["69"],
        "flour":       ["61"],
        "soap":        ["129"],
        "detergent":   ["112"],
        "spices":      ["80"],
        "salt":        ["70", "78"],
        "garam_masala":["80"],
        "molasses":    ["63"],
        "biscuits":    ["30"],
        "noodles":     ["72"],
        "tea":         ["123", "121"],
        "powdered_milk":["75"],
    }

    # API configuration
    API_BASE_URL = "https://myadmin.unimart.online/api/v1"
    PER_CATEGORY_CAP = 300
    PAGE_SIZE = 100

    def __init__(self, headless: bool = True) -> None:
        super().__init__(headless=headless)
        self._guest_id: int | None = None

    async def _get_guest_id(self) -> int | None:
        if self._guest_id:
            return self._guest_id

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        }
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{self.API_BASE_URL}/auth/guest/request",
                    headers=headers,
                    json={},
                    timeout=10.0
                )
                if resp.status_code == 200:
                    self._guest_id = resp.json().get("guest_id")
                    logger.info("[unimart] Obtained guest ID: %s", self._guest_id)
                    return self._guest_id
        except Exception as exc:
            logger.warning("[unimart] Failed to get guest ID from API: %s", exc)
        return None

    async def scrape_category(self, page, category: str, target: str) -> AsyncIterator[RawListing]:
        guest_id = await self._get_guest_id()
        if not guest_id:
            logger.error("[unimart] Scraper missing guest ID. Aborting run.")
            return

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "moduleId": "1",
            "zoneId": "[1]",
            "storeId": "1",
        }

        offset = 1
        scraped_in_category = 0
        seen_ids: set[str] = set()

        async with httpx.AsyncClient() as client:
            while scraped_in_category < self.PER_CATEGORY_CAP:
                url = (
                    f"{self.API_BASE_URL}/items/latest?"
                    f"guest_id={guest_id}&category_id={target}&"
                    f"limit={self.PAGE_SIZE}&offset={offset}"
                )
                try:
                    resp = await client.get(url, headers=headers, timeout=20.0)
                    if resp.status_code != 200:
                        logger.warning(
                            "[unimart] Request failed for target %s (status %d)",
                            target, resp.status_code
                        )
                        break

                    data = resp.json()
                    products = data.get("products", [])
                    if not products:
                        break

                    for prod in products:
                        listing = self._parse_product(prod, category)
                        if listing and listing.store_product_id not in seen_ids:
                            seen_ids.add(listing.store_product_id)
                            yield listing
                            scraped_in_category += 1
                            if scraped_in_category >= self.PER_CATEGORY_CAP:
                                break

                    if len(products) < self.PAGE_SIZE:
                        break

                    offset += 1
                    await self._polite_wait()
                except Exception as exc:
                    logger.warning(
                        "[unimart] Exception scraping category target %s: %s",
                        target, exc
                    )
                    break

    def _parse_product(self, prod: dict, category: str) -> RawListing | None:
        try:
            prod_id = prod.get("id")
            code = prod.get("code")
            if not prod_id:
                return None

            sku = f"unimart:{code}" if code else f"unimart:{prod_id}"
            name = prod.get("name", "").strip()
            if not name:
                return None

            # Price calculations (including discounts)
            base_price = float(prod.get("price", 0))
            discount = float(prod.get("discount", 0))
            discount_type = prod.get("discount_type", "amount")

            if discount > 0:
                if discount_type == "amount":
                    price = base_price - discount
                elif discount_type == "percent":
                    price = base_price * (1.0 - discount / 100.0)
                else:
                    price = base_price
                original_price = base_price
            else:
                price = base_price
                original_price = None

            # Stock checks
            status = prod.get("status", 1)
            temp_available = prod.get("temp_available", 1)
            stock = prod.get("stock")

            if status != 1 or temp_available != 1:
                in_stock = False
            elif stock is None:
                in_stock = True
            else:
                in_stock = int(stock) > 0

            # Image
            image_url = prod.get("image_full_url")

            # Fallback URL (the store doesn't index product pages due to Flutter canvas rendering)
            url = f"{self.base_url}/"

            return RawListing(
                store_product_id=sku,
                name=name,
                price=price,
                original_price=original_price,
                url=url,
                image_url=image_url,
                in_stock=in_stock,
                category_hint=category,
                raw=prod,
            )
        except Exception as exc:  # noqa: BLE001
            logger.debug("[unimart] failed to parse product: %s", exc)
            return None
