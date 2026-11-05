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
      className="rounded bg-white/10 px-1.5 py-0.5 text-[10px] font-semibold text-white/60"
      title="Match confidence"
    >
      {label}
    </span>
  );
}

export function AggregatedGroupCard({ group }: { group: AggregatedGroup }) {
  const [addedKey, setAddedKey] = useState<string | null>(null);
  const basis = useMemo(() => unitBasis(group), [group]);

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
    <article className="overflow-hidden rounded-3xl border border-white/15 bg-gradient-to-b from-[#1C120C]/90 via-[#140C08]/95 to-[#0D0704] text-white shadow-xl backdrop-blur-2xl transition-all hover:border-white/25 hover:shadow-2xl">
      <header className="flex items-center gap-4 border-b border-white/10 bg-black/40 px-5 py-4">
        {thumb && (
          <div className="flex h-14 w-14 shrink-0 items-center justify-center overflow-hidden rounded-2xl border border-white/15 bg-white/5 p-1 backdrop-blur-md">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={thumb}
              alt=""
              width={56}
              height={56}
              loading="lazy"
              referrerPolicy="no-referrer"
              className="h-full w-full object-contain filter drop-shadow-md"
            />
          </div>
        )}
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <h2 className="truncate font-display text-lg font-bold tracking-tight text-white">
              {group.display_name}
            </h2>
            {maxSavings >= 10 && (
              <span className="inline-flex items-center rounded-full bg-save px-2.5 py-0.5 text-xs font-black text-white shadow-xs">
                ৳{Math.round(maxSavings)} পর্যন্ত সাশ্রয়
              </span>
            )}
          </div>
          <p className="mt-0.5 text-xs text-white/50">
            {group.offerings.length} {group.offerings.length === 1 ? "offer" : "offers"} across{" "}
            {storeCount} {storeCount === 1 ? "store" : "stores"}
          </p>
        </div>
        {group.cheapest_price != null && (
          <div className="shrink-0 text-right">
            <div className="text-[10px] font-bold uppercase tracking-wider text-save-bright">
              Cheapest
            </div>
            <div className="tnum text-2xl font-black leading-tight text-white">
              {taka(group.cheapest_price)}
            </div>
            {basis && (
              <div className="tnum text-[11px] font-medium text-white/50">
                {unitPrice(group.cheapest_price, basis)}
              </div>
            )}
          </div>
        )}
      </header>

      <ul className="divide-y divide-white/10">
        {rows.map((o) => {
          const isCheapest = o.in_stock && o.price === group.cheapest_price;
          const savingsVsHighest =
            highestPrice > o.price && isCheapest ? highestPrice - o.price : 0;

          return (
            <li
              key={o.store_product_id}
              className={`px-5 py-3.5 text-sm transition-colors ${
                isCheapest ? "bg-save-weak/5 border-l-2 border-save" : "hover:bg-white/5"
              } ${o.in_stock ? "" : "opacity-50"}`}
            >
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <StoreBadge
                      storeName={o.store_name}
                      displayName={o.store_display_name}
                      size="sm"
                    />
                    {isCheapest && (
                      <span className="shrink-0 rounded-full bg-save px-2 py-0.5 text-[10px] font-black text-white shadow-xs">
                        Lowest Price
                      </span>
                    )}
                    {savingsVsHighest >= 10 && (
                      <span className="hidden shrink-0 text-xs font-bold text-save-bright sm:inline-block">
                        (৳{Math.round(savingsVsHighest)} সাশ্রয়)
                      </span>
                    )}
                    {o.is_sponsored && (
                      <span className="shrink-0 rounded bg-white/10 px-1.5 py-px text-[10px] text-white/50">
                        ad
                      </span>
                    )}
                    <ConfidenceTag confidence={o.match_confidence} />
                  </div>
                  <div className="mt-1 flex min-w-0 flex-wrap items-center gap-x-2 text-xs text-white/60">
                    {o.brand && (
                      <span className="shrink-0 font-bold capitalize text-white/90">{o.brand}</span>
                    )}
                    {o.product_id != null ? (
                      <Link
                        href={`/product/${productSlug({ id: o.product_id, name: o.product_name })}`}
                        className="truncate underline-offset-2 hover:text-orange-300 hover:underline"
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
                        className={`tnum text-base font-black leading-tight ${
                          isCheapest ? "text-save-bright" : "text-white"
                        }`}
                      >
                        {taka(o.price)}
                      </div>
                      {o.original_price && o.original_price > o.price ? (
                        <div className="tnum text-xs text-white/40 line-through">
                          {taka(o.original_price)}
                        </div>
                      ) : null}
                      {basis && (
                        <div className="tnum text-[11px] text-white/50">
                          {unitPrice(o.price, basis)}
                        </div>
                      )}
                    </>
                  ) : (
                    <span className="text-xs font-medium text-white/40">Out of stock</span>
                  )}
                </div>
              </div>

              <div className="mt-3 flex items-center justify-end gap-2">
                {o.in_stock && (
                  <button
                    onClick={() => handleAdd(o)}
                    className={`h-8 rounded-full px-4 text-xs font-black transition-all active:scale-95 ${
                      addedKey === `${o.store_product_id}`
                        ? "bg-save text-white shadow-md"
                        : "border border-white/20 bg-white/10 text-white hover:bg-white hover:text-black shadow-sm"
                    }`}
                  >
                    {addedKey === `${o.store_product_id}` ? "Added ✓" : "+ Add to Basket"}
                  </button>
                )}
                <a
                  href={api.clickUrl(o.store_product_id)}
                  target="_blank"
                  rel="noopener noreferrer sponsored"
                  className="inline-flex h-8 items-center gap-1.5 rounded-full border border-white/15 bg-white/5 px-3 text-xs font-semibold text-white/70 transition-colors hover:border-white/30 hover:bg-white/10 hover:text-white"
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
