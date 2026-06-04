"""Tests for the normalizer. These pin down behavior that matters at ingest."""

from app.core.normalizer import normalize


def test_rupchanda_5l_variants_normalize_consistently():
    a = normalize("Rupchanda Soyabean Oil (5 Litre)")
    b = normalize("Rupchanda Soybean Oil 5L")
    c = normalize("Rupchanda Cooking Oil 5000 ml")
    assert a.category == "cooking_oil"
    assert a.brand == "rupchanda" == b.brand == c.brand
    # Size collapses to the same base quantity regardless of unit notation
    assert a.base_unit_qty == 5000.0
    assert b.base_unit_qty == 5000.0
    assert c.base_unit_qty == 5000.0


def test_bengali_numerals_and_units():
    n = normalize("রূপচাঁদা সয়াবিন তেল ৫ লিটার")
    assert n.category == "cooking_oil"
    assert n.base_unit_qty == 5000.0
    assert n.size_unit == "L"


def test_loose_goods_flagged():
    n = normalize("Miniket Rice (Loose) 1 KG")
    assert n.category == "rice"
    assert n.subcategory == "miniket"
    assert n.is_loose is True
    assert n.base_unit_qty == 1000.0


def test_eggs_count_in_pcs():
    n = normalize("Kazi Farms Chicken Egg 12pcs")
    assert n.category == "eggs"
    assert n.brand == "kazi"
    assert n.size_unit == "PCS"
    assert n.base_unit_qty == 12.0


def test_unknown_category_returns_none():
    n = normalize("Some random thing 500g")
    assert n.category is None
    assert n.base_unit_qty == 500.0  # size still parsed


def test_kg_g_size_collapse():
    a = normalize("Fresh Atta 2kg")
    b = normalize("Fresh Atta 2000 grams")
    assert a.base_unit_qty == b.base_unit_qty == 2000.0


def test_brand_stripped_from_normalized_name():
    n = normalize("Rupchanda Soyabean Oil 5L")
    assert "rupchanda" not in n.normalized_name
    assert "soyabean" in n.normalized_name or "oil" in n.normalized_name
