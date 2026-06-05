"""
Base scraper.

Per-store scrapers are subclasses that implement `scrape_category` and yield
RawListing dicts. The base class provides:

  - Playwright lifecycle (browser, context, page)
  - Polite rate limiting (configurable per-store)
  - Retry with exponential backoff
  - Structured logging
  - A `run()` method that ties it all together and writes to the DB through
    a callback the runner provides.

We intentionally split "scrape raw listings" from "normalize + match + persist".
That makes scrapers easy to test (just yield dicts) and makes the pipeline
resilient: a scraper failure for one category doesn't poison the catalog.
"""

from __future__ import annotations

import abc
import asyncio
import logging
import random
from dataclasses import dataclass, field
from typing import AsyncIterator, Optional

logger = logging.getLogger(__name__)


@dataclass
class RawListing:
    """What a scraper emits per product."""
    store_product_id: str        # store's own SKU/slug
    name: str
    price: float
    url: Optional[str] = None
    image_url: Optional[str] = None
    in_stock: bool = True
    original_price: Optional[float] = None
    category_hint: Optional[str] = None   # which of our MVP categories the scraper looked up
    raw: dict = field(default_factory=dict)


class StoreScraper(abc.ABC):
    store_name: str
    display_name: str
    base_url: str

    # Categories the scraper knows how to hit. The runner picks from this.
    # The values are arbitrary — the scraper interprets them (URL slug,
    # search query, page id, whatever the store happens to use).
    category_targets: dict[str, list[str]] = {}

    # Polite defaults — override in subclass if a store needs gentler treatment.
    rate_limit_seconds: float = 1.5
    rate_limit_jitter: float = 0.5
    max_retries: int = 3
    request_timeout_ms: int = 30_000

    def __init__(self, headless: bool = True) -> None:
        self.headless = headless

    # --- Required hooks ---------------------------------------------------

    @abc.abstractmethod
    async def scrape_category(self, page, category: str, target: str) -> AsyncIterator[RawListing]:
        """Yield RawListing objects for one category target."""
        raise NotImplementedError

    # --- Helpers ----------------------------------------------------------

    async def _polite_wait(self) -> None:
        delay = self.rate_limit_seconds + random.uniform(0, self.rate_limit_jitter)
        await asyncio.sleep(delay)

    async def _with_retry(self, coro_factory, label: str):
        """Run `coro_factory()` with exponential backoff."""
        last_exc: Optional[BaseException] = None
        for attempt in range(self.max_retries):
            try:
                return await coro_factory()
            except Exception as exc:  # noqa: BLE001  scrapers see *every* error type
                last_exc = exc
                wait = 2 ** attempt + random.random()
                logger.warning("[%s] %s failed (attempt %d/%d): %s — retrying in %.1fs",
                               self.store_name, label, attempt + 1, self.max_retries, exc, wait)
                await asyncio.sleep(wait)
        assert last_exc is not None
        raise last_exc

    async def run(self, categories: list[str] | None = None) -> AsyncIterator[RawListing]:
        """Drive the scraper. Yields RawListing across all targeted categories.

        Defers Playwright import to call time so unit tests can import this
        module without playwright installed.
        """
        from playwright.async_api import async_playwright  # type: ignore

        cats = categories or list(self.category_targets.keys())
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=self.headless)
            context = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0 Safari/537.36"
                ),
                locale="en-US",
            )
            context.set_default_timeout(self.request_timeout_ms)
            page = await context.new_page()
            try:
                for cat in cats:
                    targets = self.category_targets.get(cat, [])
                    for target in targets:
                        logger.info("[%s] scraping %s -> %s", self.store_name, cat, target)
                        try:
                            async for listing in self.scrape_category(page, cat, target):
                                listing.category_hint = listing.category_hint or cat
                                yield listing
                            await self._polite_wait()
                        except Exception as exc:  # noqa: BLE001
                            logger.exception("[%s] category %s/%s failed: %s",
                                             self.store_name, cat, target, exc)
                            continue
            finally:
                await context.close()
                await browser.close()
