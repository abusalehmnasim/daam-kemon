from types import SimpleNamespace

from sqlalchemy import Select
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql.elements import TextClause

from app.schemas.product import ProductGroupOut, ProductOut, StoreOfferingOut
from app.services.search_service import (
    _aggregate_groups,
    _brand_hint_from_name,
    _store_display_map,
    get_base_unit_qty,
    reset_store_display_cache,
    search,
)


def _make_mock_group(prod_id: int, name: str, size_value: float, size_unit: str, category: str = "cooking_oil") -> ProductGroupOut:
    return ProductGroupOut(
        product=ProductOut(
            id=prod_id,
            name=name,
            brand="test_brand",
            category=category,
            subcategory="soybean",
            size_value=size_value,
            size_unit=size_unit,
            is_loose=False,
        ),
        offerings=[
            StoreOfferingOut(
                store_product_id=prod_id * 10,
                store_name="chaldal",
                store_display_name="Chaldal",
                name=f"{name} {size_value}{size_unit}",
                price=100.0 * size_value,
                in_stock=True,
            )
        ],
        cheapest_price=100.0 * size_value,
        cheapest_store="Chaldal",
    )


def test_brand_hint_only_returns_known_brands():
    # Product-type words and noise must NOT be surfaced as brands.
    assert _brand_hint_from_name("Sunflower Oil Deshi - 1 Litre", "cooking_oil") is None
    assert _brand_hint_from_name("EC Organic Sunflower oil 1 Liter Pet Bottle", "cooking_oil") is None
    # A real, known brand IS surfaced.
    assert _brand_hint_from_name("Rupchanda Soyabean Oil 5L", "cooking_oil") == "rupchanda"
    # Empty/None name is safe.
    assert _brand_hint_from_name("", "cooking_oil") is None


def test_get_base_unit_qty():
    assert get_base_unit_qty(5.0, "L") == 5000.0
    assert get_base_unit_qty(5.0, "KG") == 5000.0
    assert get_base_unit_qty(500.0, "ML") == 500.0
    assert get_base_unit_qty(250.0, "G") == 250.0
    assert get_base_unit_qty(12.0, "PCS") == 12.0
    assert get_base_unit_qty(None, "L") is None


def test_aggregate_offerings_carry_product_id():
    # Each aggregated offering must reference its canonical product so the UI
    # can link the row to /product/[slug].
    res = _aggregate_groups([_make_mock_group(42, "Oil 5L", 5.0, "L")], target_qty=None)
    assert res[0].offerings[0].product_id == 42


def test_aggregate_groups_sorting_without_target():
    # Setup groups with various sizes out of order
    groups = [
        _make_mock_group(1, "Oil 5L", 5.0, "L"),
        _make_mock_group(2, "Oil 1L", 1.0, "L"),
        _make_mock_group(3, "Oil 2L", 2.0, "L"),
    ]
    # No target_qty: should sort by size ascending (1L, 2L, 5L)
    res = _aggregate_groups(groups, target_qty=None)
    assert len(res) == 3
    assert res[0].size_value == 1.0
    assert res[1].size_value == 2.0
    assert res[2].size_value == 5.0


# ---- Round-trip collapse (fix: search latency = serial cross-region queries) ----


class _Result:
    """Canned result covering both `.all()` and `.scalars().unique().all()`."""

    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return self._rows

    def scalars(self):
        return self

    def unique(self):
        return self


class _RecordingSession:
    """Fake AsyncSession that records executed statements and replays canned
    results in order. No DB, no network."""

    def __init__(self, results):
        self._results = list(results)
        self.statements = []

    async def execute(self, stmt, params=None):
        self.statements.append(stmt)
        return self._results.pop(0) if self._results else _Result([])


def _fake_offering(sp_id: int, price: float):
    return SimpleNamespace(
        id=sp_id,
        store_name="chaldal",
        store_product_name="Some Oil 1L",
        price=price,
        original_price=None,
        in_stock=True,
        store_product_url="https://x",
        image_url=None,
        delivery_fee=None,
        match_confidence=None,
        match_method=None,
        raw=None,
    )


def _fake_product(pid: int):
    return SimpleNamespace(
        id=pid,
        name=f"Product {pid}",
        brand="test_brand",
        category="cooking_oil",
        subcategory="soybean",
        size_value=1.0,
        size_unit="L",
        is_loose=False,
        store_listings=[_fake_offering(pid * 10, 100.0)],
    )


async def test_trigram_path_makes_one_product_query_and_preserves_order():
    # Regression: the text-search path used to fetch ids via raw SQL and then
    # RE-FETCH the Product rows by id — a second, serial, cross-region round-trip
    # per search. It must now be a SINGLE product query. "randomxyz" resolves to
    # no category, forcing the trigram branch.
    reset_store_display_cache()
    products = [_fake_product(3), _fake_product(1), _fake_product(2)]
    session = _RecordingSession([
        _Result([("chaldal", "Chaldal")]),  # _store_display_map
        _Result(products),                   # single product query (was two)
    ])

    groups, _cat, _size = await search(session, "randomxyz")

    # Exactly two round-trips: store-display map + one product query.
    assert len(session.statements) == 2
    # The second statement is an ORM Select, NOT a raw "SELECT id FROM products".
    assert isinstance(session.statements[1], Select)
    assert not any(isinstance(s, TextClause) for s in session.statements)
    # Order returned by the DB (relevance order) is preserved, never re-sorted.
    assert [g.product.id for g in groups] == [3, 1, 2]
    # The WHERE must use the index-usable `%` operator, not a `similarity() > x`
    # predicate (which forces a seq scan and cannot use the GIN trgm indexes).
    where_sql = str(session.statements[1].whereclause.compile(dialect=postgresql.dialect()))
    assert "%" in where_sql
    assert "similarity(" not in where_sql.lower()


def test_trgm_threshold_constants_stay_in_sync():
    # The `%` operator's recall depends on the connection GUC set in database.py;
    # it must equal the threshold search reasons about, or results silently drift.
    from app.database import TRGM_SIMILARITY_THRESHOLD
    from app.services.search_service import TRGM_THRESHOLD

    assert TRGM_SIMILARITY_THRESHOLD == TRGM_THRESHOLD


async def test_store_display_map_is_cached_across_calls():
    # Regression: the store roster (~5 static rows) was fetched on EVERY search,
    # costing a cross-region round-trip. It must be served from an in-process
    # cache on the second call.
    reset_store_display_cache()
    session = _RecordingSession([_Result([("chaldal", "Chaldal")])])

    first = await _store_display_map(session)
    second = await _store_display_map(session)

    assert first == {"chaldal": "Chaldal"} == second
    assert len(session.statements) == 1  # second call hit the cache


def test_aggregate_groups_sorting_with_target():
    groups = [
        _make_mock_group(1, "Oil 1L", 1.0, "L"),
        _make_mock_group(2, "Oil 5L", 5.0, "L"),
        _make_mock_group(3, "Oil 2L", 2.0, "L"),
    ]
    # target_qty = 5000.0 (5L): should sort by closeness to 5L (5L, 2L, 1L)
    res = _aggregate_groups(groups, target_qty=5000.0)
    assert len(res) == 3
    assert res[0].size_value == 5.0
    assert res[1].size_value == 2.0
    assert res[2].size_value == 1.0

    # target_qty = 2000.0 (2L): should sort by closeness to 2L (2L, 1L, 5L)
    res2 = _aggregate_groups(groups, target_qty=2000.0)
    assert len(res2) == 3
    assert res2[0].size_value == 2.0
    # 1L is closer to 2L (diff = 1000) than 5L (diff = 3000)
    assert res2[1].size_value == 1.0
    assert res2[2].size_value == 5.0
