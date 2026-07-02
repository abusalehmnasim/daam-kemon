"""Tests for the ingest match/create logic — specifically that persisted
match_confidence/method reflect the real matcher verdict (regression: they were
always 1.0/'exact' because a dead second matcher pass excluded its own product).

No DB: a tiny fake session feeds canned query results into _get_or_create_product.
"""

from types import SimpleNamespace

from app.core.matcher import CandidateProduct, match
from app.core.normalizer import normalize
from scrapers.runner import _get_or_create_product


class _Scalars:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return self._rows

    def unique(self):
        return self


class _Result:
    def __init__(self, rows=None, scalar=None):
        self._rows = rows or []
        self._scalar = scalar

    def scalars(self):
        return _Scalars(self._rows)

    def scalar_one_or_none(self):
        return self._scalar

    def scalar_one(self):
        return self._scalar


class _Session:
    def __init__(self, results):
        self._results = list(results)

    async def execute(self, *args, **kwargs):
        return self._results.pop(0) if self._results else _Result()

    def add(self, obj):
        pass

    async def flush(self):
        pass


async def test_orphan_listing_when_no_category():
    np = normalize("some random thing 500g")
    assert np.category is None
    product, conf, method = await _get_or_create_product(_Session([]), np)
    assert product is None
    assert conf == 0.0
    assert method == "unmatched"


async def test_new_canonical_is_tagged_new():
    np = normalize("Rupchanda Soybean Oil 5L")
    # No existing candidates -> matcher finds nothing -> a fresh canonical is made.
    sess = _Session([_Result(rows=[]), _Result(scalar=None)])
    product, conf, method = await _get_or_create_product(sess, np)
    assert product is not None
    assert conf == 1.0
    assert method == "new"


async def test_matched_product_stores_real_matcher_verdict():
    # Same brand+subcategory+base-qty but different unit -> brand tier (0.85),
    # which is >= the 0.85 ingest threshold so it attaches. The stored confidence
    # must be 0.85/"brand", NOT the old hardcoded 1.0/"exact".
    np = normalize("Rupchanda Soybean Oil 5L")
    fields = dict(
        id=7,
        normalized_name="rupchanda soybean oil",
        brand="rupchanda",
        category="cooking_oil",
        subcategory="soybean",
        size_value=5000,
        size_unit="ML",
        base_unit_qty=5000,
        is_loose=False,
    )
    expected = match(np, [CandidateProduct(**fields)])
    assert expected.product_id == 7 and 0.85 <= expected.confidence < 1.0

    cand = SimpleNamespace(**fields)
    sess = _Session([_Result(rows=[cand]), _Result(scalar=cand)])
    product, conf, method = await _get_or_create_product(sess, np)
    assert product is cand
    assert conf == expected.confidence
    assert method == expected.method
