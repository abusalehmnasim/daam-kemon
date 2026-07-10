"use client";

import { api } from "@/lib/api";
import { load, remove, setQuantity, toApi, type BasketEntry } from "@/lib/basketStore";
import type { BasketOptimizeResponse, StorePlanOut } from "@/types";
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
      className="tnum w-14 rounded-md border border-line bg-card px-2 py-1 text-sm text-ink focus:border-brand focus:outline-none focus:ring-2 focus:ring-brand/20"
    />
  );
}

function PlanCard({ plan, best }: { plan: StorePlanOut; best?: boolean }) {
  return (
    <div className={`rounded-card border bg-card p-4 ${best ? "border-save/40" : "border-line"}`}>
      <header className="mb-2 flex items-baseline justify-between gap-2">
        <h3 className="flex items-center gap-2 text-sm font-medium text-ink">
          {best && (
            <span className="rounded bg-save-weak px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wide text-save-dark">
              Best
            </span>
          )}
          {plan.store_display_name}
        </h3>
        <div className="tnum text-[17px] font-semibold text-ink">{fmt(plan.total)}</div>
      </header>
      <ul className="divide-y divide-line/60 text-sm">
        {plan.items.map((it) => (
          <li key={it.item_key} className="flex justify-between gap-3 py-1.5">
            <span className="truncate text-muted">
              {it.label} <span className="text-xs text-faint">× {it.quantity}</span>
            </span>
            <span className="tnum shrink-0 text-ink">{fmt(it.line_total)}</span>
          </li>
        ))}
      </ul>
      <div className="mt-2 flex justify-between text-xs text-faint">
        <span className="tnum">Items {fmt(plan.items_subtotal)}</span>
        <span className="tnum">Delivery {fmt(plan.delivery_fee)}</span>
      </div>
      {plan.missing_items.length > 0 && (
        <p className="mt-2 text-xs text-muted">
          {plan.missing_items.length} item{plan.missing_items.length === 1 ? "" : "s"} not sold here
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
      <div className="mx-auto max-w-md py-12">
        <h1 className="text-xl font-semibold tracking-tight text-ink">Your basket is empty</h1>
        <p className="mt-2 text-[15px] leading-relaxed text-muted">
          Add items as you search. Daam Kemon then finds the cheapest single store for your whole
          list — and whether splitting across stores saves more, delivery fees included.
        </p>
        <div className="mt-5">
          <Link
            href="/"
            className="inline-flex h-10 items-center rounded-lg bg-brand px-4 text-sm font-semibold text-white transition-colors hover:bg-brand-dark"
          >
            Search products
          </Link>
        </div>
        <p className="mt-6 text-xs font-medium uppercase tracking-wide text-faint">Popular</p>
        <div className="mt-2 flex flex-wrap gap-2">
          {QUICK_ADDS.map((s) => (
            <Link
              key={s.q}
              href={`/search?q=${encodeURIComponent(s.q)}`}
              className="rounded-full border border-line bg-card px-3 py-1.5 text-[13px] text-muted transition-colors hover:border-line-strong hover:text-ink"
            >
              {s.label}
            </Link>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold tracking-tight text-ink">Your basket</h1>

      <ul className="divide-y divide-line/70 overflow-hidden rounded-card border border-line bg-card">
        {entries.map((e) => (
          <li key={e.id} className="flex items-center justify-between gap-3 p-3">
            <div className="min-w-0">
              <p className="truncate text-sm font-medium text-ink">{e.label}</p>
              {e.query && <p className="text-xs text-faint">query: {e.query}</p>}
            </div>
            <div className="flex shrink-0 items-center gap-3">
              <QtyInput value={e.quantity} onCommit={(n) => setEntries(setQuantity(e.id, n))} />
              <button
                onClick={() => setEntries(remove(e.id))}
                className="text-xs text-muted transition-colors hover:text-ink"
              >
                Remove
              </button>
            </div>
          </li>
        ))}
      </ul>

      {loading && <p className="text-sm text-faint">Optimizing…</p>}
      {error && <p className="text-sm text-muted">Couldn&apos;t optimize the basket right now.</p>}

      {result?.unresolved_items && result.unresolved_items.length > 0 && (
        <div className="rounded-card border border-line bg-card p-3 text-sm text-muted">
          Not found for: {result.unresolved_items.join(", ")}
        </div>
      )}

      {result?.single_store && (
        <section className="space-y-3">
          <h2 className="text-sm font-medium uppercase tracking-wide text-faint">
            Cheapest single store
          </h2>
          <PlanCard plan={result.single_store} best />
        </section>
      )}

      {result && result.split.length > 0 && (
        <section className="space-y-3">
          <h2 className="text-sm font-medium text-ink">
            Split across stores saves{" "}
            <span className="tnum text-save">{fmt(result.split_savings)}</span>
          </h2>
          <div className="grid gap-3 sm:grid-cols-2">
            {result.split.map((p) => (
              <PlanCard key={p.store} plan={p} />
            ))}
          </div>
        </section>
      )}

      {result && result.all_single_store.length > 0 && (
        <section className="space-y-3">
          <h2 className="text-sm font-medium uppercase tracking-wide text-faint">
            All stores compared
          </h2>
          <div className="grid gap-3 sm:grid-cols-3">
            {result.all_single_store.map((p) => (
              <PlanCard key={p.store} plan={p} />
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
