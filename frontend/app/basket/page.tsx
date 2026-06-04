"use client";

import { api } from "@/lib/api";
import { load, remove, setQuantity, toApi, type BasketEntry } from "@/lib/basketStore";
import type { BasketOptimizeResponse, StorePlanOut } from "@/types";
import Link from "next/link";
import { useEffect, useState } from "react";

function fmt(n: number) {
  return "৳ " + n.toLocaleString("en-BD", { maximumFractionDigits: 2 });
}

function PlanCard({ plan, title }: { plan: StorePlanOut; title?: string }) {
  return (
    <div className="bg-white border border-gray-200 rounded-xl p-4">
      <header className="flex items-baseline justify-between mb-2">
        <h3 className="font-semibold">
          {title ? <span className="text-brand mr-2">{title}</span> : null}
          {plan.store_display_name}
        </h3>
        <div className="text-lg font-bold">{fmt(plan.total)}</div>
      </header>
      <ul className="text-sm divide-y divide-gray-100">
        {plan.items.map((it) => (
          <li key={it.item_key} className="flex justify-between py-1.5 gap-3">
            <span className="truncate">
              {it.label} <span className="text-xs text-gray-500">× {it.quantity}</span>
            </span>
            <span className="text-gray-700 shrink-0">{fmt(it.line_total)}</span>
          </li>
        ))}
      </ul>
      <div className="text-xs text-gray-500 mt-2 flex justify-between">
        <span>Items: {fmt(plan.items_subtotal)}</span>
        <span>Delivery: {fmt(plan.delivery_fee)}</span>
      </div>
      {plan.missing_items.length > 0 && (
        <p className="text-xs text-amber-700 mt-2">
          Missing at this store: {plan.missing_items.length} item(s)
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

  useEffect(() => { setEntries(load()); }, []);

  const refreshOptimize = async (next: BasketEntry[]) => {
    if (next.length === 0) { setResult(null); return; }
    setLoading(true); setError(null);
    try {
      const res = await api.optimize(toApi(next));
      setResult(res);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { void refreshOptimize(entries); }, [entries]);

  if (entries.length === 0) {
    return (
      <div className="text-center py-12 space-y-3">
        <p className="text-gray-600">Your basket is empty.</p>
        <Link href="/" className="inline-block px-4 py-2 rounded-md bg-brand text-white">
          Start shopping
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Your basket</h1>

      <ul className="bg-white border border-gray-200 rounded-xl divide-y divide-gray-100">
        {entries.map((e) => (
          <li key={e.id} className="flex items-center justify-between p-3 gap-3">
            <div className="min-w-0">
              <p className="font-medium truncate">{e.label}</p>
              {e.query && <p className="text-xs text-gray-500">query: {e.query}</p>}
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <input
                type="number"
                min={1}
                value={e.quantity}
                onChange={(ev) => setEntries(setQuantity(e.id, Math.max(1, Number(ev.target.value) || 1)))}
                className="w-16 px-2 py-1 border border-gray-300 rounded text-sm"
              />
              <button
                onClick={() => setEntries(remove(e.id))}
                className="text-xs text-red-600 hover:underline"
              >
                Remove
              </button>
            </div>
          </li>
        ))}
      </ul>

      {loading && <p className="text-sm text-gray-500">Optimizing…</p>}
      {error && <p className="text-sm text-red-600">{error}</p>}

      {result?.unresolved_items && result.unresolved_items.length > 0 && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 text-sm">
          We couldn&apos;t resolve: {result.unresolved_items.join(", ")}
        </div>
      )}

      {result?.single_store && (
        <section className="space-y-3">
          <h2 className="font-semibold text-lg">Cheapest single store</h2>
          <PlanCard plan={result.single_store} title="Best" />
        </section>
      )}

      {result && result.split.length > 0 && (
        <section className="space-y-3">
          <h2 className="font-semibold text-lg">
            Smart split — saves <span className="text-brand">{fmt(result.split_savings)}</span>
          </h2>
          <div className="grid sm:grid-cols-2 gap-3">
            {result.split.map((p) => <PlanCard key={p.store} plan={p} />)}
          </div>
        </section>
      )}

      {result && result.all_single_store.length > 0 && (
        <section className="space-y-3">
          <h2 className="font-semibold text-lg">All stores compared</h2>
          <div className="grid sm:grid-cols-3 gap-3">
            {result.all_single_store.map((p) => <PlanCard key={p.store} plan={p} />)}
          </div>
        </section>
      )}
    </div>
  );
}
