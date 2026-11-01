"""Tests for the Shwapno scraper card parsing logic."""

from scrapers.shwapno import ShwapnoScraper


def test_shwapno_extract_with_name_el():
    scraper = ShwapnoScraper()
    item = {
        "href": "/rupchanda-soyabean-oil-1liter",
        "nameText": "Rupchanda Soyabean Oil 1Ltr.",
        "priceText": "৳204",
        "inner": "Most Picked\n\nDelivery 1-2 hours \nRupchanda Soyabean Oil 1Ltr.\n \n৳204\n Per Piece\nAdd to Bag",
        "img_src": "https://example.com/oil.webp",
    }
    listing = scraper._extract_card_data(item)
    assert listing is not None
    assert listing.store_product_id == "shwapno:rupchanda-soyabean-oil-1liter"
    assert listing.name == "Rupchanda Soyabean Oil 1Ltr."
    assert listing.price == 204.0
    assert listing.in_stock is True
    assert listing.image_url == "https://example.com/oil.webp"
    assert listing.url == "https://www.shwapno.com/rupchanda-soyabean-oil-1liter"


def test_shwapno_extract_fallback_strips_ribbon_and_delivery():
    scraper = ShwapnoScraper()
    item = {
        "href": "/fresh-soyabean-oil-5ltr",
        "nameText": None,
        "priceText": None,
        "inner": "Most Picked\n\nDelivery 1-2 hours \nFresh Soyabean Oil 5Ltr.\n \n৳1,000\n Per Piece\nAdd to Bag",
        "img_src": None,
    }
    listing = scraper._extract_card_data(item)
    assert listing is not None
    assert listing.store_product_id == "shwapno:fresh-soyabean-oil-5ltr"
    assert listing.name == "Fresh Soyabean Oil 5Ltr."
    assert listing.price == 1000.0
    assert listing.in_stock is True
