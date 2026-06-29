"""Tests for the Daraz scraper parsing logic.

Item shapes are taken from a real catalog/?ajax=true response. No network.
"""

from scrapers.daraz import DarazScraper


def test_daraz_parse_regular_item():
    scraper = DarazScraper()
    # A genuine cooking oil with a volume size (passes the relevance filter).
    item = {
        "itemId": 323114931,
        "name": "Ambassador Spanish Olive Oil - 150ml",
        "price": "615",
        "priceShow": "৳ 615",
        "originalPrice": "677",
        "discount": "9% Off",
        "inStock": True,
        "brandName": "No Brand",
        "itemUrl": "//www.daraz.com.bd/products/ambassador-150ml-i323114931.html",
        "image": "https://static-01.daraz.com.bd/p/87fe18e45c378d55eeb2e1866997d0bd.jpg",
    }

    listing = scraper._parse_item(item, "cooking_oil")
    assert listing is not None
    assert listing.store_product_id == "daraz:323114931"
    assert listing.name == "Ambassador Spanish Olive Oil - 150ml"
    assert listing.price == 615.0
    assert listing.original_price == 677.0  # original > price, so kept
    assert listing.in_stock is True
    # protocol-relative URL gets https: prefixed
    assert listing.url == "https://www.daraz.com.bd/products/ambassador-150ml-i323114931.html"
    assert listing.image_url.endswith(".jpg")
    assert listing.category_hint == "cooking_oil"


def test_daraz_relevance_filter_drops_marketplace_noise():
    scraper = DarazScraper()

    # Real noise from a live "soybean oil" search: canned tuna in soybean oil.
    tuna = {
        "itemId": 261472762,
        "name": "Nautilus Lite Tuna Chunk In Soybean Oil 165gm",
        "price": "364",
        "itemUrl": "//www.daraz.com.bd/products/165-i261472762.html",
    }
    assert scraper._parse_item(tuna, "cooking_oil") is None  # 'tuna' denied

    # Truncated canned-fish name with no fish word, but sold by weight (165G):
    # rejected because cooking_oil requires a volume unit.
    canned = {
        "itemId": 460434230,
        "name": "In Soybean Oil 165G",
        "price": "261",
        "itemUrl": "//www.daraz.com.bd/products/-i460434230.html",
    }
    assert scraper._parse_item(canned, "cooking_oil") is None

    # Other categories use keyword deny lists.
    teapot = {"itemId": 9, "name": "Ceramic Tea Pot 1000ml", "price": "450"}
    assert scraper._parse_item(teapot, "tea") is None  # 'pot' denied

    hair_oil = {"itemId": 10, "name": "Hair Oil 200ml", "price": "150"}
    assert scraper._parse_item(hair_oil, "cooking_oil") is None  # 'hair' denied

    # A real volume-based cooking oil still passes.
    real_oil = {"itemId": 11, "name": "Rupchanda Soybean Oil 5 Litre", "price": "905"}
    assert scraper._parse_item(real_oil, "cooking_oil") is not None


def test_daraz_no_discount_drops_original_price():
    scraper = DarazScraper()
    # originalPrice <= price => not a real discount, original_price stays None
    item = {
        "itemId": 1,
        "name": "Some Oil 1L",
        "price": "200",
        "originalPrice": "200",
        "inStock": True,
        "itemUrl": "//www.daraz.com.bd/products/x-i1.html",
    }
    listing = scraper._parse_item(item, "cooking_oil")
    assert listing is not None
    assert listing.price == 200.0
    assert listing.original_price is None


def test_daraz_out_of_stock():
    scraper = DarazScraper()
    item = {
        "itemId": 2,
        "name": "Rice 5kg",
        "price": "550",
        "inStock": False,
        "itemUrl": "//www.daraz.com.bd/products/x-i2.html",
    }
    listing = scraper._parse_item(item, "rice")
    assert listing is not None
    assert listing.in_stock is False


def test_daraz_rejects_bad_items():
    scraper = DarazScraper()
    # Missing id
    assert scraper._parse_item({"name": "X", "price": "10"}, "rice") is None
    # Missing/blank name
    assert scraper._parse_item({"itemId": 3, "name": "  ", "price": "10"}, "rice") is None
    # Non-numeric price
    assert scraper._parse_item({"itemId": 4, "name": "X", "price": "N/A"}, "rice") is None
    # Zero / negative price
    assert scraper._parse_item({"itemId": 5, "name": "X", "price": "0"}, "rice") is None


def test_daraz_absolute_and_relative_urls():
    scraper = DarazScraper()
    # already-absolute itemUrl is left intact
    item = {
        "itemId": 6,
        "name": "Sugar 1kg",
        "price": "120",
        "itemUrl": "https://www.daraz.com.bd/products/sugar-i6.html",
    }
    assert scraper._parse_item(item, "sugar").url == "https://www.daraz.com.bd/products/sugar-i6.html"
    # missing itemUrl falls back to base_url
    item2 = {"itemId": 7, "name": "Salt 1kg", "price": "30"}
    assert scraper._parse_item(item2, "salt").url == "https://www.daraz.com.bd/"
