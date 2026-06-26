"""API endpoint tests.

These exercise the FastAPI routing layer — URL/query validation, error paths
(404s), and response serialization — without a real database. The DB session
dependency is overridden with a lightweight fake, and the two service functions
that wrap Postgres-specific (pg_trgm) SQL are monkeypatched. Like the rest of
the suite, these tests need no DB and no network.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.database import get_session
from app.main import app
from app.schemas.basket import BasketOptimizeResponse
from app.schemas.product import ProductGroupOut, ProductOut
from app.schemas.search import AggregatedGroup


# --------------------------------------------------------------------------- #
# Fake async DB session
# --------------------------------------------------------------------------- #
class _Scalars:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return self._rows

    def unique(self):
        return self


class FakeResult:
    """Mimics the slice of the SQLAlchemy Result API the routes use."""

    def __init__(self, rows=None, scalar=None):
        self._rows = rows or []
        self._scalar = scalar

    def scalar_one_or_none(self):
        return self._scalar

    def scalars(self):
        return _Scalars(self._rows)

    def all(self):
        return self._rows


class FakeSession:
    """Returns the supplied results in order; falls back to an empty result.

    Empty result => scalar_one_or_none() is None and every list access is [],
    which is exactly what the 404 / empty-list paths need.
    """

    def __init__(self, results=None):
        self._results = list(results or [])

    async def execute(self, *args, **kwargs):
        if self._results:
            return self._results.pop(0)
        return FakeResult()

    def add(self, obj):  # used by /click
        pass

    async def commit(self):  # used by /click
        pass


@pytest.fixture
def client():
    # Default: every route gets an empty fake session, so nothing ever touches
    # a real engine. Individual tests replace this with seeded results.
    app.dependency_overrides[get_session] = lambda: FakeSession()
    test_client = TestClient(app)
    yield test_client
    app.dependency_overrides.clear()


def _use_session(session):
    app.dependency_overrides[get_session] = lambda: session


# --------------------------------------------------------------------------- #
# Meta endpoints
# --------------------------------------------------------------------------- #
def test_root(client):
    res = client.get("/")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_healthz(client):
    res = client.get("/healthz")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


# --------------------------------------------------------------------------- #
# Query / path validation (pure FastAPI, no DB access on the failure path)
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "url",
    [
        "/search?limit=0",       # below ge=1
        "/search?limit=201",     # above le=200
        "/products?limit=0",     # below ge=1
        "/products/abc",         # path param must be int
        "/admin/scrape_runs?limit=0",
        "/admin/scrape_runs?limit=999",
        "/click/abc",            # path param must be int
    ],
)
def test_validation_rejects_bad_params(client, url):
    assert client.get(url).status_code == 422


def test_basket_optimize_requires_body(client):
    # Missing body / missing required `items` => 422
    assert client.post("/basket/optimize").status_code == 422
    assert client.post("/basket/optimize", json={}).status_code == 422
    assert client.post("/basket/optimize", json={"items": "nope"}).status_code == 422


# --------------------------------------------------------------------------- #
# Error paths — 404s via empty fake session
# --------------------------------------------------------------------------- #
def test_get_product_not_found(client):
    res = client.get("/products/999999")
    assert res.status_code == 404
    assert res.json()["detail"] == "Product not found"


def test_click_listing_not_found(client):
    res = client.get("/click/999999")
    assert res.status_code == 404
    assert res.json()["detail"] == "Listing not found"


# --------------------------------------------------------------------------- #
# Success paths — serialization with seeded fake session
# --------------------------------------------------------------------------- #
def test_list_stores(client):
    store = SimpleNamespace(
        name="chaldal",
        display_name="Chaldal",
        base_url="https://chaldal.com",
        active=True,
    )
    _use_session(FakeSession([FakeResult(rows=[store])]))

    res = client.get("/stores")
    assert res.status_code == 200
    body = res.json()
    assert len(body) == 1
    assert body[0] == {
        "name": "chaldal",
        "display_name": "Chaldal",
        "base_url": "https://chaldal.com",
        "active": True,
    }


def test_list_stores_empty(client):
    res = client.get("/stores")
    assert res.status_code == 200
    assert res.json() == []


def test_list_products(client):
    product = SimpleNamespace(
        id=1,
        name="Fresh Soybean Oil 5L",
        brand="Fresh",
        category="cooking_oil",
        subcategory="soybean",
        size_value=5.0,
        size_unit="L",
        is_loose=False,
    )
    _use_session(FakeSession([FakeResult(rows=[product])]))

    res = client.get("/products")
    assert res.status_code == 200
    body = res.json()
    assert len(body) == 1
    assert body[0]["id"] == 1
    assert body[0]["name"] == "Fresh Soybean Oil 5L"
    assert body[0]["size_value"] == 5.0


def test_get_product_found(client, monkeypatch):
    # The found path delegates aggregation to two search_service helpers that
    # issue their own pg_trgm queries — patch them so we test only the route's
    # found-vs-404 branch and serialization.
    group = ProductGroupOut(
        product=ProductOut(
            id=1, name="Fresh Soybean Oil 5L", brand="Fresh",
            category="cooking_oil", subcategory="soybean",
            size_value=5.0, size_unit="L", is_loose=False,
        ),
        offerings=[],
        cheapest_price=890.0,
        cheapest_store="Shwapno",
    )

    async def fake_display_map(session):
        return {}

    async def fake_build_group(session, product, display):
        return group

    monkeypatch.setattr("app.api.products._store_display_map", fake_display_map)
    monkeypatch.setattr("app.api.products._build_group", fake_build_group)
    _use_session(FakeSession([FakeResult(scalar=SimpleNamespace(id=1))]))

    res = client.get("/products/1")
    assert res.status_code == 200
    body = res.json()
    assert body["product"]["id"] == 1
    assert body["cheapest_price"] == 890.0


def test_list_categories(client):
    # Empty fake session => zero counts, but the full vocabulary tree still
    # renders. Exercises the real categories_grouped() assembly.
    res = client.get("/categories")
    assert res.status_code == 200
    body = res.json()
    assert len(body) > 0
    first_group = body[0]
    assert "group" in first_group
    assert isinstance(first_group["categories"], list)
    assert first_group["categories"][0]["product_count"] == 0


def test_admin_scrape_runs_empty(client):
    res = client.get("/admin/scrape_runs")
    assert res.status_code == 200
    assert res.json() == []


def test_search_endpoint(client, monkeypatch):
    group = AggregatedGroup(
        category="cooking_oil",
        subcategory="soybean",
        display_name="5L Soybean Oil",
        size_value=5.0,
        size_unit="L",
        offerings=[],
        cheapest_price=890.0,
    )

    async def fake_aggregated_search(session, q, **kwargs):
        return ([group], [], "cooking_oil", "5L")

    monkeypatch.setattr("app.api.search.aggregated_search", fake_aggregated_search)

    res = client.get("/search", params={"q": "5L oil"})
    assert res.status_code == 200
    body = res.json()
    assert body["query"] == "5L oil"
    assert body["parsed_category"] == "cooking_oil"
    assert body["parsed_size"] == "5L"
    assert body["total_groups"] == 1
    assert len(body["groups"]) == 1
    assert body["groups"][0]["display_name"] == "5L Soybean Oil"


def test_basket_optimize(client, monkeypatch):
    response = BasketOptimizeResponse(
        single_store=None,
        split=[],
        split_savings=0.0,
        all_single_store=[],
        unresolved_items=["mystery item"],
    )

    async def fake_optimize_basket(session, items, stores):
        return response

    monkeypatch.setattr("app.api.basket.optimize_basket", fake_optimize_basket)

    res = client.post(
        "/basket/optimize",
        json={"items": [{"query": "5L oil", "quantity": 1}], "stores": None},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["split_savings"] == 0.0
    assert body["unresolved_items"] == ["mystery item"]
