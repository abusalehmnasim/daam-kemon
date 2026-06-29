"""Tests for the Unimart scraper parsing logic."""

from scrapers.unimart import UnimartScraper


def test_unimart_parse_regular_product():
    scraper = UnimartScraper()
    prod_data = {
        "id": 4325,
        "code": "0253692",
        "name": "Olitalia Sunflower Oil 1Ltr",
        "price": 550,
        "discount": 0,
        "discount_type": "percent",
        "status": 1,
        "temp_available": 1,
        "stock": 192,
        "image_full_url": "https://myadmin.unimart.online/storage/app/public/product/all_img/0253692.webp",
    }

    listing = scraper._parse_product(prod_data, "cooking_oil")
    assert listing is not None
    assert listing.store_product_id == "unimart:0253692"
    assert listing.name == "Olitalia Sunflower Oil 1Ltr"
    assert listing.price == 550.0
    assert listing.original_price is None
    assert listing.in_stock is True
    assert listing.image_url == "https://myadmin.unimart.online/storage/app/public/product/all_img/0253692.webp"
    assert listing.url == "https://unimart.online/"
    assert listing.category_hint == "cooking_oil"


def test_unimart_parse_discounted_product():
    scraper = UnimartScraper()

    # Amount discount
    prod_amount = {
        "id": 123,
        "code": "12345",
        "name": "Chefs Choice Mustard Oil 1000Ml",
        "price": 360,
        "discount": 25,
        "discount_type": "amount",
        "status": 1,
        "temp_available": 1,
        "stock": 10,
    }
    listing = scraper._parse_product(prod_amount, "cooking_oil")
    assert listing is not None
    assert listing.price == 335.0  # 360 - 25
    assert listing.original_price == 360.0

    # Percentage discount
    prod_percent = {
        "id": 124,
        "code": "12346",
        "name": "Discounted Oil",
        "price": 200,
        "discount": 10,
        "discount_type": "percent",
        "status": 1,
        "temp_available": 1,
        "stock": 10,
    }
    listing = scraper._parse_product(prod_percent, "cooking_oil")
    assert listing is not None
    assert listing.price == 180.0  # 200 * 0.9
    assert listing.original_price == 200.0


def test_unimart_parse_stock_status():
    scraper = UnimartScraper()

    # Out of stock due to status
    prod_status = {
        "id": 1,
        "name": "Test Item",
        "price": 100,
        "status": 0,
        "temp_available": 1,
        "stock": 10,
    }
    listing = scraper._parse_product(prod_status, "cooking_oil")
    assert listing is not None
    assert listing.in_stock is False

    # Out of stock due to temp_available
    prod_temp = {
        "id": 2,
        "name": "Test Item",
        "price": 100,
        "status": 1,
        "temp_available": 0,
        "stock": 10,
    }
    listing = scraper._parse_product(prod_temp, "cooking_oil")
    assert listing is not None
    assert listing.in_stock is False

    # Out of stock due to stock count
    prod_stock = {
        "id": 3,
        "name": "Test Item",
        "price": 100,
        "status": 1,
        "temp_available": 1,
        "stock": 0,
    }
    listing = scraper._parse_product(prod_stock, "cooking_oil")
    assert listing is not None
    assert listing.in_stock is False

    # Stock is None (assume in stock)
    prod_none_stock = {
        "id": 4,
        "name": "Test Item",
        "price": 100,
        "status": 1,
        "temp_available": 1,
        "stock": None,
    }
    listing = scraper._parse_product(prod_none_stock, "cooking_oil")
    assert listing is not None
    assert listing.in_stock is True
