"use client";

import type { AggregatedGroup, AggregatedOffering } from "@/types";
import { api } from "@/lib/api";
import { add as addToBasket } from "@/lib/basketStore";
import { productSlug } from "@/lib/slug";
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
    <article className="overflow-hidden rounded-card border border-line bg-card">
      <header className="flex items-center gap-3.5 border-b border-line px-4 py-3.5">
        {thumb && (
          <div className="hidden h-12 w-12 shrink-0 items-center justify-center overflow-hidden rounded-md border border-line bg-white p-1 sm:flex">
            {/* eslint-disable-next-line @next/next/no-img-element -- scraped store-CDN images span arbitrary domains */}
            <img
              src={thumb}
              alt=""
              width={48}
              height={48}
              loading="lazy"
              referrerPolicy="no-referrer"
              className="h-full w-full object-contain"
            />
          </div>
        )}
        <div className="min-w-0 flex-1">
          <h2 className="truncate text-[15px] font-semibold tracking-tight text-ink">
            {group.display_name}
          </h2>
          <p className="mt-0.5 text-xs text-faint">
            {group.offerings.length} offer{group.offerings.length === 1 ? "" : "s"} · {storeCount}{" "}
            store{storeCount === 1 ? "" : "s"}
          </p>
        </div>
        {group.cheapest_price != null && (
          <div className="shrink-0 text-right">
            <div className="text-[10px] uppercase tracking-wide text-faint">cheapest</div>
            <div className="tnum text-lg font-semibold leading-tight text-save">
              {taka(group.cheapest_price)}
            </div>
            {basis && (
              <div className="tnum text-[11px] text-muted">
                {unitPrice(group.cheapest_price, basis)}
              </div>
            )}
          </div>
        )}
      </header>

      {/* Mobile-first rows: no horizontal scroll, no fixed columns. Each row
          surfaces store · price · unit price · savings up front; brand,
          match confidence and actions wrap below on narrow screens. */}
      <ul className="divide-y divide-line/60">
        {rows.map((o) => {
          const isCheapest = o.in_stock && o.price === group.cheapest_price;
          return (
            <li
              key={o.store_product_id}
              className={`px-4 py-3 text-sm transition-colors ${
                isCheapest ? "bg-save-weak/60" : "hover:bg-line/40"
              } ${o.in_stock ? "" : "opacity-60"}`}
            >
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-1.5">
                    {isCheapest && (
                      <span className="shrink-0 rounded-full bg-save px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-white">
                        Cheapest
                      </span>
                    )}
                    <span className="truncate font-medium text-ink">{o.store_display_name}</span>
                    {o.is_sponsored && (
                      <span className="shrink-0 rounded bg-line/70 px-1 py-px text-[10px] text-muted">
                        ad
                      </span>
                    )}
                    <ConfidenceTag confidence={o.match_confidence} />
                  </div>
                  <div className="mt-0.5 flex min-w-0 flex-wrap items-center gap-x-1.5 text-xs text-muted">
                    {o.brand && <span className="shrink-0 capitalize text-ink/80">{o.brand}</span>}
                    {o.product_id != null ? (
                      <Link
                        href={`/product/${productSlug({ id: o.product_id, name: o.product_name })}`}
                        className="truncate underline-offset-2 hover:text-ink hover:underline"
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
                        className={`tnum text-[15px] font-semibold leading-tight ${
                          isCheapest ? "text-save" : "text-ink"
                        }`}
                      >
                        {taka(o.price)}
                      </div>
                      {o.original_price && o.original_price > o.price && (
                        <div className="tnum text-xs text-faint line-through">
                          {taka(o.original_price)}
                        </div>
                      )}
                      {basis && (
                        <div className="tnum text-[11px] text-muted">
                          {unitPrice(o.price, basis)}
                        </div>
                      )}
                    </>
                  ) : (
                    <span className="text-xs text-faint">Out of stock</span>
                  )}
                </div>
              </div>

              <div className="mt-2 flex items-center justify-end gap-2">
                {o.in_stock && (
                  <button
                    onClick={() => handleAdd(o)}
                    className="h-9 rounded-md border border-line px-3 text-xs font-medium text-ink transition-colors hover:border-line-strong hover:bg-line/50"
                  >
                    {addedKey === `${o.store_product_id}` ? "Added ✓" : "Add"}
                  </button>
                )}
                <a
                  href={api.clickUrl(o.store_product_id)}
                  target="_blank"
                  rel="noopener noreferrer sponsored"
                  className="inline-flex h-9 items-center px-2 text-xs font-medium text-muted underline-offset-2 hover:text-ink hover:underline"
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
