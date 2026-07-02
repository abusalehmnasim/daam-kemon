"""
Othoba scraper.

Replaced Pandamart in the scraper rotation because Foodpanda's grocery
storefront gates listings by a delivery-location cookie and aggressively
blocks headless browsers.

Verified live (probe on /oil):

  - Cards are `div.product-details` (40 per category page).
  - Name + link: `h4.product-name > a[href]`
  - Current price: `ins.new-price` -> "Tk 940"
  - Original (when discounted): `del.old-price` -> "Tk 1,120"
  - Hidden SKU input: `input.dl-product-sku` -> "MGIN70981" etc.

Stock (probed 2026-07): listing cards carry NO add-to-cart button and NO stock
indicator; a 479-card probe across 9 categories found zero out-of-stock items,
so Othoba appears to filter OOS products out of category listings. The real
out-of-stock marker is a `.sold-out-tag` / `.soldOutTag` badge that lives on the
product *detail* page. We scrape listings only, so `in_stock` defaults to True
and the badge check below is best-effort. Reliable per-SKU stock would require
visiting each detail page — deliberately not done (defeats the one-round-trip
snapshot design).

Implementation note: an earlier version walked the DOM with
ElementHandle.query_selector, and Playwright returned no children — likely
because the page kept mutating after document-ready and handles went stale.
The current version does the entire extraction inside a single page.evaluate()
call so we read a consistent snapshot.
"""

from __future__ import annotations

import logging
import re
from typing import AsyncIterator

from .base import RawListing, StoreScraper

logger = logging.getLogger(__name__)


CARD_SEL = "div.product-details"

_PRICE_RE = re.compile(r"([0-9][\d,]*\.?\d*)")


class OthobaScraper(StoreScraper):
    store_name = "othoba"
    display_name = "Othoba"
    base_url = "https://othoba.com"

    category_targets = {
        "cooking_oil": ["/oil"],
        "rice":        ["/rice"],
        "sugar":       ["/sugar"],
        "eggs":        ["/eggs"],
        "milk":        ["/milk"],
        "lentils":     ["/dal-lentils"],
        "flour":       ["/flour"],
        "soap":        ["/bath-soap"],
        "detergent":   ["/detergent-powder"],
        # Backfilled categories:
        "spices":      ["/spices"],
        "salt":        ["/salt"],
        "garam_masala":["/garam-masala"],
        "molasses":    ["/gur"],
        "biscuits":    ["/biscuits"],
        "noodles":     ["/noodles"],
        "tea":         ["/tea"],
        "powdered_milk":["/powder-milk"],
    }

    PER_CATEGORY_CAP = 200
    SCROLL_PASSES = 8

    async def scrape_category(self, page, category: str, target: str) -> AsyncIterator[RawListing]:
        url = self.base_url + target
        await self._with_retry(lambda: page.goto(url, wait_until="domcontentloaded"), f"goto {url}")
        try:
            await page.wait_for_selector(CARD_SEL, timeout=12_000)
        except Exception:
            logger.warning("[othoba] %s: no cards rendered", url)
            return
        # Othoba uses Cloudflare RocketLoader, which defers the JS that fills
        # the price <ins> placeholders. Wait until at least one card actually
        # shows a "Tk <num>" before extracting.
        try:
            await page.wait_for_function(
                r"""() => {
                    const ins = document.querySelector('div.product-details ins.new-price[id^="price_"]');
                    return ins && /Tk\s*[\d,]+/i.test(ins.textContent || '');
                }""",
                timeout=15_000,
            )
        except Exception:
            logger.warning("[othoba] %s: prices never populated (RocketLoader didn't fire)", url)
            # fall through anyway — maybe a few did get populated

        seen: set[str] = set()
        last_count = -1
        for _ in range(self.SCROLL_PASSES):
            extracted = await self._snapshot_cards(page)
            if extracted["total"] == last_count:
                break
            last_count = extracted["total"]
            for item in extracted["items"][: self.PER_CATEGORY_CAP]:
                if item["sku"] in seen:
                    continue
                seen.add(item["sku"])
                yield RawListing(
                    store_product_id=item["sku"],
                    name=item["name"],
                    price=item["price"],
                    original_price=item.get("original_price"),
                    url=item["url"],
                    image_url=None,
                    in_stock=item.get("in_stock", True),
                )
            await page.mouse.wheel(0, 8000)
            await page.wait_for_timeout(1100)

    async def _snapshot_cards(self, page) -> dict:
        """Extract every card on the current page in one DOM round-trip.

        Avoids the stale-handle problem we hit with per-card query_selector
        calls. Returns {'total': N, 'items': [{sku, name, url, price, ...}]}.
        """
        data = await page.evaluate(
            r"""(base) => {
                const cards = [...document.querySelectorAll('div.product-details')];
                const out = [];
                for (const card of cards) {
                    const a = card.querySelector('h4.product-name a[href]') || card.querySelector('a[href^="/"]');
                    if (!a) continue;
                    const href = a.getAttribute('href');
                    if (!href || href === '#' || href === '/') continue;

                    const nameEl = card.querySelector('h4.product-name');
                    let name = (nameEl ? nameEl.innerText : a.innerText).replace(/\s+/g, ' ').trim();
                    if (!name) continue;

                    // Cards have MULTIPLE ins.new-price elements; the first
                    // is a hidden mobile placeholder. The real price is on the
                    // one whose id starts with "price_".
                    const newEl = card.querySelector('ins.new-price[id^="price_"]')
                               || [...card.querySelectorAll('ins.new-price')].find(e => (e.textContent || '').trim().length > 0);
                    const oldEl = card.querySelector('del.old-price[id^="oldPrice_"]')
                               || card.querySelector('del.old-price');
                    const parse = (el) => {
                        if (!el) return null;
                        const m = (el.textContent || '').replace(/,/g, '').match(/[\d.]+/);
                        return m ? parseFloat(m[0]) : null;
                    };
                    const price = parse(newEl);
                    if (price === null) continue;
                    const original = parse(oldEl);

                    const skuEl = card.querySelector('input.dl-product-sku');
                    const skuVal = skuEl ? (skuEl.value || '') : '';
                    const slug = href.replace(/^\/+/, '').split('?')[0].replace(/\/+$/, '');
                    const sku = 'othoba:' + (skuVal || slug);

                    const url = href.startsWith('http') ? href : base + (href.startsWith('/') ? href : '/' + href);

                    // Othoba marks stock-out with a .sold-out-tag / .soldOutTag
                    // badge (confirmed in its markup). Listing cards have no
                    // add-to-cart button, and a 479-card probe across 9 categories
                    // found zero OOS items — Othoba appears to filter out-of-stock
                    // products out of category listings. This guard is safe
                    // insurance: it only fires if such a badge is actually rendered
                    // on a card, and defaults to in-stock otherwise.
                    const soldEl = card.querySelector('.sold-out-tag, .soldOutTag, .out-of-stock');
                    const in_stock = !(soldEl && soldEl.offsetParent !== null);

                    out.push({ sku, name, url, price, original_price: original, in_stock });
                }
                return { total: cards.length, items: out };
            }""",
            self.base_url,
        )
        return data
