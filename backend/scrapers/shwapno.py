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
        "milk":        ["/liquid-and-uht-milk"],
        "lentils":     ["/daal-or-lentil"],
        "flour":       ["/flours"],
        "soap":        ["/bath-and-body"],
        "detergent":   ["/laundry"],
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

        # Scroll to load all cards first
        last_count = -1
        for _ in range(self.SCROLL_PASSES):
            cards = await page.query_selector_all(CARD_SEL)
            if len(cards) == last_count:
                break
            last_count = len(cards)
            await page.mouse.wheel(0, 8000)
            await page.wait_for_timeout(1000)

        # Extract all cards in a single DOM evaluation round-trip
        try:
            card_data = await page.evaluate(
                r"""({ cardSel, linkSel, priceSel, nameSel, imgSel }) => {
                    const cards = Array.from(document.querySelectorAll(cardSel));
                    return cards.map(card => {
                        const inner = card.innerText ? card.innerText.trim() : '';

                        const linkEl = card.querySelector(linkSel);
                        const href = linkEl ? linkEl.getAttribute('href') : null;

                        const priceEl = card.querySelector(priceSel);
                        const priceText = priceEl ? priceEl.innerText : null;

                        const nameEl = card.querySelector(nameSel);
                        const nameText = nameEl ? nameEl.innerText : null;

                        const imgEl = card.querySelector(imgSel);
                        const img_src = imgEl ? (imgEl.getAttribute('src') || imgEl.getAttribute('data-src')) : null;

                        return { inner, href, priceText, nameText, img_src };
                    });
                }""",
                {
                    "cardSel": CARD_SEL,
                    "linkSel": LINK_SEL,
                    "priceSel": ".active-price",
                    "nameSel": NAME_SEL,
                    "imgSel": IMG_SEL,
                }
            )
        except Exception as exc:
            logger.warning("[shwapno] DOM evaluation failed for %s: %s", url, exc)
            return

        seen_slugs: set[str] = set()
        for item in card_data[: self.PER_CATEGORY_CAP]:
            listing = self._extract_card_data(item)
            if listing is None or listing.store_product_id in seen_slugs:
                continue
            seen_slugs.add(listing.store_product_id)
            yield listing

    def _extract_card_data(self, item: dict) -> RawListing | None:
        try:
            href = item["href"]
            if not href or href in ("/", "#"):
                return None
            url = href if href.startswith("http") else (self.base_url + href)
            slug = href.lstrip("/").split("?", 1)[0].rstrip("/")
            sku = f"shwapno:{slug}"

            # Price
            price = None
            if item["priceText"]:
                price = _parse_price(item["priceText"])
            inner = item["inner"]
            if price is None:
                m = _PRICE_RE.search(inner)
                if m:
                    price = _parse_price(m.group(0))
            if price is None:
                return None

            # Name
            if item["nameText"]:
                name = item["nameText"].strip()
            else:
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
            img = item["img_src"]

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
