"""
Shwapno scraper.

Shwapno is a Next.js storefront. Verified via probe against the live site:

  - Cards on a category page are `div.product-box` (Tailwind-classed; the
    `.product-box` token is the stable bit).
  - Each card contains:
      * <a href="/<slug>">  → product URL = base_url + href
      * <picture><img>      → image (use srcset or src)
      * .product-price > .active-price text "৳<num>"
      * Product name text appears alongside; we extract via the full inner_text
  - Card innerText format:
        "Delivery 1-2 hours <Name> ৳<price> Per Piece Add to Bag"

  - Category routes are direct slugs: /soybean-oil, /rice, /sugar, /eggs, etc.
    (verified /soybean-oil returns 200).

Patch CSS selectors and regexes at the top when Shwapno redesigns.
"""

from __future__ import annotations

import logging
import re
from typing import AsyncIterator

from .base import RawListing, StoreScraper

logger = logging.getLogger(__name__)


CARD_SEL        = "div.product-box"
LINK_SEL        = "a[href^='/']"
IMG_SEL         = "img"
PRICE_TEXT_SEL  = ".active-price, .product-price"
NAME_SEL        = ".product-title, h3, [class*='product-title']"

_PRICE_RE        = re.compile(r"৳\s*([\d,]+(?:\.\d+)?)")
_DELIVERY_PREFIX = re.compile(r"^\s*Delivery\s+\d+(?:-\d+)?\s*(?:hr|hour|hours|min|minute|minutes|day|days)\b\s*",
                              re.IGNORECASE)
_TAIL_NOISE      = re.compile(r"\b(Per Piece|Add to Bag|Out of Stock|In Stock|Per Pack)\b.*$", re.IGNORECASE)


class ShwapnoScraper(StoreScraper):
    store_name = "shwapno"
    display_name = "Shwapno"
    base_url = "https://www.shwapno.com"

    # Shwapno uses direct category slugs, no /category/ prefix.
    category_targets = {
        "cooking_oil": ["/soybean-oil"],
        "rice":        ["/rice"],
        "sugar":       ["/sugar"],
        "eggs":        ["/egg"],
        "milk":        ["/milk-dairy"],
        "lentils":     ["/dal"],
        "flour":       ["/atta-flour"],
        "soap":        ["/bath-soap"],
        "detergent":   ["/detergent-powder"],
        # Backfilled categories:
        "spices":      ["/spices"],
        "salt":        ["/salt"],
        "garam_masala":["/Wholespice", "/Mixed-Spice"],
        "molasses":    ["/honey"],
        "biscuits":    ["/biscuits"],
        "noodles":     ["/noodles"],
        "tea":         ["/tea"],
        "powdered_milk":["/powder-milk"],
    }

    PER_CATEGORY_CAP = 200
    SCROLL_PASSES = 10

    async def scrape_category(self, page, category: str, target: str) -> AsyncIterator[RawListing]:
        url = self.base_url + target
        await self._with_retry(lambda: page.goto(url, wait_until="domcontentloaded"), f"goto {url}")
        try:
            await page.wait_for_selector(CARD_SEL, timeout=12_000)
        except Exception:
            logger.warning("[shwapno] %s: no cards rendered (selector %r)", url, CARD_SEL)
            return

        seen_slugs: set[str] = set()
        last_count = -1
        for _ in range(self.SCROLL_PASSES):
            cards = await page.query_selector_all(CARD_SEL)
            if len(cards) == last_count:
                break
            last_count = len(cards)
            for card in cards[: self.PER_CATEGORY_CAP]:
                listing = await self._extract_card(card)
                if listing is None or listing.store_product_id in seen_slugs:
                    continue
                seen_slugs.add(listing.store_product_id)
                yield listing
            await page.mouse.wheel(0, 8000)
            await page.wait_for_timeout(1200)

    async def _extract_card(self, card) -> RawListing | None:
        try:
            # Link / URL — first anchor that looks like a product slug
            link_el = await card.query_selector(LINK_SEL)
            href = await link_el.get_attribute("href") if link_el else None
            if not href or href in ("/", "#"):
                return None
            url = href if href.startswith("http") else (self.base_url + href)
            slug = href.lstrip("/").split("?", 1)[0].rstrip("/")
            sku = f"shwapno:{slug}"

            # Price — read the .active-price text first; fall back to a regex on inner_text
            price = None
            price_el = await card.query_selector(".active-price")
            if price_el:
                price = _parse_price(await price_el.inner_text())
            inner = (await card.inner_text()).strip()
            if price is None:
                m = _PRICE_RE.search(inner)
                if m:
                    price = _parse_price(m.group(0))
            if price is None:
                return None

            # Name. Try a structured selector first; fall back to text munging.
            name_el = await card.query_selector(NAME_SEL)
            if name_el:
                name = (await name_el.inner_text()).strip()
            else:
                # innerText is "Delivery 1-2 hours <Name> ৳975 Per Piece Add to Bag"
                stripped = _DELIVERY_PREFIX.sub("", inner)
                m = _PRICE_RE.search(stripped)
                if m:
                    name = stripped[: m.start()].strip()
                else:
                    name = stripped.strip()
                name = _TAIL_NOISE.sub("", name).strip()
            if not name or len(name) < 3:
                return None

            # Image
            img_el = await card.query_selector(IMG_SEL)
            img = None
            if img_el:
                img = await img_el.get_attribute("src") or await img_el.get_attribute("data-src")

            return RawListing(
                store_product_id=sku,
                name=name,
                price=price,
                url=url,
                image_url=img,
                in_stock="out of stock" not in inner.lower(),
            )
        except Exception as exc:  # noqa: BLE001
            logger.debug("[shwapno] card extract failed: %s", exc)
            return None


def _parse_price(text: str | None) -> float | None:
    if not text:
        return None
    cleaned = "".join(c for c in text if c.isdigit() or c == ".")
    try:
        return float(cleaned) if cleaned else None
    except ValueError:
        return None
