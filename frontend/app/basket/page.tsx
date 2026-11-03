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
    <div className="flex items-center rounded-lg border border-line bg-card p-0.5">
      <button
        type="button"
        onClick={() => {
          const n = Math.max(1, value - 1);
          setText(String(n));
          onCommit(n);
        }}
        className="flex h-7 w-7 items-center justify-center rounded-md text-xs font-bold text-muted hover:bg-line/50 hover:text-ink active:scale-95"
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
        className="tnum w-10 bg-transparent text-center text-xs font-bold text-ink focus:outline-none"
      />
      <button
        type="button"
        onClick={() => {
          const n = Math.min(1000, value + 1);
          setText(String(n));
          onCommit(n);
        }}
        className="flex h-7 w-7 items-center justify-center rounded-md text-xs font-bold text-muted hover:bg-line/50 hover:text-ink active:scale-95"
      >
        +
      </button>
    </div>
  );
}

function PlanCard({ plan, best }: { plan: StorePlanOut; best?: boolean }) {
  return (
    <div
      className={`rounded-2xl border bg-card p-5 shadow-xs transition-shadow hover:shadow-md ${
        best ? "border-save/50 ring-2 ring-save/10" : "border-line"
      }`}
    >
      <header className="mb-3 flex items-start justify-between gap-2 border-b border-line/60 pb-3">
        <div>
          <div className="flex items-center gap-2">
            <StoreBadge storeName={plan.store} displayName={plan.store_display_name} size="md" />
            {best && (
              <span className="rounded-full bg-save px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-white shadow-xs">
                Cheapest Single Store
              </span>
            )}
          </div>
        </div>
        <div className="text-right">
          <div className="text-[10px] uppercase tracking-wider text-faint">Estimated Total</div>
          <div className="tnum text-xl font-extrabold text-ink leading-tight">
            {fmt(plan.total)}
          </div>
        </div>
      </header>

      <ul className="divide-y divide-line/60 text-sm">
        {plan.items.map((it) => (
          <li key={it.item_key} className="flex justify-between gap-3 py-2">
            <span className="truncate text-muted">
              {it.label} <span className="text-xs font-semibold text-faint">× {it.quantity}</span>
            </span>
            <span className="tnum shrink-0 font-bold text-ink">{fmt(it.line_total)}</span>
          </li>
        ))}
      </ul>

      <div className="mt-3 flex justify-between rounded-xl bg-paper/60 p-2 text-xs font-medium text-muted">
        <span className="tnum">Items: {fmt(plan.items_subtotal)}</span>
        <span className="tnum">
          Delivery: {plan.delivery_fee === 0 ? "FREE" : fmt(plan.delivery_fee)}
        </span>
      </div>

      {plan.missing_items.length > 0 && (
        <p className="mt-2 text-xs font-medium text-warn">
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
      <div className="mx-auto max-w-lg py-12 text-center">
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-3xl bg-save-weak text-save">
          <svg
            className="h-8 w-8"
            fill="none"
            viewBox="0 0 24 24"
            strokeWidth={1.8}
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M15.75 10.5V6a3.75 3.75 0 10-7.5 0v4.5m11.356-1.993l1.263 12c.07.665-.45 1.243-1.119 1.243H4.25a1.125 1.125 0 01-1.12-1.243l1.264-12A1.125 1.125 0 015.513 7.5h12.974c.576 0 1.059.435 1.119 1.007zM8.625 10.5a.375.375 0 11-.75 0 .375.375 0 01.75 0zm7.5 0a.375.375 0 11-.75 0 .375.375 0 01.75 0z"
            />
          </svg>
        </div>
        <h1 className="mt-4 text-2xl font-extrabold tracking-tight text-ink">
          Your basket is empty
        </h1>
        <p className="mt-2 text-sm leading-relaxed text-muted">
          Add items to your basket as you explore. Daam Kemon calculates whether buying everything
          from a single store or splitting across two stores saves you more money after delivery
          fees.
        </p>

        <div className="mt-6 flex flex-wrap justify-center gap-2">
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
              className="rounded-full border border-line bg-card px-3.5 py-1.5 text-xs font-semibold text-ink shadow-xs transition-colors hover:border-brand hover:text-brand"
            >
              + {s.label}
            </button>
          ))}
        </div>

        <div className="mt-6">
          <Link
            href="/"
            className="inline-flex items-center gap-1.5 rounded-xl bg-brand px-6 py-2.5 text-xs font-bold text-white shadow-sm hover:bg-brand-dark"
          >
            <span>Explore All Products</span>
            <span>→</span>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div className="flex flex-col justify-between gap-2 sm:flex-row sm:items-center">
        <div>
          <h1 className="text-2xl font-extrabold tracking-tight text-ink sm:text-3xl">
            Basket Optimizer
          </h1>
          <p className="text-xs text-muted sm:text-sm">
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
          className="text-xs font-semibold text-error hover:underline self-start sm:self-auto"
        >
          Clear entire basket
        </button>
      </div>

      {/* Item list */}
      <div className="overflow-hidden rounded-2xl border border-line bg-card shadow-xs">
        <div className="border-b border-line bg-paper/40 px-4 py-2.5 text-xs font-bold text-muted">
          Items to Compare
        </div>
        <ul className="divide-y divide-line/60">
          {entries.map((e) => (
            <li key={e.id} className="flex items-center justify-between gap-3 p-3.5">
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-bold text-ink">{e.label}</p>
                {e.query && <p className="text-xs text-faint">Matched to: {e.query}</p>}
              </div>
              <div className="flex shrink-0 items-center gap-3">
                <QtyInput value={e.quantity} onCommit={(n) => setEntries(setQuantity(e.id, n))} />
                <button
                  onClick={() => setEntries(remove(e.id))}
                  className="rounded-lg p-1.5 text-xs font-medium text-muted transition-colors hover:bg-error/10 hover:text-error"
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
        <div className="flex items-center gap-2 rounded-2xl border border-line bg-card p-4 text-xs font-bold text-muted">
          <span className="h-2 w-2 rounded-full bg-save animate-ping" />
          <span>Calculating optimal store combination across Bangladesh…</span>
        </div>
      )}

      {error && (
        <div className="rounded-2xl border border-error/30 bg-card p-4 text-xs text-error">
          ⚠️ Couldn&apos;t optimize the basket right now. Please retry in a few moments.
        </div>
      )}

      {result?.unresolved_items && result.unresolved_items.length > 0 && (
        <div className="rounded-2xl border border-line bg-card p-4 text-xs text-muted">
          Could not find equivalent listings for:{" "}
          <strong className="text-ink">{result.unresolved_items.join(", ")}</strong>
        </div>
      )}

      {/* OPTIMAL SPLIT (DOPAMINE BANNER) */}
      {result && result.split.length > 0 && (
        <section className="space-y-4">
          <div className="rounded-2xl border border-save/40 bg-gradient-to-r from-save-weak to-white p-5 shadow-xs">
            <div className="flex flex-col justify-between gap-2 sm:flex-row sm:items-center">
              <div>
                <span className="inline-flex items-center gap-1 rounded-full bg-save px-2.5 py-0.5 text-xs font-extrabold text-white">
                  ⚡ Smart Split Recommendation
                </span>
                <h2 className="mt-2 text-xl font-black tracking-tight text-ink sm:text-2xl">
                  Save <span className="text-save">{fmt(result.split_savings)}</span> by splitting
                  between {result.split.length} stores!
                </h2>
                <p className="mt-0.5 text-xs text-muted">
                  Even after paying two delivery fees, this split order is cheaper than any single
                  supermarket.
                </p>
              </div>
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            {result.split.map((p) => (
              <PlanCard key={p.store} plan={p} />
            ))}
          </div>
        </section>
      )}

      {/* CHEAPEST SINGLE STORE */}
      {result?.single_store && (
        <section className="space-y-3">
          <h2 className="text-xs font-bold uppercase tracking-wider text-faint">
            Single Store Option (One Delivery)
          </h2>
          <PlanCard plan={result.single_store} best={result.split.length === 0} />
        </section>
      )}

      {/* ALL STORES COMPARISON */}
      {result && result.all_single_store.length > 0 && (
        <section className="space-y-3">
          <h2 className="text-xs font-bold uppercase tracking-wider text-faint">
            All Supermarkets Ranked (Single Store)
          </h2>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {result.all_single_store.map((p) => (
              <PlanCard key={p.store} plan={p} />
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
