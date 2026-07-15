"""
Agora scraper.

Agora (agorasuperstores.com) is a Laravel storefront. Verified against the live
site:

  - `/products/<slug>` renders the FULL listing for one storefront subcategory
    server-side in one request — no pagination param has any effect (`?page=2`
    returns byte-identical output; a client-side "PAGINATION" widget just
    show/hides cards already in the DOM). No Playwright needed.
  - Cards are `<div class="veg-card">` — reused verbatim across every
    subcategory (meat, dairy, cleaning supplies all render with the same
    "veg-card"/"allProduct-*" class names; the names are template leftovers,
    not semantic).
  - Each card: `<h5 class="allProduct-title">` (brand-ish name), one or two
    `<p class="allProduct-subtext">` (first = description with size, second
    = "<N> TK OFF" discount badge when on sale, empty otherwise), and
    `<p class="allProduct-price" data-price="...">` (already-discounted price).
    `original_price` is reconstructed as price + discount amount.
  - No out-of-stock markers were found anywhere on these pages — like Othoba,
    Agora appears to filter OOS items out of listings, so `in_stock` defaults
    True.
  - There's also a `/products/search?name=&location=` JSON endpoint, but it's
    an autocomplete suggester capped at 10 results — useless for bulk listing.

Agora's storefront subcategories are coarser than our category set: one page
(e.g. "commodities") mixes cooking oil, rice, sugar, lentils, flour and salt
together. We fetch each distinct subcategory page only once per run (cached
on the instance) and keyword-filter per our category, the same relevance-
filter pattern `daraz.py` uses for its marketplace noise — except here it's
"which of our categories does this card belong to" rather than "is this
noise". A few categories (spices/garam_masala) deliberately overlap rather
than fight over an exclusion list; the ingest upsert is idempotent so a card
counted under two categories in one run is harmless.

molasses has no obvious home in Agora's subcategories (not found under
"commodities"), so it's left out of category_targets — same as any store
that simply doesn't carry a category.
"""

from __future__ import annotations

import logging
import re
from typing import AsyncIterator

import httpx

from .base import RawListing, StoreScraper

logger = logging.getLogger(__name__)

CARD_MARKER = '<div class="veg-card">'

_PROD_ID_RE = re.compile(r'data-prod-id="(\d+)"')
_TITLE_RE = re.compile(r'allProduct-title"[^>]*>([^<]*)</h5>')
_SUBTEXT_RE = re.compile(r'allProduct-subtext[^"]*"[^>]*>\s*([^<]*?)\s*</p>')
_PRICE_RE = re.compile(r'allProduct-price"[^>]*data-price="([\d.]+)"')
_IMG_RE = re.compile(r'<img src="([^"]+)"')
_URL_RE = re.compile(r'<a href="([^"]+)" class="text-decoration-none">')
_DISCOUNT_RE = re.compile(r'([\d.]+)\s*TK OFF', re.IGNORECASE)


class AgoraScraper(StoreScraper):
    store_name = "agora"
    display_name = "Agora"
    base_url = "https://agorasuperstores.com"

    # category key -> storefront subcategory slug(s) (/products/<slug>).
    # Several categories deliberately share a slug; scrape_category filters by
    # keyword and the page fetch itself is cached per slug to avoid re-hitting
    # the same URL once for every category that points at it.
    category_targets = {
        "cooking_oil":   ["commodities"],
        "rice":          ["commodities"],
        "sugar":         ["commodities"],
        "lentils":       ["commodities"],
        "flour":         ["commodities"],
        "salt":          ["commodities"],
        "eggs":          ["poultry"],
        "milk":          ["milk"],
        "powdered_milk": ["milk"],
        "soap":          ["personal-care"],
        "detergent":     ["cleaning-needs"],
        "spices":        ["spices"],
        "garam_masala":  ["spices"],
        "biscuits":      ["grocery-essentials"],
        "tea":           ["grocery-essentials"],
        "noodles":       ["quick-food"],
    }

    # Pages are single, unpaginated server-side dumps (largest observed: 427
    # items on /products/spices), so this is a safety ceiling, not a real cap.
    PER_CATEGORY_CAP = 500

    # Keyword filter per category. Empty tuple means "accept everything on
    # the page" (used only where the page maps 1:1 to a single category).
    CATEGORY_KEYWORDS: dict[str, tuple[str, ...]] = {
        "cooking_oil":   ("OIL",),
        # Descriptions are truncated by the site's own CSS, so a rice card can
        # read e.g. "Green field miniket muzammel rashid loos" — the word
        # "rice" itself gets cut off. Variety names catch what the truncated
        # generic word would have.
        "rice":          ("RICE", "CHAL", "MINIKET", "CHINIGURA", "NAZIRSHAIL",
                           "BASMATI", "PAIJAM", "SWARNA", "KATARIVOG", "KALIJIRA"),
        # "CHINI" (sugar, romanized Bangla) was tried and dropped: every hit in
        # the real commodities page was "CHINIGURA" (a rice variety), a false
        # positive, and the storefront's own sugar listings all just say SUGAR.
        "sugar":         ("SUGAR",),
        "lentils":       ("LENTIL", "DAL", "DAAL", "MASOOR", "MOONG", "MUSHURI"),
        "flour":         ("ATTA", "MAIDA", "FLOUR"),
        "salt":          ("SALT", "LOBON"),
        "eggs":          ("EGG",),
        "soap":          ("SOAP",),
        "detergent":     ("DETERGENT", "SURF", "WHEEL", "OMO"),
        "spices":        (),
        "garam_masala":  ("GARAM MASALA",),
        "biscuits":      ("BISCUIT", "COOKIE", "CRACKER"),
        "tea":           ("TEA",),
        "noodles":       ("NOODLE", "MAGGI"),
    }

    # Word-boundary patterns for CATEGORY_KEYWORDS, precompiled once. Plain
    # substring matching let short keywords false-match inside unrelated
    # words — e.g. detergent's "SURF" (the brand) matching inside "SURFACE"
    # ("Multi Surface Cleaner"), or lentils' "DAL" matching inside "DALDA".
    _CATEGORY_KEYWORD_PATTERNS: dict[str, tuple[re.Pattern, ...]] = {
        cat: tuple(re.compile(r"\b" + re.escape(kw) + r"\b") for kw in kws)
        for cat, kws in CATEGORY_KEYWORDS.items()
    }

    def __init__(self, headless: bool = True) -> None:
        super().__init__(headless=headless)
        self._page_cache: dict[str, list[dict]] = {}

    def _headers(self) -> dict[str, str]:
        return {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml",
        }

    @staticmethod
    def _split_cards(html: str) -> list[str]:
        starts = [m.start() for m in re.finditer(re.escape(CARD_MARKER), html)]
        starts.append(len(html))
        return [html[starts[i]:starts[i + 1]] for i in range(len(starts) - 1)]

    @staticmethod
    def _extract_card(card_html: str) -> dict | None:
        prod_id = _PROD_ID_RE.search(card_html)
        title = _TITLE_RE.search(card_html)
        price = _PRICE_RE.search(card_html)
        if not (prod_id and title and price):
            return None
        url = _URL_RE.search(card_html)
        img = _IMG_RE.search(card_html)
        subtexts = [s for s in _SUBTEXT_RE.findall(card_html)]
        return {
            "prod_id": prod_id.group(1),
            "title": title.group(1).strip(),
            "subtexts": subtexts,
            "price": price.group(1),
            "url": url.group(1) if url else None,
            "image": img.group(1) if img else None,
        }

    async def _fetch_cards(self, slug: str) -> list[dict]:
        if slug in self._page_cache:
            return self._page_cache[slug]

        async def _do_fetch():
            async with httpx.AsyncClient(follow_redirects=True) as client:
                return await client.get(
                    f"{self.base_url}/products/{slug}", headers=self._headers(), timeout=20.0
                )

        # Only cache on a successful fetch. Caching an empty result after a
        # failed request would silently zero out every other category sharing
        # this slug for the rest of the run (e.g. one transient 503 on
        # "commodities" would drop cooking_oil/rice/sugar/lentils/flour/salt
        # together) — better to retry the page on each category's turn.
        cards: list[dict] = []
        try:
            resp = await self._with_retry(_do_fetch, f"GET /products/{slug}")
            if resp.status_code == 200:
                for block in self._split_cards(resp.text):
                    item = self._extract_card(block)
                    if item:
                        cards.append(item)
                self._page_cache[slug] = cards
            else:
                logger.warning("[agora] /products/%s -> status %d", slug, resp.status_code)
        except Exception as exc:
            logger.warning("[agora] request failed for %r: %s", slug, exc)

        return cards

    # The "milk" storefront page is really a dairy page (milk, cheese, butter,
    # curd, yogurt all mixed in) and also carries non-dairy powders (health
    # drinks, custard) under the same page. "F.C.M.P."/"FCMP"/"I.F.C.M" are
    # the store's own abbreviations for "full cream milk powder" and are
    # sufficient on their own. A bare "POWDER" is not — "Bournvita Health
    # Drink Powder" or "Custard Powder" would otherwise be misfiled as
    # powdered milk — so it additionally requires "MILK" in the name.
    MILK_POWDER_ABBREVIATIONS = ("F.C.M.P", "FCMP", "I.F.C.M")

    def _matches_category(self, name_upper: str, category: str) -> bool:
        has_milk = "MILK" in name_upper
        is_powdered = (
            any(a in name_upper for a in self.MILK_POWDER_ABBREVIATIONS)
            or ("POWDER" in name_upper and has_milk)
        )
        if category == "milk":
            return has_milk and not is_powdered
        if category == "powdered_milk":
            return is_powdered
        patterns = self._CATEGORY_KEYWORD_PATTERNS.get(category, ())
        if not patterns:
            return True
        return any(p.search(name_upper) for p in patterns)

    async def run(self, categories: list[str] | None = None) -> AsyncIterator[RawListing]:
        """Drive the scraper without the base class's Playwright/Chromium
        launch — Agora is httpx-only (see module docstring), so the base
        implementation would launch and immediately discard an unused
        browser on every run, and hard-fail on any host without Chromium
        installed."""
        cats = categories or list(self.category_targets.keys())
        for cat in cats:
            targets = self.category_targets.get(cat, [])
            for target in targets:
                logger.info("[%s] scraping %s -> %s", self.store_name, cat, target)
                try:
                    async for listing in self.scrape_category(None, cat, target):
                        listing.category_hint = listing.category_hint or cat
                        yield listing
                    await self._polite_wait()
                except Exception as exc:  # noqa: BLE001
                    logger.exception("[%s] category %s/%s failed: %s",
                                     self.store_name, cat, target, exc)
                    continue

    async def scrape_category(self, page, category: str, target: str) -> AsyncIterator[RawListing]:
        cards = await self._fetch_cards(target)
        seen: set[str] = set()
        scraped = 0
        for item in cards:
            if scraped >= self.PER_CATEGORY_CAP:
                break
            listing = self._parse_card(item, category)
            if listing is None or listing.store_product_id in seen:
                continue
            seen.add(listing.store_product_id)
            yield listing
            scraped += 1

    def _parse_card(self, item: dict, category: str) -> RawListing | None:
        try:
            prod_id = item.get("prod_id")
            title = (item.get("title") or "").strip()
            if not prod_id or not title:
                return None

            subtexts = item.get("subtexts") or []
            detail = subtexts[0].strip() if subtexts else ""
            name = f"{title} {detail}".strip()

            if not self._matches_category(name.upper(), category):
                return None

            try:
                price = float(item.get("price"))
            except (TypeError, ValueError):
                return None
            if price <= 0:
                return None

            original_price = None
            for extra in subtexts[1:]:
                m = _DISCOUNT_RE.search(extra)
                if m:
                    try:
                        discount = float(m.group(1))
                        if discount > 0:
                            original_price = price + discount
                    except ValueError:
                        pass
                    break

            url = item.get("url") or f"{self.base_url}/product-details/{prod_id}"

            return RawListing(
                store_product_id=f"agora:{prod_id}",
                name=name,
                price=price,
                original_price=original_price,
                url=url,
                image_url=item.get("image"),
                in_stock=True,
                category_hint=category,
                raw=item,
            )
        except Exception as exc:  # noqa: BLE001
            logger.debug("[agora] failed to parse card: %s", exc)
            return None
