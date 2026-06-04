from app.core.basket_optimizer import BasketItem, Offering, optimize


FEES = {
    "chaldal":   {"tiers": [{"min": 0, "fee": 80}, {"min": 1500, "fee": 0}]},
    "shwapno":   {"tiers": [{"min": 0, "fee": 70}, {"min": 2000, "fee": 0}]},
    "pandamart": {"flat": 60},
}
STORES = ["chaldal", "shwapno", "pandamart"]


def _item(key, label, qty, *offerings):
    return BasketItem(
        key=key, label=label, quantity=qty,
        offerings=[Offering(store=s, store_product_id=spid, store_product_name=label,
                            unit_price=p, in_stock=True, confidence=1.0)
                   for s, spid, p in offerings],
    )


def test_single_store_picks_cheapest_full_cart():
    items = [
        _item("oil", "5L Oil",   1, ("chaldal", 1, 920), ("shwapno", 2, 905), ("pandamart", 3, 935)),
        _item("rice", "Rice 5kg", 1, ("chaldal", 4, 425), ("shwapno", 5, 420), ("pandamart", 6, 430)),
    ]
    res = optimize(items, STORES, FEES)
    # Shwapno is cheapest both items; subtotal 1325, no free-delivery threshold
    # crossed, so total = 1325 + 70 = 1395
    assert res.single_store is not None
    assert res.single_store.store == "shwapno"
    assert res.single_store.total == 1395


def test_split_proposed_only_when_savings_meaningful():
    # Chaldal is cheapest for oil, Pandamart for rice. Whether splitting is
    # worth it depends on the delivery fees and the min-savings threshold.
    items = [
        _item("oil",  "5L Oil",   1, ("chaldal", 1, 800), ("shwapno", 2, 905), ("pandamart", 3, 935)),
        _item("rice", "Rice 5kg", 1, ("chaldal", 4, 600), ("shwapno", 5, 420), ("pandamart", 6, 410)),
    ]
    res = optimize(items, STORES, FEES)
    assert res.single_store is not None
    if res.split:
        # If a split was proposed, it must actually save money beyond the threshold
        split_total = sum(p.total for p in res.split)
        assert res.single_store.total - split_total >= 30


def test_optimizer_handles_missing_items_gracefully():
    items = [
        _item("oil",  "5L Oil",  1, ("chaldal", 1, 900)),
        _item("rice", "Rice 5kg", 1, ("shwapno", 2, 420)),
    ]
    res = optimize(items, STORES, FEES)
    # No single store fulfills both. The best_single will be a partial cart;
    # the split should fulfill everything.
    assert res.single_store is not None
    assert len(res.single_store.missing_items) >= 1
    if res.split:
        all_keys = {ip.item_key for p in res.split for ip in p.items}
        assert all_keys == {"oil", "rice"}


def test_empty_basket_returns_empty_result():
    res = optimize([], STORES, FEES)
    assert res.single_store is None
    assert res.split == []
