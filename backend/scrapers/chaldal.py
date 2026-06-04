"""
Chaldal scraper.

Chaldal is a React SPA with stable React-component class names. Verified via a
probe against the live site (`scrapers/_probe_chaldal.py`):

  - Cards on a category page are `div.productV2Catalog` (~48 per scroll pass).
  - Cards have no `<a href>`; they're click-handled in React. The product URL
    is derivable from the card's `<img>` src, which has the form
        chaldn.com/_mpimage/<slug>?src=...
    The product page is then `https://chaldal.com/<slug>`.
  - Each card's `innerText` looks like:
        "৳ 355 Rahul Pure Mustard Oil 1 ltr 1 hr"
    i.e. price token, then product name, then a delivery-time suffix.
  - Out-of-stock cards include the text "Sold out" or have an `outOfStock` class
    on the inner button.

Categories: Chaldal uses /<slug> directly (no /category/ prefix). `/oil` works;
the old `/cooking-oil` 404s.

If the site changes, all selectors and regexes live at the top of this file.
"""

from __future__ import annotations

import logging
import re
from typing import AsyncIterator

from .base import RawListing, StoreScraper

logger = logging.getLogger(__name__)


# Selectors and regexes — patch here when Chaldal redesigns.
CARD_SEL       = "div.productV2Catalog"
IMG_SEL        = "img"
OUT_OF_STOCK_TEXT = "sold out"

# innerText parsing
_PRICE_RE     = re.compile(r"৳\s*(\d+(?:\.\d+)?)")
_DELIVERY_RE  = re.compile(r"\s*\d+\s*(?:hr|hour|min|minute|day)s?\s*$", re.IGNORECASE)
_SLUG_FROM_IMG = re.compile(r"/_mpimage/([a-z0-9\-]+)")


class ChaldalScraper(StoreScraper):
    store_name = "chaldal"
    display_name = "Chaldal"
    base_url = "https://chaldal.com"

    # Category-slug targets. Verified live: `/oil`, `/rice`, `/sugar`, `/egg`,
    # `/milk`, `/dal-pulses`, `/atta-flour`, `/soap`, `/laundry-detergent`.
    category_targets = {
        "cooking_oil": ["/oil"],
        "rice":        ["/rice"],
        "sugar":       ["/sugar"],
        "eggs":        ["/egg"],
        "milk":        ["/milk"],
        "lentils":     ["/dal-pulses"],
        "flour":       ["/atta-flour"],
        "soap":        ["/soap"],
        "detergent":   ["/laundry-detergent"],
    }

    PER_CATEGORY_CAP = 200
    SCROLL_PASSES = 12

    async def scrape_category(self, page, category: str, target: str) -> AsyncIterator[RawListing]:
        url = self.base_url + target
        await self._with_retry(lambda: page.goto(url, wait_until="domcontentloaded"), f"goto {url}")
        try:
            await page.wait_for_selector(CARD_SEL, timeout=12_000)
        except Exception:
            logger.warning("[chaldal] %s: no cards rendered (selector %r)", url, CARD_SEL)
            return

        seen_slugs: set[str] = set()
        last_count = -1
        for _ in range(self.SCROLL_PASSES):
            cards = await page.query_selector_all(CARD_SEL)
            if len(cards) == last_count:
                break       # no new cards after a scroll — we've reached the bottom
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
            inner = (await card.inner_text()).strip()
            if not inner:
                return None

            price_match = _PRICE_RE.search(inner)
            if not price_match:
                return None
            price = float(price_match.group(1))

            # Slug + product URL from the card's image src
            img_el = await card.query_selector(IMG_SEL)
            img_src = await img_el.get_attribute("src") if img_el else None
            slug_match = _SLUG_FROM_IMG.search(img_src or "")
            if not slug_match:
                return None
            slug = slug_match.group(1)
            url = f"{self.base_url}/{slug}"
            sku = f"chaldal:{slug}"

            # Name = everything except the price token and the trailing delivery suffix.
            # Chaldal lays out the card text as several lines (product name on one,
            # size on another). Join them so the normalizer can extract size — picking
            # the longest line drops "500 ml" etc.
            name_part = inner[price_match.end():].strip()
            name_part = _DELIVERY_RE.sub("", name_part).strip()
            lines = [ln.strip() for ln in name_part.splitlines() if ln.strip()]
            # Drop any "Save ৳ X" badge line.
            lines = [ln for ln in lines if not ln.lower().startswith("save ৳") and not ln.lower().startswith("save tk")]
            name = " ".join(lines) if lines else name_part

            in_stock = OUT_OF_STOCK_TEXT not in inner.lower()

            return RawListing(
                store_product_id=sku,
                name=name,
                price=price,
                url=url,
                image_url=img_src,
                in_stock=in_stock,
            )
        except Exception as exc:  # noqa: BLE001
            logger.debug("[chaldal] card extract failed: %s", exc)
            return None
