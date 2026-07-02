"""
Basket optimization.

A "basket item" is something the user wants — usually a (product_id, quantity)
pair, but could also be a category-level request ("5L oil, brand doesn't matter").

For each item we have N candidate store offerings (one per store, or several
if the matcher returned alternatives). The optimizer answers two questions:

  1. Which single store gives the cheapest total cart (incl. delivery)?
  2. Can splitting the cart across stores save enough to be worth the hassle?

The single-store answer is straightforward arithmetic. The split answer is the
classic "set cover with fixed costs" — NP-hard in general, but our N is tiny
(3 stores, ~20 items), so brute force over the 2^N - 1 non-empty subsets is
fine and gives an exact optimum. If we ever scale to 10+ stores we switch to
ILP; until then this code is correct and obvious.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations
from typing import Iterable, Optional


@dataclass(frozen=True)
class Offering:
    store: str
    store_product_id: int            # FK into store_products
    store_product_name: str
    unit_price: float                # per unit in BDT
    in_stock: bool
    confidence: float                # from the matcher; we may downrank low-conf offerings later


@dataclass
class BasketItem:
    key: str                         # opaque ID — could be product_id, or a category bucket
    label: str                       # human-readable, what we echo back ("5L Soybean Oil")
    quantity: float
    offerings: list[Offering]        # one per store (or several if alternatives)


@dataclass
class ItemPlan:
    item_key: str
    label: str
    store: str
    store_product_id: int
    store_product_name: str
    unit_price: float
    quantity: float

    @property
    def line_total(self) -> float:
        return self.unit_price * self.quantity


@dataclass
class StorePlan:
    store: str
    items: list[ItemPlan] = field(default_factory=list)
    delivery_fee: float = 0.0
    missing_items: list[str] = field(default_factory=list)  # item keys this store can't fulfill

    @property
    def items_subtotal(self) -> float:
        return sum(it.line_total for it in self.items)

    @property
    def total(self) -> float:
        return self.items_subtotal + self.delivery_fee


@dataclass
class OptimizationResult:
    single_store: Optional[StorePlan]              # best single-store cart (may have missing items)
    split: list[StorePlan]                         # optimal multi-store split
    split_savings: float                           # 0 if split is not better than single
    all_single_store: list[StorePlan]              # per-store breakdown, for the UI table


def _delivery_fee(store: str, subtotal: float, fee_table: dict[str, dict]) -> float:
    """Look up delivery fee for a store given the subtotal.

    fee_table[store] looks like:
        {"flat": 60} or {"tiers": [{"min": 0, "fee": 80}, {"min": 500, "fee": 0}]}
    A store with no entry has a 0 fee (we assume free delivery rather than blocking).
    """
    cfg = fee_table.get(store)
    if not cfg:
        return 0.0
    if "flat" in cfg:
        return float(cfg["flat"])
    tiers = sorted(cfg.get("tiers", []), key=lambda t: t["min"])
    applicable = 0.0
    for t in tiers:
        if subtotal >= t["min"]:
            applicable = float(t["fee"])
    return applicable


def _plan_for_stores(
    stores: Iterable[str],
    items: list[BasketItem],
    fee_table: dict[str, dict],
) -> list[StorePlan]:
    """For each store in `stores`, build a plan with all items it can fulfill.

    An item is "fulfilled" by the cheapest in-stock offering from that store.
    Items the store cannot fulfill go into missing_items (the caller decides
    what to do with them).
    """
    plans: dict[str, StorePlan] = {s: StorePlan(store=s) for s in stores}
    for item in items:
        # group offerings by store, pick the cheapest in-stock one per store
        per_store: dict[str, Offering] = {}
        for off in item.offerings:
            if not off.in_stock:
                continue
            if off.store not in plans:
                continue
            cur = per_store.get(off.store)
            if cur is None or off.unit_price < cur.unit_price:
                per_store[off.store] = off

        for store, plan in plans.items():
            off = per_store.get(store)
            if off is None:
                plan.missing_items.append(item.key)
                continue
            plan.items.append(ItemPlan(
                item_key=item.key,
                label=item.label,
                store=off.store,
                store_product_id=off.store_product_id,
                store_product_name=off.store_product_name,
                unit_price=off.unit_price,
                quantity=item.quantity,
            ))

    for plan in plans.values():
        plan.delivery_fee = _delivery_fee(plan.store, plan.items_subtotal, fee_table)

    return list(plans.values())


def optimize(
    items: list[BasketItem],
    stores: list[str],
    fee_table: dict[str, dict],
    *,
    min_split_savings_bdt: float = 30.0,
) -> OptimizationResult:
    """Compute single-store and optimal split plans.

    `min_split_savings_bdt` guards against suggesting a split that saves
    pocket change at the cost of dealing with two deliveries. Default 30 BDT
    is roughly the "is it worth my time" threshold for grocery shopping.
    """
    if not items:
        return OptimizationResult(None, [], 0.0, [])

    # 1. Per-store single-store plans (the user-facing comparison table)
    all_single = _plan_for_stores(stores, items, fee_table)

    # The best single-store cart: prefer one that fulfills *all* items;
    # only fall back to a partial cart if no store can fulfill the basket.
    full = [p for p in all_single if not p.missing_items]
    if full:
        best_single = min(full, key=lambda p: p.total)
    else:
        best_single = min(all_single, key=lambda p: (len(p.missing_items), p.total))

    # 2. Optimal split: for each non-empty subset of stores, compute the
    # minimum cost when each item is bought from the cheapest store *in that
    # subset*, then add the delivery fees of the subset. The subset whose
    # total is lowest (and that fulfills every item) wins.
    best_split: Optional[list[StorePlan]] = None
    best_split_total = float("inf")
    n = len(stores)
    for k in range(1, n + 1):
        for subset in combinations(stores, k):
            plans = _plan_for_stores(subset, items, fee_table)
            # Each item must be fulfilled by *some* store in the subset.
            all_keys = {it.key for it in items}
            fulfilled = {ip.item_key for p in plans for ip in p.items}
            if fulfilled != all_keys:
                continue
            # Greedy per-item choice: for each item, keep only the cheapest
            # store in the subset. (The plans returned above already did
            # "cheapest in store" per item; now we further trim to "cheapest
            # across the subset" per item.)
            cheapest_for_item: dict[str, ItemPlan] = {}
            for p in plans:
                for ip in p.items:
                    cur = cheapest_for_item.get(ip.item_key)
                    if cur is None or ip.unit_price < cur.unit_price:
                        cheapest_for_item[ip.item_key] = ip

            # Re-bucket by store and recompute delivery
            bucket: dict[str, StorePlan] = {s: StorePlan(store=s) for s in subset}
            for ip in cheapest_for_item.values():
                bucket[ip.store].items.append(ip)
            # Drop stores that ended up with no items (no delivery, no plan)
            bucket = {s: p for s, p in bucket.items() if p.items}
            for p in bucket.values():
                p.delivery_fee = _delivery_fee(p.store, p.items_subtotal, fee_table)

            subset_total = sum(p.total for p in bucket.values())
            if subset_total < best_split_total:
                best_split_total = subset_total
                best_split = list(bucket.values())

    if best_split is None:
        return OptimizationResult(best_single, [], 0.0, all_single)

    savings = best_single.total - best_split_total
    # Only apply the savings threshold when the single store actually fulfills the
    # WHOLE basket. If best_single is partial (missing items), comparing its total
    # against a complete split is apples-to-oranges — and suppressing the split
    # would hide the only plan that buys everything the user wants.
    if not best_single.missing_items and (savings < min_split_savings_bdt or len(best_split) == 1):
        return OptimizationResult(best_single, [], 0.0, all_single)
    if len(best_split) == 1:
        # A one-store "split" isn't a split.
        return OptimizationResult(best_single, [], 0.0, all_single)

    return OptimizationResult(best_single, best_split, max(savings, 0.0), all_single)
