"use client";

import type { AggregatedGroup, AggregatedOffering } from "@/types";
import { api } from "@/lib/api";
import { add as addToBasket } from "@/lib/basketStore";
import { useMemo, useState } from "react";

function fmt(price: number | null | undefined) {
  if (price === null || price === undefined) return "—";
  return "৳ " + price.toLocaleString("en-BD", { maximumFractionDigits: 2 });
}

function ConfidenceBadge({ confidence }: { confidence: number | null }) {
  if (confidence == null || confidence >= 0.99) return null;
  const tier =
    confidence >= 0.85
      ? { label: "brand match", cls: "bg-blue-100 text-blue-800" }
      : confidence >= 0.7
      ? { label: "category match", cls: "bg-amber-100 text-amber-800" }
      : { label: "approximate", cls: "bg-gray-100 text-gray-700" };
  return (
    <span className={`text-[10px] uppercase tracking-wide px-1.5 py-0.5 rounded ${tier.cls}`}>
      {tier.label}
    </span>
  );
}

export function AggregatedGroupCard({ group }: { group: AggregatedGroup }) {
  const [addedKey, setAddedKey] = useState<string | null>(null);

  // Sub-group by brand so the user sees "all Rupchanda 5L oils across stores" together,
  // then can compare across brands. Brand-less rows go into a single "Unbranded" bucket.
  const byBrand = useMemo(() => {
    const m = new Map<string, AggregatedOffering[]>();
    for (const o of group.offerings) {
      const k = o.brand ? o.brand : "_unbranded";
      const arr = m.get(k) ?? [];
      arr.push(o);
      m.set(k, arr);
    }
    // Order brands by cheapest in-stock price
    const ordered = [...m.entries()].map(([brand, list]) => {
      const cheap = list.find((o) => o.in_stock)?.price ?? Infinity;
      return { brand, list, cheap };
    });
    ordered.sort((a, b) => a.cheap - b.cheap);
    return ordered;
  }, [group.offerings]);

  const handleAdd = (off: AggregatedOffering) => {
    addToBasket({
      productId: undefined,
      query: undefined,
      label: `${off.brand ? off.brand + " · " : ""}${group.display_name}`,
      quantity: 1,
    });
    setAddedKey(`${off.store_product_id}`);
    setTimeout(() => setAddedKey(null), 1500);
  };

  return (
    <article className="rounded-xl bg-white border border-gray-200 shadow-sm">
      <header className="px-4 py-3 border-b border-gray-100 flex items-baseline justify-between gap-3">
        <div>
          <h2 className="font-semibold text-base">{group.display_name}</h2>
          <p className="text-xs text-gray-500 mt-0.5">
            {group.offerings.length} offer{group.offerings.length === 1 ? "" : "s"} across{" "}
            {new Set(group.offerings.map((o) => o.store_name)).size} stores
            {" · "}
            {byBrand.filter((b) => b.brand !== "_unbranded").length} brand
            {byBrand.length === 1 ? "" : "s"}
          </p>
        </div>
        {group.cheapest_price !== null && (
          <div className="text-right shrink-0">
            <div className="text-[10px] uppercase text-gray-400 tracking-wide">from</div>
            <div className="text-lg font-bold text-brand">{fmt(group.cheapest_price)}</div>
            <div className="text-[10px] text-gray-500">
              {group.cheapest_brand} · {group.cheapest_store}
            </div>
          </div>
        )}
      </header>

      <div className="divide-y divide-gray-100">
        {byBrand.map(({ brand, list }) => (
          <div key={brand} className="px-4 py-2.5">
            <div className="text-xs font-medium text-gray-700 mb-1.5 flex items-center gap-2">
              <span className="capitalize">{brand === "_unbranded" ? "Unbranded / loose" : brand}</span>
            </div>
            <ul className="space-y-1.5">
              {list.map((o) => {
                const isCheapest =
                  o.in_stock && o.price === group.cheapest_price;
                return (
                  <li
                    key={o.store_product_id}
                    className="flex items-center justify-between gap-3 text-sm"
                  >
                    <div className="min-w-0 flex items-center gap-2">
                      <span className="font-medium">{o.store_display_name}</span>
                      {o.is_sponsored && (
                        <span className="text-[10px] uppercase tracking-wide bg-yellow-100 text-yellow-800 px-1.5 py-0.5 rounded">
                          sponsored
                        </span>
                      )}
                      <ConfidenceBadge confidence={o.match_confidence} />
                      <span className="text-xs text-gray-400 truncate hidden sm:inline">
                        {o.store_product_name}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      {!o.in_stock ? (
                        <span className="text-xs text-red-600">Out of stock</span>
                      ) : (
                        <span
                          className={`text-base font-semibold ${
                            isCheapest ? "text-brand" : ""
                          }`}
                        >
                          {fmt(o.price)}
                        </span>
                      )}
                      {o.original_price && o.original_price > o.price && (
                        <span className="text-xs text-gray-400 line-through">
                          {fmt(o.original_price)}
                        </span>
                      )}
                      <button
                        onClick={() => handleAdd(o)}
                        className="text-xs px-2 py-1 rounded border border-brand text-brand hover:bg-brand hover:text-white transition"
                      >
                        {addedKey === `${o.store_product_id}` ? "✓" : "+ Basket"}
                      </button>
                      <a
                        href={api.clickUrl(o.store_product_id)}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs px-2 py-1 rounded bg-gray-100 hover:bg-gray-200"
                      >
                        Visit
                      </a>
                    </div>
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </div>
    </article>
  );
}
