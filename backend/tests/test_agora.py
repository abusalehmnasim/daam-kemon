"""Tests for the Agora scraper parsing logic.

Card shapes are taken from real `/products/<slug>` responses. No network.
"""

import httpx

from scrapers.agora import AgoraScraper


def test_agora_parse_regular_item():
    scraper = AgoraScraper()
    # A genuine sugar card with a discount badge, from /products/commodities.
    item = {
        "prod_id": "10995",
        "title": "Green Field",
        "subtexts": ["Green field sugar loose", "4 TK OFF"],
        "price": "101",
        "url": "https://agorasuperstores.com/product-details/green-field?prod_id=10995",
        "image": "https://agorastorageacount.blob.core.windows.net/img/product/10995.png",
    }

    listing = scraper._parse_card(item, "sugar")
    assert listing is not None
    assert listing.store_product_id == "agora:10995"
    assert listing.name == "Green Field Green field sugar loose"
    assert listing.price == 101.0
    assert listing.original_price == 105.0  # price + discount amount
    assert listing.in_stock is True
    assert listing.url.endswith("prod_id=10995")
    assert listing.category_hint == "sugar"


def test_agora_no_discount_drops_original_price():
    scraper = AgoraScraper()
    # Empty second subtext is how a no-discount card renders.
    item = {
        "prod_id": "11018",
        "title": "Green Field",
        "subtexts": ["Green field miniket muzammel rashid loos", ""],
        "price": "85",
        "url": "https://agorasuperstores.com/product-details/green-field?prod_id=11018",
        "image": "https://agorastorageacount.blob.core.windows.net/img/product/11018.png",
    }
    listing = scraper._parse_card(item, "rice")
    assert listing is not None
    assert listing.price == 85.0
    assert listing.original_price is None


def test_agora_category_keyword_filter():
    scraper = AgoraScraper()
    # commodities page mixes oil/rice/sugar/lentils/flour/salt on one page —
    # the same card must only pass for its real category.
    oil = {"prod_id": "1", "title": "Rupchanda", "subtexts": ["Rupchanda soyabean oil 2ltr"], "price": "398"}
    assert scraper._parse_card(oil, "cooking_oil") is not None
    assert scraper._parse_card(oil, "rice") is None

    rice = {"prod_id": "2", "title": "Green Field", "subtexts": ["Green field miniket rice premium"], "price": "75"}
    assert scraper._parse_card(rice, "rice") is not None
    assert scraper._parse_card(rice, "sugar") is None


def test_agora_milk_vs_powdered_milk_split():
    scraper = AgoraScraper()
    liquid = {"prod_id": "3", "title": "Aarong", "subtexts": ["Aarong milk 1ltr"], "price": "95"}
    powder = {"prod_id": "4", "title": "Nido", "subtexts": ["Nido full cream milk powder 400g"], "price": "560"}

    assert scraper._parse_card(liquid, "milk") is not None
    assert scraper._parse_card(liquid, "powdered_milk") is None
    assert scraper._parse_card(powder, "powdered_milk") is not None
    assert scraper._parse_card(powder, "milk") is None


def test_agora_rejects_bad_items():
    scraper = AgoraScraper()
    # Missing prod_id
    assert scraper._parse_card({"title": "X", "subtexts": [], "price": "10"}, "rice") is None
    # Missing/blank title
    assert scraper._parse_card({"prod_id": "5", "title": "  ", "subtexts": [], "price": "10"}, "rice") is None
    # Non-numeric price
    assert scraper._parse_card({"prod_id": "6", "title": "X", "subtexts": [], "price": "N/A"}, "rice") is None
    # Zero / negative price
    assert scraper._parse_card({"prod_id": "7", "title": "X", "subtexts": [], "price": "0"}, "rice") is None


def test_agora_split_cards_isolates_each_card():
    html = (
        '<div class="veg-card">'
        '<a href="https://agorasuperstores.com/product-details/a?prod_id=1" class="text-decoration-none">'
        '<img src="https://x/1.png"><h5 class="allProduct-title">A</h5>'
        '<p class="allProduct-subtext text-muted">Desc A</p>'
        '<p class="allProduct-subtext"></p>'
        '<p class="allProduct-price" data-price="10">Tk 10</p></a>'
        '<button data-prod-id="1"></button></div>'
        '<div class="veg-card">'
        '<a href="https://agorasuperstores.com/product-details/b?prod_id=2" class="text-decoration-none">'
        '<img src="https://x/2.png"><h5 class="allProduct-title">B</h5>'
        '<p class="allProduct-subtext text-muted">Desc B</p>'
        '<p class="allProduct-subtext">2 TK OFF</p>'
        '<p class="allProduct-price" data-price="20">Tk 20</p></a>'
        '<button data-prod-id="2"></button></div>'
    )
    blocks = AgoraScraper._split_cards(html)
    assert len(blocks) == 2

    first = AgoraScraper._extract_card(blocks[0])
    assert first["prod_id"] == "1"
    assert first["title"] == "A"
    assert first["price"] == "10"
    assert first["subtexts"] == ["Desc A", ""]

    second = AgoraScraper._extract_card(blocks[1])
    assert second["prod_id"] == "2"
    assert second["subtexts"] == ["Desc B", "2 TK OFF"]


async def test_agora_failed_fetch_does_not_poison_cache():
    """A failed fetch for a shared slug (e.g. "commodities", used by six
    categories) must not cache []  — otherwise every other category sharing
    that slug silently gets zero listings for the rest of the run."""
    scraper = AgoraScraper()
    calls = {"n": 0}

    async def flaky_with_retry(coro_factory, label):
        calls["n"] += 1
        if calls["n"] == 1:
            raise httpx.ConnectError("boom")
        return httpx.Response(
            200,
            text=(
                '<div class="veg-card">'
                '<a href="https://x/a?prod_id=1" class="text-decoration-none">'
                '<img src="https://x/1.png"><h5 class="allProduct-title">A</h5>'
                '<p class="allProduct-subtext">Desc A</p>'
                '<p class="allProduct-subtext"></p>'
                '<p class="allProduct-price" data-price="10">Tk 10</p></a>'
                '<button data-prod-id="1"></button></div>'
            ),
        )

    scraper._with_retry = flaky_with_retry

    first = await scraper._fetch_cards("commodities")
    assert first == []
    assert "commodities" not in scraper._page_cache

    second = await scraper._fetch_cards("commodities")
    assert len(second) == 1
    assert second[0]["prod_id"] == "1"
    assert scraper._page_cache["commodities"] == second
