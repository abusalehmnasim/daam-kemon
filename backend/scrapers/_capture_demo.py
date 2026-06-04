"""Capture key demo screenshots for the README.

Runs against the live web container (web:3000) using the same Playwright
runtime the scrapers use. Saves PNGs to /app/_docs (we bind-mount this to
the host's docs/ dir at run time).

Usage:
    docker compose run --rm \\
        -v "${PWD}/docs:/app/_docs" \\
        api python -m scrapers._capture_demo
"""

from __future__ import annotations

import asyncio
from pathlib import Path

from playwright.async_api import async_playwright

OUT = Path("/app/_docs")
WEB = "http://web:3000"

VIEWPORT = {"width": 1280, "height": 800}


async def shot(page, path: Path) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    await page.wait_for_timeout(800)
    await page.screenshot(path=str(path), full_page=False)
    print(f"  saved {path}")


async def main() -> None:
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        ctx = await browser.new_context(viewport=VIEWPORT, device_scale_factor=2)
        page = await ctx.new_page()

        print("→ home")
        await page.goto(WEB, wait_until="networkidle", timeout=30_000)
        await shot(page, OUT / "01_home.png")

        print("→ search: 5L soybean oil  (aggregated buckets)")
        await page.goto(f"{WEB}/search?q=5L+soybean+oil", wait_until="networkidle", timeout=30_000)
        # Let the comparison rows render; scroll into view of the 5L bucket
        await page.wait_for_selector("article", timeout=15_000)
        await shot(page, OUT / "02_search_aggregated.png")

        print("→ categories browse page")
        await page.goto(f"{WEB}/categories", wait_until="networkidle", timeout=30_000)
        await shot(page, OUT / "03_categories.png")

        print("→ filtered: cooking_oil + soybean")
        await page.goto(
            f"{WEB}/search?category=cooking_oil&subcategory=soybean",
            wait_until="networkidle",
            timeout=30_000,
        )
        await page.wait_for_selector("article", timeout=15_000)
        await shot(page, OUT / "04_filtered.png")

        await ctx.close()
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
