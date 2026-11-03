"use client";

import type { AggregatedGroup, AggregatedOffering } from "@/types";
import { api } from "@/lib/api";
import { add as addToBasket } from "@/lib/basketStore";
import { productSlug } from "@/lib/slug";
import { StoreBadge } from "@/components/StoreBadge";
import Link from "next/link";
import { useMemo, useState } from "react";

function taka(n: number | null | undefined): string {
  if (n === null || n === undefined) return "—";
  return "৳" + Math.round(n).toLocaleString("en-US");
}

// Unit-price basis for the whole group (size is shared across its offerings):
// price ÷ this divisor gives ৳/L, ৳/kg or ৳/pc. Frontend-computed, no API field.
function unitBasis(group: AggregatedGroup): { divisor: number; label: string } | null {
  const v = group.size_value;
  if (!v || v <= 0 || !group.size_unit) return null;
  const u = group.size_unit.toUpperCase();
  if (u === "L") return { divisor: v, label: "/L" };
  if (u === "ML") return { divisor: v / 1000, label: "/L" };
  if (u === "KG") return { divisor: v, label: "/kg" };
  if (u === "G") return { divisor: v / 1000, label: "/kg" };
  if (u === "PCS") return { divisor: v, label: group.category === "eggs" ? "/egg" : "/pc" };
  return null;
}

function unitPrice(price: number, basis: { divisor: number; label: string }): string {
  const val = price / basis.divisor;
  const rounded = val >= 100 ? Math.round(val) : Math.round(val * 10) / 10;
  return "৳" + rounded.toLocaleString("en-US") + basis.label;
}

function ConfidenceTag({ confidence }: { confidence: number | null }) {
  if (confidence == null || confidence >= 0.99) return null;
  const label = confidence >= 0.85 ? "brand match" : confidence >= 0.7 ? "category" : "approx";
  return (
    <span
      className="rounded bg-line/70 px-1 py-px text-[10px] font-medium text-muted"
      title="Match confidence"
    >
      {label}
    </span>
  );
}

export function AggregatedGroupCard({ group }: { group: AggregatedGroup }) {
  const [addedKey, setAddedKey] = useState<string | null>(null);
  const basis = useMemo(() => unitBasis(group), [group]);

  // Flat, cheapest-first: in-stock by price, then out-of-stock by price.
  const rows = useMemo(() => {
    return [...group.offerings].sort(
      (a, b) => Number(!a.in_stock) - Number(!b.in_stock) || a.price - b.price
    );
  }, [group.offerings]);

  const storeCount = useMemo(
    () => new Set(group.offerings.map((o) => o.store_name)).size,
    [group.offerings]
  );

  const inStockOfferings = useMemo(() => rows.filter((r) => r.in_stock), [rows]);
  const highestPrice = useMemo(
    () => (inStockOfferings.length > 0 ? Math.max(...inStockOfferings.map((r) => r.price)) : 0),
    [inStockOfferings]
  );

  const maxSavings = useMemo(() => {
    if (!group.cheapest_price || highestPrice <= group.cheapest_price) return 0;
    return highestPrice - group.cheapest_price;
  }, [group.cheapest_price, highestPrice]);

  // Card thumbnail: first offering (cheapest-first) that has a scraped image.
  const thumb = useMemo(() => rows.find((o) => o.image_url)?.image_url ?? null, [rows]);

  const handleAdd = (off: AggregatedOffering) => {
    addToBasket({
      query: group.display_name,
      label: `${off.brand ? off.brand + " · " : ""}${group.display_name}`,
      quantity: 1,
    });
    setAddedKey(`${off.store_product_id}`);
    setTimeout(() => setAddedKey(null), 1400);
  };

  return (
    <article className="overflow-hidden rounded-2xl border border-line bg-card shadow-sm transition-shadow hover:shadow-md">
      <header className="flex items-center gap-3.5 border-b border-line/80 bg-paper/30 px-4 py-3.5">
        {thumb && (
          <div className="flex h-14 w-14 shrink-0 items-center justify-center overflow-hidden rounded-xl border border-line bg-white p-1 shadow-xs">
            {/* eslint-disable-next-line @next/next/no-img-element -- scraped store-CDN images span arbitrary domains */}
            <img
              src={thumb}
              alt=""
              width={56}
              height={56}
              loading="lazy"
              referrerPolicy="no-referrer"
              className="h-full w-full object-contain"
            />
          </div>
        )}
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <h2 className="truncate text-base font-bold tracking-tight text-ink">
              {group.display_name}
            </h2>
            {maxSavings >= 10 && (
              <span className="inline-flex items-center rounded-full bg-save-weak px-2 py-0.5 text-[11px] font-bold text-save-dark ring-1 ring-save/20">
                ৳{Math.round(maxSavings)} পর্যন্ত সাশ্রয়
              </span>
            )}
          </div>
          <p className="mt-0.5 text-xs text-muted">
            {group.offerings.length} {group.offerings.length === 1 ? "offer" : "offers"} across{" "}
            {storeCount} {storeCount === 1 ? "store" : "stores"}
          </p>
        </div>
        {group.cheapest_price != null && (
          <div className="shrink-0 text-right">
            <div className="text-[10px] font-semibold uppercase tracking-wider text-save">
              Cheapest
            </div>
            <div className="tnum text-xl font-extrabold leading-tight text-save">
              {taka(group.cheapest_price)}
            </div>
            {basis && (
              <div className="tnum text-[11px] font-medium text-muted">
                {unitPrice(group.cheapest_price, basis)}
              </div>
            )}
          </div>
        )}
      </header>

      {/* Mobile-first offerings list */}
      <ul className="divide-y divide-line/60">
        {rows.map((o) => {
          const isCheapest = o.in_stock && o.price === group.cheapest_price;
          const savingsVsHighest =
            highestPrice > o.price && isCheapest ? highestPrice - o.price : 0;

          return (
            <li
              key={o.store_product_id}
              className={`px-4 py-3 text-sm transition-colors ${
                isCheapest ? "bg-save-weak/40" : "hover:bg-line/30"
              } ${o.in_stock ? "" : "opacity-60"}`}
            >
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-1.5">
                    <StoreBadge
                      storeName={o.store_name}
                      displayName={o.store_display_name}
                      size="sm"
                    />
                    {isCheapest && (
                      <span className="shrink-0 rounded-full bg-save px-1.5 py-0.5 text-[10px] font-bold text-white shadow-xs">
                        Lowest Price
                      </span>
                    )}
                    {savingsVsHighest >= 10 && (
                      <span className="hidden shrink-0 text-[11px] font-medium text-save-dark sm:inline-block">
                        (৳{Math.round(savingsVsHighest)} সাশ্রয়)
                      </span>
                    )}
                    {o.is_sponsored && (
                      <span className="shrink-0 rounded bg-line/70 px-1 py-px text-[10px] text-muted">
                        ad
                      </span>
                    )}
                    <ConfidenceTag confidence={o.match_confidence} />
                  </div>
                  <div className="mt-1 flex min-w-0 flex-wrap items-center gap-x-1.5 text-xs text-muted">
                    {o.brand && (
                      <span className="shrink-0 font-medium capitalize text-ink/80">{o.brand}</span>
                    )}
                    {o.product_id != null ? (
                      <Link
                        href={`/product/${productSlug({ id: o.product_id, name: o.product_name })}`}
                        className="truncate underline-offset-2 hover:text-brand hover:underline"
                        title={`See all prices for ${o.product_name}`}
                      >
                        {o.store_product_name}
                      </Link>
                    ) : (
                      <span className="truncate">{o.store_product_name}</span>
                    )}
                  </div>
                </div>

                <div className="shrink-0 text-right">
                  {o.in_stock ? (
                    <>
                      <div
                        className={`tnum text-[15px] font-bold leading-tight ${
                          isCheapest ? "text-save" : "text-ink"
                        }`}
                      >
                        {taka(o.price)}
                      </div>
                      {o.original_price && o.original_price > o.price ? (
                        <div className="tnum text-xs text-faint line-through">
                          {taka(o.original_price)}
                        </div>
                      ) : null}
                      {basis && (
                        <div className="tnum text-[11px] text-muted">
                          {unitPrice(o.price, basis)}
                        </div>
                      )}
                    </>
                  ) : (
                    <span className="text-xs font-medium text-faint">Out of stock</span>
                  )}
                </div>
              </div>

              <div className="mt-2.5 flex items-center justify-end gap-2">
                {o.in_stock && (
                  <button
                    onClick={() => handleAdd(o)}
                    className={`h-8 rounded-lg px-3 text-xs font-semibold transition-all active:scale-95 ${
                      addedKey === `${o.store_product_id}`
                        ? "bg-save text-white shadow-xs"
                        : "border border-line bg-card text-ink hover:border-brand hover:bg-brand/5 hover:text-brand"
                    }`}
                  >
                    {addedKey === `${o.store_product_id}` ? "Added ✓" : "+ Add to Basket"}
                  </button>
                )}
                <a
                  href={api.clickUrl(o.store_product_id)}
                  target="_blank"
                  rel="noopener noreferrer sponsored"
                  className="inline-flex h-8 items-center gap-1 rounded-lg border border-line bg-card px-2.5 text-xs font-medium text-muted transition-colors hover:border-line-strong hover:text-ink"
                >
                  <span>Visit</span>
                  <svg
                    className="h-3 w-3"
                    fill="none"
                    viewBox="0 0 24 24"
                    strokeWidth={2}
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M13.5 6H5.25A2.25 2.25 0 003 8.25v10.5A2.25 2.25 0 005.25 21h10.5A2.25 2.25 0 0018 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25"
                    />
                  </svg>
                </a>
              </div>
            </li>
          );
        })}
      </ul>
    </article>
  );
}
