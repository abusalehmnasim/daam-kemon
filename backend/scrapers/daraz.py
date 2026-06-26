"""
Daraz scraper.

Daraz (daraz.com.bd) runs the Alibaba/Lazada platform behind Akamai anti-bot.
The SEO *category* paths (e.g. /cooking-oils/) redirect bots to an error page,
but the *search* endpoint returns clean JSON for a plain request with a browser
User-Agent:

    GET https://www.daraz.com.bd/catalog/?ajax=true&q=<query>&page=<n>
    -> { "mods": { "listItems": [ {name, itemId, price, ...}, ... ] },
         "mainInfo": { "page", "totalResults", "noMorePages", ... } }

So, unlike the category-id scrapers, Daraz `category_targets` values are SEARCH
QUERIES. Daraz is a marketplace, so results are noisy (third-party sellers,
"No Brand", unrelated items). We deliberately keep queries specific and let the
normalizer + matcher filter: anything that doesn't resolve to a known grocery
category is stored as an orphan listing and never surfaces in aggregated search.

If anti-bot ever tightens and bare requests start returning the HTML error page,
the fallback is to warm cookies via the inherited Playwright context first; the
parser below stays the same.
"""

from __future__ import annotations

import logging
import re
from typing import AsyncIterator
from urllib.parse import quote_plus

import httpx

from .base import RawListing, StoreScraper

logger = logging.getLogger(__name__)

# A quantity expressed as a volume — used to keep cooking oil / liquid milk and
# reject canned goods "in oil" (those are sold by weight, e.g. "Tuna ... 165G").
_VOLUME_RE = re.compile(r"\b\d+(?:\.\d+)?\s*(?:ml|l|ltr|litre|liter)\b", re.IGNORECASE)


class DarazScraper(StoreScraper):
    store_name = "daraz"
    display_name = "Daraz"
    base_url = "https://www.daraz.com.bd"

    # category key -> list of search queries. Kept specific to limit marketplace
    # noise; the normalizer still does the final category/brand/size extraction.
    category_targets = {
        "cooking_oil":  ["soybean oil", "sunflower oil", "mustard oil"],
        "rice":         ["miniket rice", "basmati rice", "chinigura rice"],
        "sugar":        ["sugar"],
        "lentils":      ["masoor dal", "moong dal"],
        "salt":         ["edible salt"],
        "flour":        ["atta flour", "maida flour"],
        "milk":         ["uht liquid milk"],
        "powdered_milk":["milk powder"],
        "tea":          ["tea"],
        "spices":       ["turmeric powder", "chili powder"],
        "noodles":      ["instant noodles"],
        "biscuits":     ["biscuits"],
    }

    API_PATH = "/catalog/"
    PAGE_SIZE = 40
    PER_QUERY_CAP = 80  # ~2 pages; deeper pages get noisier on a marketplace

    # --- Relevance filtering -------------------------------------------------
    # Daraz is a marketplace, so a search for "soybean oil" also returns canned
    # tuna *in* soybean oil, hair oil, tea pots, etc. The runner forces our
    # category_hint when the normalizer can't decide, so junk would be filed
    # under the wrong category. We drop obviously-wrong items here, before they
    # ever enter the pipeline. These are deliberately conservative keyword lists.

    # If any of these substrings appears in the name, reject the item.
    DENY_KEYWORDS: dict[str, tuple[str, ...]] = {
        "cooking_oil":  ("tuna", "fish", "sardine", "mackerel", "seafood", "hair",
                         "massage", "essential", "engine", "lubricant", "paint",
                         "soap", "balm", "candle", "diffuser", "lamp", "skin",
                         "face", "body lotion", "lip"),
        "rice":         ("cooker", "paper", "maker", "crispy", "cracker", "snack",
                         "noodle", "press", "light", "puffed", "cake", "mat"),
        "sugar":        ("free", "scrub", "wax", "soap", "candy", "cosmetic", "toy"),
        "lentils":      ("soup", "snack", "papad", "fried", "sprout", "plant", "seed kit"),
        "salt":         ("lamp", "bath", "scrub", "epsom"),
        "flour":        ("machine", "maker", "mill ", "supplement"),
        "milk":         ("soap", "cream", "bath", "frother", "lotion", "face"),
        "powdered_milk":("soap", "cream", "bath", "frother", "lotion", "face"),
        "tea":          ("pot", "cup", "mug", "kettle", "tray", "infuser", "table",
                         "strainer", "maker", "tree oil", "tree ", "set", "jug",
                         "flask", "warmer", "light"),
        "spices":       ("soap", "cream", "face", "mask", "capsule", "supplement",
                         "tablet", "plant", "seed", "oil"),
        "noodles":      ("maker", "bowl", "toy", "press"),
        "biscuits":     ("jar", "tin", "cutter", "mould", "maker", "toy", "plush"),
    }

    # Categories where the name must contain a volume quantity (ml/L). Edible oil
    # and liquid milk are sold by volume; "in soybean oil 165G" canned fish is not.
    REQUIRE_VOLUME: frozenset[str] = frozenset({"cooking_oil", "milk"})

    def _is_relevant(self, name: str, category: str) -> bool:
        low = name.lower()
        if any(k in low for k in self.DENY_KEYWORDS.get(category, ())):
            return False
        if category in self.REQUIRE_VOLUME and not _VOLUME_RE.search(low):
            return False
        return True

    def _headers(self) -> dict[str, str]:
        return {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0 Safari/537.36"
            ),
            "Accept": "application/json, text/plain, */*",
            "Referer": f"{self.base_url}/",
            "X-Requested-With": "XMLHttpRequest",
        }

    async def scrape_category(self, page, category: str, target: str) -> AsyncIterator[RawListing]:
        # `target` is a search query.
        page_num = 1
        scraped = 0
        seen: set[str] = set()

        async with httpx.AsyncClient(follow_redirects=True) as client:
            while scraped < self.PER_QUERY_CAP:
                url = (
                    f"{self.base_url}{self.API_PATH}?ajax=true"
                    f"&q={quote_plus(target)}&page={page_num}"
                )
                try:
                    resp = await client.get(url, headers=self._headers(), timeout=20.0)
                except Exception as exc:
                    logger.warning("[daraz] request failed for %r: %s", target, exc)
                    break

                if resp.status_code != 200:
                    logger.warning("[daraz] %r page %d -> status %d", target, page_num, resp.status_code)
                    break

                try:
                    data = resp.json()
                except Exception:
                    # Anti-bot served the HTML error page instead of JSON.
                    logger.warning("[daraz] non-JSON response for %r (anti-bot?) — stopping", target)
                    break

                items = (data.get("mods") or {}).get("listItems") or []
                if not items:
                    break

                for it in items:
                    listing = self._parse_item(it, category)
                    if listing and listing.store_product_id not in seen:
                        seen.add(listing.store_product_id)
                        yield listing
                        scraped += 1
                        if scraped >= self.PER_QUERY_CAP:
                            break

                main = data.get("mainInfo") or {}
                if main.get("noMorePages") or len(items) < self.PAGE_SIZE:
                    break
                page_num += 1
                await self._polite_wait()

    def _parse_item(self, it: dict, category: str) -> RawListing | None:
        try:
            item_id = it.get("itemId") or it.get("nid")
            name = (it.get("name") or "").strip()
            if not item_id or not name:
                return None

            # Drop marketplace noise that doesn't belong in this category.
            if not self._is_relevant(name, category):
                return None

            try:
                price = float(it.get("price"))
            except (TypeError, ValueError):
                return None
            if price <= 0:
                return None

            original_price = None
            try:
                orig = float(it.get("originalPrice"))
                if orig > price:
                    original_price = orig
            except (TypeError, ValueError):
                pass

            in_stock = bool(it.get("inStock", True))

            url = it.get("itemUrl") or ""
            if url.startswith("//"):
                url = "https:" + url
            elif url.startswith("/"):
                url = self.base_url + url
            elif not url:
                url = f"{self.base_url}/"

            return RawListing(
                store_product_id=f"daraz:{item_id}",
                name=name,
                price=price,
                original_price=original_price,
                url=url,
                image_url=it.get("image"),
                in_stock=in_stock,
                category_hint=category,
                raw=it,
            )
        except Exception as exc:  # noqa: BLE001
            logger.debug("[daraz] failed to parse item: %s", exc)
            return None
