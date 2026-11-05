"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { addMultiple as addMultipleToBasket } from "@/lib/basketStore";

const BUNDLES = [
  {
    id: "weekly",
    badge: "Most Popular",
    title: "সাপ্তাহিক নিত্যবাজার",
    subtitle: "Weekly Family Essentials Pack",
    estTotal: 1675,
    estSavings: 145,
    items: [
      { label: "5L Soybean Oil", query: "5L soybean oil", quantity: 1 },
      { label: "Miniket Rice 5kg", query: "miniket rice 5kg", quantity: 1 },
      { label: "Masoor Dal 1kg", query: "masoor dal 1kg", quantity: 1 },
      { label: "12 Eggs", query: "12 eggs", quantity: 1 },
      { label: "Sugar 1kg", query: "sugar 1kg", quantity: 1 },
    ],
  },
  {
    id: "breakfast",
    badge: "Morning Combo",
    title: "সকালের নাস্তা প্যাক",
    subtitle: "Breakfast & Morning Chai",
    estTotal: 460,
    estSavings: 45,
    items: [
      { label: "12 Eggs", query: "12 eggs", quantity: 1 },
      { label: "Milk Powder 500g", query: "dano milk 500g", quantity: 1 },
      { label: "Sugar 1kg", query: "sugar 1kg", quantity: 1 },
    ],
  },
  {
    id: "bachelor",
    badge: "Quick Student Cart",
    title: "ব্যাচেলর স্পেশাল",
    subtitle: "Quick Monthly Staples",
    estTotal: 620,
    estSavings: 60,
    items: [
      { label: "Soybean Oil 1L", query: "soybean oil 1L", quantity: 1 },
      { label: "12 Eggs", query: "12 eggs", quantity: 1 },
      { label: "Masoor Dal 1kg", query: "masoor dal 1kg", quantity: 1 },
      { label: "Instant Noodles", query: "maggi noodles", quantity: 1 },
    ],
  },
];

export function BazaarBundles() {
  const router = useRouter();
  const [addingId, setAddingId] = useState<string | null>(null);

  const handleAdd = (bundle: (typeof BUNDLES)[number]) => {
    setAddingId(bundle.id);
    addMultipleToBasket(
      bundle.items.map((it) => ({
        query: it.query,
        label: it.label,
        quantity: it.quantity,
      }))
    );
    setTimeout(() => {
      setAddingId(null);
      router.push("/basket");
    }, 400);
  };

  return (
    <section className="space-y-5">
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
                d="M15.75 10.5V6a3.75 3.75 0 10-7.5 0v4.5m11.356-1.993l1.263 12c.07.665-.45 1.243-1.119 1.243H4.25a1.125 1.125 0 01-1.12-1.243l1.264-12A1.125 1.125 0 015.513 7.5h12.974c.576 0 1.059.435 1.119 1.007zM8.625 10.5a.375.375 0 11-.75 0 .375.375 0 01.75 0zm7.5 0a.375.375 0 11-.75 0 .375.375 0 01.75 0z"
              />
            </svg>
          </span>
          <h2 className="text-xl font-extrabold tracking-tight text-white sm:text-2xl">
            1-Click Bazaar Bundles
          </h2>
          <span className="rounded-full bg-white/10 px-2.5 py-0.5 text-xs font-bold text-orange-300">
            রেডি বাজার প্যাক
          </span>
        </div>
        <p className="mt-1 text-xs text-white/60 sm:text-sm">
          Load an entire grocery list with 1 tap. Our Basket Optimizer computes the cheapest
          multi-store split with delivery fees.
        </p>
      </div>

      <div className="grid gap-5 sm:grid-cols-3">
        {BUNDLES.map((b) => (
          <div
            key={b.id}
            className="flex flex-col justify-between rounded-3xl border border-white/10 bg-gradient-to-b from-[#241712] via-[#1A100C] to-[#120B08] p-6 shadow-xl backdrop-blur-2xl transition-all hover:border-white/25 hover:scale-[1.01]"
          >
            <div>
              <div className="flex items-center justify-between">
                <span className="rounded-full bg-white/10 px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wider text-white/70">
                  {b.badge}
                </span>
                <span className="rounded-full bg-save px-2.5 py-0.5 text-[11px] font-black text-white shadow-xs">
                  বাঁচবে ৳{b.estSavings}+
                </span>
              </div>

              <h3 className="mt-4 font-display text-xl font-black text-white">{b.title}</h3>
              <p className="text-xs text-white/50">{b.subtitle}</p>

              <ul className="mt-4 space-y-2 border-t border-white/10 pt-4 text-xs text-white/80">
                {b.items.map((it) => (
                  <li key={it.query} className="flex items-center gap-2">
                    <span className="text-emerald-400 font-bold">✓</span>
                    <span>{it.label}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="mt-6 border-t border-white/10 pt-4">
              <div className="mb-3 flex items-baseline justify-between text-xs">
                <span className="text-white/50">Estimated Total:</span>
                <span className="tnum text-lg font-black text-white">৳{b.estTotal}</span>
              </div>

              <button
                onClick={() => handleAdd(b)}
                disabled={addingId === b.id}
                className="flex w-full items-center justify-center gap-2 rounded-full bg-white py-3 text-xs font-black text-black shadow-lg transition-all hover:bg-orange-100 active:scale-95 disabled:opacity-50"
              >
                <span>{addingId === b.id ? "Optimizing…" : "Add Bundle & Optimize"}</span>
                <span>›</span>
              </button>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
