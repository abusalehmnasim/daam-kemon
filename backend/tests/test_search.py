from app.services.search_service import _aggregate_groups, get_base_unit_qty
from app.schemas.product import ProductGroupOut, ProductOut, StoreOfferingOut


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


def test_get_base_unit_qty():
    assert get_base_unit_qty(5.0, "L") == 5000.0
    assert get_base_unit_qty(5.0, "KG") == 5000.0
    assert get_base_unit_qty(500.0, "ML") == 500.0
    assert get_base_unit_qty(250.0, "G") == 250.0
    assert get_base_unit_qty(12.0, "PCS") == 12.0
    assert get_base_unit_qty(None, "L") is None


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
