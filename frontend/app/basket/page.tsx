"use client";

import { api } from "@/lib/api";
import {
  load,
  remove,
  setQuantity,
  toApi,
  add as addToBasket,
  type BasketEntry,
} from "@/lib/basketStore";
import type { BasketOptimizeResponse, StorePlanOut } from "@/types";
import { StoreBadge } from "@/components/StoreBadge";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";

function fmt(n: number) {
  return "৳" + Math.round(n).toLocaleString("en-US");
}

const QUICK_ADDS = [
  { label: "5L Soybean Oil", q: "5L soybean oil" },
  { label: "Miniket Rice 5kg", q: "miniket rice 5kg" },
  { label: "Sugar 1kg", q: "sugar 1kg" },
  { label: "12 Eggs", q: "12 eggs" },
  { label: "Masoor Dal 1kg", q: "masoor dal 1kg" },
];

function QtyInput({ value, onCommit }: { value: number; onCommit: (n: number) => void }) {
  const [text, setText] = useState(String(value));
  useEffect(() => {
    setText(String(value));
  }, [value]);
  const commit = () => {
    const n = Math.max(1, Math.min(1000, Math.floor(Number(text) || 1)));
    setText(String(n));
    onCommit(n);
  };
  return (
    <div className="flex items-center rounded-full border border-white/20 bg-white/10 p-1 backdrop-blur-md">
      <button
        type="button"
        onClick={() => {
          const n = Math.max(1, value - 1);
          setText(String(n));
          onCommit(n);
        }}
        className="flex h-7 w-7 items-center justify-center rounded-full text-xs font-black text-white hover:bg-white/20 active:scale-90"
      >
        −
      </button>
      <input
        type="number"
        min={1}
        max={1000}
        value={text}
        onChange={(ev) => setText(ev.target.value)}
        onBlur={commit}
        onKeyDown={(ev) => {
          if (ev.key === "Enter") ev.currentTarget.blur();
        }}
        aria-label="Quantity"
        className="tnum w-10 bg-transparent text-center text-xs font-extrabold text-white focus:outline-none"
      />
      <button
        type="button"
        onClick={() => {
          const n = Math.min(1000, value + 1);
          setText(String(n));
          onCommit(n);
        }}
        className="flex h-7 w-7 items-center justify-center rounded-full text-xs font-black text-white hover:bg-white/20 active:scale-90"
      >
        +
      </button>
    </div>
  );
}

function PlanCard({ plan, best }: { plan: StorePlanOut; best?: boolean }) {
  return (
    <div
      className={`rounded-3xl border bg-gradient-to-b from-white/10 to-white/5 p-6 backdrop-blur-2xl shadow-xl transition-all ${
        best ? "border-save/60 ring-2 ring-save/20" : "border-white/10"
      }`}
    >
      <header className="mb-4 flex items-start justify-between gap-3 border-b border-white/10 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <StoreBadge storeName={plan.store} displayName={plan.store_display_name} size="md" />
            {best && (
              <span className="rounded-full bg-save px-2.5 py-0.5 text-[10px] font-black uppercase tracking-wider text-white shadow-xs">
                Cheapest Single Store
              </span>
            )}
          </div>
        </div>
        <div className="text-right">
          <div className="text-[10px] font-bold uppercase tracking-wider text-white/40">
            Total Cost
          </div>
          <div className="tnum text-2xl font-black text-white leading-tight">{fmt(plan.total)}</div>
        </div>
      </header>

      <ul className="divide-y divide-white/10 text-sm">
        {plan.items.map((it) => (
          <li key={it.item_key} className="flex justify-between gap-3 py-2.5">
            <span className="truncate text-white/80">
              {it.label} <span className="text-xs font-bold text-white/40">× {it.quantity}</span>
            </span>
            <span className="tnum shrink-0 font-bold text-white">{fmt(it.line_total)}</span>
          </li>
        ))}
      </ul>

      <div className="mt-4 flex justify-between rounded-2xl bg-black/30 p-2.5 text-xs font-semibold text-white/70">
        <span className="tnum">Items: {fmt(plan.items_subtotal)}</span>
        <span className="tnum">
          Delivery: {plan.delivery_fee === 0 ? "FREE" : fmt(plan.delivery_fee)}
        </span>
      </div>

      {plan.missing_items.length > 0 && (
        <p className="mt-3 text-xs font-semibold text-amber-300">
          ⚠️ {plan.missing_items.length} {plan.missing_items.length === 1 ? "item" : "items"} not
          available at this store
        </p>
      )}
    </div>
  );
}

export default function BasketPage() {
  const [entries, setEntries] = useState<BasketEntry[]>([]);
  const [result, setResult] = useState<BasketOptimizeResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setEntries(load());
  }, []);

  const optimizeSeq = useRef(0);

  const refreshOptimize = async (next: BasketEntry[]) => {
    if (next.length === 0) {
      setResult(null);
      return;
    }
    const seq = ++optimizeSeq.current;
    setLoading(true);
    setError(null);
    try {
      const res = await api.optimize(toApi(next));
      if (seq === optimizeSeq.current) setResult(res);
    } catch (e) {
      if (seq === optimizeSeq.current) setError(String(e));
    } finally {
      if (seq === optimizeSeq.current) setLoading(false);
    }
  };

  useEffect(() => {
    void refreshOptimize(entries);
  }, [entries]);

  if (entries.length === 0) {
    return (
      <div className="mx-auto max-w-lg py-16 text-center">
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-3xl bg-white/10 text-orange-400">
          <svg
            className="h-8 w-8"
            fill="none"
            viewBox="0 0 24 24"
            strokeWidth={2}
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M15.75 10.5V6a3.75 3.75 0 10-7.5 0v4.5m11.356-1.993l1.263 12c.07.665-.45 1.243-1.119 1.243H4.25a1.125 1.125 0 01-1.12-1.243l1.264-12A1.125 1.125 0 015.513 7.5h12.974c.576 0 1.059.435 1.119 1.007zM8.625 10.5a.375.375 0 11-.75 0 .375.375 0 01.75 0zm7.5 0a.375.375 0 11-.75 0 .375.375 0 01.75 0z"
            />
          </svg>
        </div>
        <h1 className="mt-5 font-display text-3xl font-black tracking-tight text-white">
          Your basket is empty
        </h1>
        <p className="mt-2 text-sm leading-relaxed text-white/60">
          Add items to your basket as you explore. Daam Kemon calculates whether ordering from a
          single supermarket or splitting across two stores saves you more money after delivery
          fees.
        </p>

        <div className="mt-8 flex flex-wrap justify-center gap-2">
          {QUICK_ADDS.map((s) => (
            <button
              key={s.q}
              onClick={() => {
                const updated = addToBasket({
                  query: s.q,
                  label: s.label,
                  quantity: 1,
                });
                setEntries(updated);
              }}
              className="rounded-full border border-white/15 bg-white/5 px-4 py-1.5 text-xs font-bold text-white transition-all hover:bg-white/15"
            >
              + {s.label}
            </button>
          ))}
        </div>

        <div className="mt-8">
          <Link
            href="/"
            className="inline-flex items-center gap-2 rounded-full bg-white px-8 py-3.5 text-xs font-black text-black shadow-xl hover:bg-orange-100"
          >
            <span>Explore Today&apos;s Deals</span>
            <span>›</span>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-10">
      <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
        <div>
          <h1 className="font-display text-3xl font-black tracking-tight text-white sm:text-4xl">
            Basket Optimizer
          </h1>
          <p className="mt-1 text-xs text-white/60 sm:text-sm">
            {entries.length} {entries.length === 1 ? "item" : "items"} in your shopping list. We
            compute the cheapest single store and optimal split.
          </p>
        </div>
        <button
          onClick={() => {
            if (confirm("Clear all items from your basket?")) {
              for (const e of entries) remove(e.id);
              setEntries([]);
            }
          }}
          className="text-xs font-bold text-error hover:underline self-start sm:self-auto"
        >
          Clear entire basket
        </button>
      </div>

      {/* Item list */}
      <div className="overflow-hidden rounded-3xl border border-white/10 bg-gradient-to-b from-white/10 to-white/5 backdrop-blur-2xl shadow-xl">
        <div className="border-b border-white/10 bg-black/40 px-6 py-3 text-xs font-black uppercase tracking-wider text-white/50">
          Items in Comparison
        </div>
        <ul className="divide-y divide-white/10">
          {entries.map((e) => (
            <li key={e.id} className="flex items-center justify-between gap-4 p-4 sm:px-6">
              <div className="min-w-0 flex-1">
                <p className="truncate font-display text-base font-bold text-white">{e.label}</p>
                {e.query && <p className="text-xs text-white/40">Matched to: {e.query}</p>}
              </div>
              <div className="flex shrink-0 items-center gap-3">
                <QtyInput value={e.quantity} onCommit={(n) => setEntries(setQuantity(e.id, n))} />
                <button
                  onClick={() => setEntries(remove(e.id))}
                  className="rounded-full p-2 text-xs font-medium text-white/50 hover:bg-error/20 hover:text-error"
                  aria-label="Remove item"
                >
                  <svg
                    className="h-4 w-4"
                    fill="none"
                    viewBox="0 0 24 24"
                    strokeWidth={2}
                    stroke="currentColor"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </li>
          ))}
        </ul>
      </div>

      {loading && (
        <div className="flex items-center gap-2 rounded-2xl border border-white/10 bg-white/5 p-4 text-xs font-bold text-white/70">
          <span className="h-2 w-2 rounded-full bg-save animate-ping" />
          <span>Calculating optimal store combination across Bangladesh…</span>
        </div>
      )}

      {error && (
        <div className="rounded-2xl border border-error/40 bg-black/40 p-4 text-xs text-error">
          ⚠️ Couldn&apos;t optimize the basket right now. Please retry in a few moments.
        </div>
      )}

      {result?.unresolved_items && result.unresolved_items.length > 0 && (
        <div className="rounded-2xl border border-white/10 bg-black/30 p-4 text-xs text-white/60">
          Could not find equivalent listings for:{" "}
          <strong className="text-white">{result.unresolved_items.join(", ")}</strong>
        </div>
      )}

      {/* OPTIMAL SPLIT (DOPAMINE BANNER) */}
      {result && result.split.length > 0 && (
        <section className="space-y-4">
          <div className="rounded-3xl border border-save/50 bg-gradient-to-r from-save/20 via-save/10 to-transparent p-6 shadow-xl backdrop-blur-2xl">
            <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
              <div>
                <span className="inline-flex items-center gap-1.5 rounded-full bg-save px-3 py-1 text-xs font-black text-white shadow-sm">
                  ⚡ Smart Split Recommendation
                </span>
                <h2 className="mt-3 font-display text-2xl font-black tracking-tight text-white sm:text-3xl">
                  Save <span className="text-save-bright">{fmt(result.split_savings)}</span> by
                  splitting between {result.split.length} stores!
                </h2>
                <p className="mt-1 text-xs text-white/60">
                  Even after paying multiple delivery fees, this split order is cheaper than any
                  single supermarket.
                </p>
              </div>
            </div>
          </div>

          <div className="grid gap-5 sm:grid-cols-2">
            {result.split.map((p) => (
              <PlanCard key={p.store} plan={p} />
            ))}
          </div>
        </section>
      )}

      {/* CHEAPEST SINGLE STORE */}
      {result?.single_store && (
        <section className="space-y-4">
          <h2 className="text-xs font-black uppercase tracking-wider text-white/40">
            Single Store Option (One Delivery)
          </h2>
          <PlanCard plan={result.single_store} best={result.split.length === 0} />
        </section>
      )}

      {/* ALL STORES COMPARISON */}
      {result && result.all_single_store.length > 0 && (
        <section className="space-y-4">
          <h2 className="text-xs font-black uppercase tracking-wider text-white/40">
            All Supermarkets Ranked (Single Store)
          </h2>
          <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {result.all_single_store.map((p) => (
              <PlanCard key={p.store} plan={p} />
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
