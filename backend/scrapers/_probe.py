"""Targeted probe: find the wrapping product card by walking up from a known
inner selector (e.g. h4.product-name) until we find an ancestor that also
contains a price-like element. Print the full card html.

Usage:
    python -m scrapers._probe <url> <inner_selector>
"""

from __future__ import annotations

import asyncio
import sys

from playwright.async_api import async_playwright


async def probe(url: str, inner: str) -> None:
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        ctx = await browser.new_context(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/124.0 Safari/537.36 DaamKemonBot/0.1",
        )
        page = await ctx.new_page()
        try:
            resp = await page.goto(url, wait_until="domcontentloaded", timeout=25_000)
        except Exception as exc:
            print(f"goto error: {exc}")
            return
        print(f"status={resp.status if resp else 'none'}, final url={page.url}")
        await page.wait_for_timeout(4500)
        await page.mouse.wheel(0, 2500)
        await page.wait_for_timeout(2000)

        cards = await page.eval_on_selector_all(
            inner,
            r"""(els) => els.slice(0, 4).map(inner => {
                // Walk up until we hit an ancestor whose text contains
                // a digit string and the inner text. That's the card.
                let cur = inner;
                for (let d = 0; d < 10 && cur; d++) {
                    cur = cur.parentElement;
                    if (!cur) break;
                    const t = cur.innerText || '';
                    if (/\d{2,}/.test(t) && t.length > inner.innerText.length && t.length < 600) {
                        return {
                            depth: d + 1,
                            tag: cur.tagName.toLowerCase(),
                            cls: cur.className,
                            text: t.replace(/\s+/g, ' ').slice(0, 320),
                            html: cur.outerHTML.slice(0, 3000),
                        };
                    }
                }
                return null;
            }).filter(Boolean)"""
        )
        print(f"\n--- {len(cards)} wrapper cards (ancestors of {inner!r}) ---")
        for i, c in enumerate(cards):
            print(f"\n[{i}] depth={c['depth']} <{c['tag']} class='{c['cls'][:140]}'>")
            print(f"    text: {c['text']!r}")
            print(f"    html: {c['html']}")

        await ctx.close()
        await browser.close()


def main() -> None:
    if len(sys.argv) < 3:
        print("usage: python -m scrapers._probe <url> <inner_selector>")
        sys.exit(2)
    asyncio.run(probe(sys.argv[1], sys.argv[2]))


if __name__ == "__main__":
    main()
