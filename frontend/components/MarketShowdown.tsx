"use client";

import Link from "next/link";
import { useState } from "react";
import { StoreBadge } from "@/components/StoreBadge";
import { add as addToBasket } from "@/lib/basketStore";

const SHOWDOWN_ITEMS = [
  {
    id: "oil-fresh",
    name: "5L Soybean Oil",
    bnSubtitle: "ফ্রেশ / তীর বোতল",
    query: "5L soybean oil",
    lowestPrice: 890,
    lowestStore: "shwapno",
    highestPrice: 960,
    highestStore: "chaldal",
    savings: 70,
  },
  {
    id: "rice-miniket",
    name: "Miniket Rice 5kg",
    bnSubtitle: "প্রিমিয়াম মিনিকেট চাল",
    query: "miniket rice 5kg",
    lowestPrice: 365,
    lowestStore: "chaldal",
    highestPrice: 415,
    highestStore: "unimart",
    savings: 50,
  },
  {
    id: "milk-dano",
    name: "Dano Milk Powder 1kg",
    bnSubtitle: "ফুল ক্রিম মিল্ক পাউডার",
    query: "dano milk powder 1kg",
    lowestPrice: 885,
    lowestStore: "unimart",
    highestPrice: 960,
    highestStore: "shwapno",
    savings: 75,
  },
  {
    id: "eggs-farm",
    name: "12 Brown Eggs",
    bnSubtitle: "১২টি ফার্ম ফ্রেশ ডিম",
    query: "12 eggs",
    lowestPrice: 148,
    lowestStore: "shwapno",
    highestPrice: 165,
    highestStore: "agora",
    savings: 17,
  },
  {
    id: "dal-masoor",
    name: "Deshi Masoor Dal 1kg",
    bnSubtitle: "চিকন দেশি মসুর ডাল",
    query: "masoor dal 1kg",
    lowestPrice: 138,
    lowestStore: "agora",
    highestPrice: 155,
    highestStore: "chaldal",
    savings: 17,
  },
  {
    id: "sugar-white",
    name: "Refined White Sugar 1kg",
    bnSubtitle: "পরিশোধিত সাদা চিনি",
    query: "sugar 1kg",
    lowestPrice: 134,
    lowestStore: "chaldal",
    highestPrice: 148,
    highestStore: "daraz",
    savings: 14,
  },
];

export function MarketShowdown() {
  const [addedId, setAddedId] = useState<string | null>(null);

  const handleAdd = (item: (typeof SHOWDOWN_ITEMS)[number]) => {
    addToBasket({
      query: item.query,
      label: item.name,
      quantity: 1,
    });
    setAddedId(item.id);
    setTimeout(() => setAddedId(null), 1500);
  };

  return (
    <section className="space-y-5">
      <div className="flex flex-col justify-between gap-2 sm:flex-row sm:items-end">
        <div>
          <div className="flex items-center gap-2">
            <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-orange-500/20 text-orange-400">
              <svg
                className="h-4 w-4"
                fill="none"
                viewBox="0 0 24 24"
                strokeWidth={2.5}
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M15.362 5.214A8.252 8.252 0 0112 21 8.25 8.25 0 016.038 7.048 8.287 8.287 0 009 9.6a8.983 8.983 0 013.361-6.867 8.21 8.21 0 003 2.48z"
                />
              </svg>
            </span>
            <h2 className="text-xl font-extrabold tracking-tight text-white sm:text-2xl">
              Today&apos;s Biggest Price Discrepancies
            </h2>
            <span className="rounded-full bg-save px-2.5 py-0.5 text-xs font-black text-white shadow-xs">
              আজকের সেরা সাশ্রয়
            </span>
          </div>
          <p className="mt-1 text-xs text-white/60 sm:text-sm">
            Equivalent brands and sizes, side by side. Same quality, pocket the difference.
          </p>
        </div>

        <Link
          href="/search?q=oil"
          className="text-xs font-bold text-orange-400 hover:text-orange-300"
        >
          View All Comparisons →
        </Link>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {SHOWDOWN_ITEMS.map((item) => (
          <div
            key={item.id}
            className="flex flex-col justify-between rounded-3xl border border-white/10 bg-gradient-to-b from-white/10 to-white/5 p-5 backdrop-blur-xl shadow-lg transition-all hover:border-white/20 hover:scale-[1.01]"
          >
            <div>
              <div className="flex items-start justify-between gap-2">
                <div>
                  <h3 className="font-bold text-white text-base leading-snug">{item.name}</h3>
                  <p className="text-xs text-white/50">{item.bnSubtitle}</p>
                </div>
                <span className="shrink-0 rounded-full bg-save/90 px-2.5 py-0.5 text-xs font-black text-white shadow-xs">
                  ৳{item.savings} সাশ্রয়
                </span>
              </div>

              {/* Price comparison row */}
              <div className="mt-4 flex items-center justify-between rounded-2xl border border-white/10 bg-black/30 p-3">
                <div>
                  <span className="text-[10px] font-bold uppercase tracking-wider text-save-bright">
                    Cheapest at
                  </span>
                  <div className="mt-1">
                    <StoreBadge storeName={item.lowestStore} size="sm" />
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-xl font-black text-white">৳{item.lowestPrice}</div>
                  <div className="text-[11px] text-white/40 line-through">
                    ৳{item.highestPrice} at {item.highestStore}
                  </div>
                </div>
              </div>
            </div>

            <div className="mt-4 flex items-center justify-between border-t border-white/10 pt-3">
              <Link
                href={`/search?q=${encodeURIComponent(item.query)}`}
                className="text-xs font-semibold text-white/60 hover:text-white"
              >
                Compare stores →
              </Link>
              <button
                onClick={() => handleAdd(item)}
                className={`h-8 rounded-full px-3.5 text-xs font-bold transition-all active:scale-95 ${
                  addedId === item.id
                    ? "bg-save text-white shadow-md"
                    : "border border-white/20 bg-white/10 text-white hover:bg-white hover:text-black"
                }`}
              >
                {addedId === item.id ? "Added ✓" : "+ Add"}
              </button>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
