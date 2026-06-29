"use client";

import type { ProductGroupOut, StoreOfferingOut } from "@/types";
import { api } from "@/lib/api";
import { add as addToBasket } from "@/lib/basketStore";
import { useState } from "react";

function fmt(price: number | null) {
  if (price === null || price === undefined) return "—";
  return "৳ " + price.toLocaleString("en-BD", { maximumFractionDigits: 2 });
}

function ConfidenceBadge({
  confidence,
  method,
}: {
  confidence: number | null;
  method: string | null;
}) {
  if (confidence == null || confidence >= 0.99) return null;
  const tier =
    confidence >= 0.85
      ? { label: "brand match", cls: "bg-blue-100 text-blue-800" }
      : confidence >= 0.7
        ? { label: "category match", cls: "bg-amber-100 text-amber-800" }
        : { label: "approximate", cls: "bg-gray-100 text-gray-700" };
  return (
    <span
      className={`text-[10px] uppercase tracking-wide px-1.5 py-0.5 rounded ${tier.cls}`}
      title={method ?? undefined}
    >
      {tier.label}
    </span>
  );
}

export function PriceComparison({ group }: { group: ProductGroupOut }) {
  const [added, setAdded] = useState(false);
  const sorted: StoreOfferingOut[] = [...group.offerings].sort(
    (a, b) => Number(!a.in_stock) - Number(!b.in_stock) || a.price - b.price
  );
  const cheapestPrice = sorted.find((o) => o.in_stock)?.price ?? null;

  const handleAdd = () => {
    addToBasket({
      productId: group.product.id,
      label: group.product.name,
      quantity: 1,
    });
    setAdded(true);
    setTimeout(() => setAdded(false), 1500);
  };

  return (
    <article className="rounded-xl bg-white border border-gray-200 p-4 shadow-sm">
      <header className="flex items-start justify-between gap-3 mb-3">
        <div>
          <h2 className="font-semibold text-base leading-tight">{group.product.name}</h2>
          <p className="text-xs text-gray-500 mt-0.5">
            {group.product.category.replace("_", " ")}
            {group.product.subcategory ? ` · ${group.product.subcategory}` : ""}
            {group.product.is_loose ? " · loose" : ""}
          </p>
        </div>
        <button
          onClick={handleAdd}
          className="text-sm px-3 py-1.5 rounded-md border border-brand text-brand hover:bg-brand hover:text-white transition shrink-0"
        >
          {added ? "Added ✓" : "Add to basket"}
        </button>
      </header>

      <ul className="divide-y divide-gray-100 border-t border-gray-100">
        {sorted.map((o) => {
          const isCheapest = o.in_stock && o.price === cheapestPrice;
          return (
            <li key={o.store_product_id} className="flex items-center justify-between py-2 gap-3">
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <span className="font-medium text-sm">{o.store_display_name}</span>
                  {o.is_sponsored && (
                    <span className="text-[10px] uppercase tracking-wide bg-yellow-100 text-yellow-800 px-1.5 py-0.5 rounded">
                      sponsored
                    </span>
                  )}
                  <ConfidenceBadge confidence={o.match_confidence} method={o.match_method} />
                </div>
                <p className="text-xs text-gray-500 truncate">{o.name}</p>
              </div>
              <div className="flex items-center gap-3 shrink-0">
                <div className="text-right">
                  {!o.in_stock ? (
                    <span className="text-xs text-red-600">Out of stock</span>
                  ) : (
                    <span className={`text-base font-semibold ${isCheapest ? "text-brand" : ""}`}>
                      {fmt(o.price)}
                    </span>
                  )}
                  {o.original_price && o.original_price > o.price && (
                    <div className="text-xs text-gray-400 line-through">
                      {fmt(o.original_price)}
                    </div>
                  )}
                </div>
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
    </article>
  );
}
