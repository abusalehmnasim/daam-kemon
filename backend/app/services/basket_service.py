"""Translate API basket requests into the optimizer's domain objects, then back."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.basket_optimizer import BasketItem, Offering, optimize
from ..core.normalizer import normalize
from ..models import Product, Store
from ..schemas.basket import (
    BasketItemIn,
    BasketOptimizeResponse,
    StoreLineItemOut,
    StorePlanOut,
)


async def _resolve_query_to_products(session: AsyncSession, query: str) -> list[Product]:
    """A query-style basket item resolves to all products in the relevant
    category/subcategory at roughly the requested size. The optimizer will
    pick the cheapest qualifying offering per store."""
    np = normalize(query)
    if not np.category:
        return []
    stmt = select(Product).where(Product.category == np.category)
    if np.subcategory:
        stmt = stmt.where(Product.subcategory == np.subcategory)
    if np.base_unit_qty is not None:
        # ±5% size window for "5L oil" style queries
        low = np.base_unit_qty * 0.95
        high = np.base_unit_qty * 1.05
        stmt = stmt.where(Product.base_unit_qty.between(low, high))
    res = await session.execute(stmt)
    return list(res.scalars().unique().all())


async def _stores_info(session: AsyncSession, store_filter: list[str] | None) -> tuple[list[str], dict[str, str], dict[str, dict]]:
    stmt = select(Store).where(Store.active == True)  # noqa: E712
    if store_filter:
        stmt = stmt.where(Store.name.in_(store_filter))
    res = await session.execute(stmt)
    stores = list(res.scalars().all())
    names = [s.name for s in stores]
    display = {s.name: s.display_name for s in stores}
    fees = {s.name: s.delivery_config or {} for s in stores}
    return names, display, fees


async def optimize_basket(
    session: AsyncSession,
    items_in: list[BasketItemIn],
    store_filter: list[str] | None,
) -> BasketOptimizeResponse:
    store_names, store_display, fee_table = await _stores_info(session, store_filter)
    if not store_names:
        return BasketOptimizeResponse(single_store=None, split=[], split_savings=0.0, all_single_store=[])

    domain_items: list[BasketItem] = []
    unresolved: list[str] = []

    for idx, item in enumerate(items_in):
        # Resolve item -> a set of canonical Products to consider
        products: list[Product] = []
        label: str
        key: str

        if item.product_id is not None:
            res = await session.execute(select(Product).where(Product.id == item.product_id))
            p = res.scalar_one_or_none()
            if p is None:
                unresolved.append(item.query or f"product_id={item.product_id}")
                continue
            products = [p]
            label = p.name
            key = f"pid:{p.id}"
        elif item.query:
            products = await _resolve_query_to_products(session, item.query)
            if not products:
                unresolved.append(item.query)
                continue
            label = item.query
            key = f"q:{idx}:{item.query}"
        else:
            unresolved.append("(empty item)")
            continue

        # Collect every in-stock store offering across all resolved products
        offerings: list[Offering] = []
        for p in products:
            for sp in p.store_listings:
                if sp.store_name not in store_names:
                    continue
                offerings.append(Offering(
                    store=sp.store_name,
                    store_product_id=sp.id,
                    store_product_name=sp.store_product_name,
                    unit_price=float(sp.price),
                    in_stock=sp.in_stock,
                    confidence=float(sp.match_confidence) if sp.match_confidence else 1.0,
                ))
        if not offerings:
            unresolved.append(label)
            continue

        domain_items.append(BasketItem(
            key=key,
            label=label,
            quantity=float(item.quantity),
            offerings=offerings,
        ))

    if not domain_items:
        return BasketOptimizeResponse(
            single_store=None, split=[], split_savings=0.0,
            all_single_store=[], unresolved_items=unresolved,
        )

    result = optimize(domain_items, store_names, fee_table)

    def to_plan_out(plan) -> StorePlanOut:
        return StorePlanOut(
            store=plan.store,
            store_display_name=store_display.get(plan.store, plan.store),
            items=[
                StoreLineItemOut(
                    item_key=it.item_key,
                    label=it.label,
                    store_product_id=it.store_product_id,
                    store_product_name=it.store_product_name,
                    unit_price=it.unit_price,
                    quantity=it.quantity,
                    line_total=it.line_total,
                )
                for it in plan.items
            ],
            items_subtotal=round(plan.items_subtotal, 2),
            delivery_fee=round(plan.delivery_fee, 2),
            total=round(plan.total, 2),
            missing_items=plan.missing_items,
        )

    return BasketOptimizeResponse(
        single_store=to_plan_out(result.single_store) if result.single_store else None,
        split=[to_plan_out(p) for p in result.split],
        split_savings=round(result.split_savings, 2),
        all_single_store=[to_plan_out(p) for p in result.all_single_store],
        unresolved_items=unresolved,
    )
