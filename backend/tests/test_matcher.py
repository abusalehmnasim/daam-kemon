from app.core.matcher import CandidateProduct, match
from app.core.normalizer import normalize


def _cand(id, name, brand, cat, sub, size_value, size_unit, base_qty, loose=False):
    return CandidateProduct(
        id=id, normalized_name=name, brand=brand, category=cat, subcategory=sub,
        size_value=size_value, size_unit=size_unit, base_unit_qty=base_qty, is_loose=loose,
    )


def test_exact_match_wins():
    candidates = [
        _cand(1, "soyabean oil", "rupchanda", "cooking_oil", "soybean", 5, "L", 5000),
        _cand(2, "soyabean oil", "fresh",     "cooking_oil", "soybean", 5, "L", 5000),
    ]
    np = normalize("Rupchanda Soyabean Oil 5L")
    r = match(np, candidates)
    assert r.product_id == 1
    assert r.confidence == 1.00
    assert r.method == "exact"


def test_loose_tier_respects_subcategory():
    # A loose miniket rice listing must NOT match a loose najirshail canonical —
    # different varieties, different prices. (Regression: the loose tier ignored
    # subcategory and collapsed them.)
    candidates = [
        _cand(1, "najirshail rice", None, "rice", "najirshail", 1, "KG", 1000, loose=True),
    ]
    np = normalize("Miniket Rice (Loose) 1 KG")
    assert np.is_loose and np.subcategory == "miniket"
    r = match(np, candidates)
    assert r.product_id != 1  # no false loose match across subcategories


def test_brand_tier_when_unit_differs():
    candidates = [
        _cand(1, "soyabean oil", "rupchanda", "cooking_oil", "soybean", 5000, "ML", 5000),
    ]
    np = normalize("Rupchanda Soyabean Oil 5L")
    r = match(np, candidates)
    assert r.product_id == 1
    # Same brand, same base quantity, but stored as ML — exact still applies
    # because base quantity AND canonical size_unit match (L). When they differ
    # we drop to BRAND tier.
    assert r.method in ("exact", "brand")


def test_category_tier_when_brand_unknown():
    candidates = [
        _cand(1, "soyabean oil", "fresh", "cooking_oil", "soybean", 5, "L", 5000),
    ]
    np = normalize("Soybean Oil 5L")  # no brand on the user side
    r = match(np, candidates)
    assert r.product_id == 1
    assert r.confidence == 0.70
    assert r.method == "category"


def test_loose_tier_matches_loose_only():
    # When loose subcategory + size match, the category tier (0.70) fires —
    # higher confidence than the bare "loose" fallback. The candidate filter
    # ensures we never link a loose listing to a packaged product.
    candidates = [
        _cand(1, "rice", None, "rice", "miniket", 1, "KG", 1000, loose=True),
        _cand(2, "rice", "rashid", "rice", "miniket", 1, "KG", 1000, loose=False),
    ]
    np = normalize("Miniket Rice (Loose) 1 KG")
    r = match(np, candidates)
    assert r.product_id == 1
    assert r.method in ("category", "loose")


def test_loose_bare_fallback_when_subcategory_missing():
    # No subcategory info on either side: still link to the loose candidate
    # via the LOOSE tier, not the packaged one.
    candidates = [
        _cand(1, "sugar", None, "sugar", None, 1, "KG", 1000, loose=True),
        _cand(2, "sugar", "city", "sugar", None, 1, "KG", 1000, loose=False),
    ]
    np = normalize("Sugar (loose) 1kg")
    r = match(np, candidates)
    assert r.product_id == 1
    assert r.method in ("category", "loose")


def test_unmatched_when_no_category():
    np = normalize("mysterious item 500g")
    r = match(np, [])
    assert r.method == "unmatched"
    assert r.product_id is None


def test_unmatched_when_size_off():
    candidates = [
        _cand(1, "soyabean oil", "rupchanda", "cooking_oil", "soybean", 5, "L", 5000),
    ]
    np = normalize("Rupchanda Soybean Oil 2L")
    r = match(np, candidates)
    assert r.product_id is None


def test_category_tier_does_not_cross_brands():
    # Real-world bug: when scraping "Pusti Soybean Oil 5L" with only Rupchanda
    # 5L Soybean as a candidate, the category tier was attaching the listing
    # to the Rupchanda canonical, corrupting brand attribution.
    candidates = [
        _cand(1, "soyabean oil", "rupchanda", "cooking_oil", "soybean", 5, "L", 5000),
    ]
    np = normalize("Pusti Soybean Oil 5L")
    r = match(np, candidates)
    assert r.product_id is None
    assert r.method == "unmatched"


def test_exact_does_not_cross_subcategories():
    # Same brand + same size in the same category, but different oil types —
    # must NOT collapse. This was a real bug in production: "Fresh Rice Bran
    # Oil 5L" was being merged into "Fresh Soybean Oil 5L".
    candidates = [
        _cand(1, "soyabean oil", "fresh", "cooking_oil", "soybean", 5, "L", 5000),
    ]
    np = normalize("Fresh Rice Bran Oil 5L")
    r = match(np, candidates)
    assert r.product_id is None
    assert r.method == "unmatched"
