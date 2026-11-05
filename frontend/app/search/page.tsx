"use client";

import { SearchBar } from "@/components/SearchBar";
import { AggregatedGroupCard } from "@/components/AggregatedGroup";
import { api } from "@/lib/api";
import type { CategoryGroupOut, CategoryOut, SearchResponse } from "@/types";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useMemo, useState } from "react";

function SearchInner() {
  const params = useSearchParams();
  const q = params.get("q") || "";
  const categoryKey = params.get("category");
  const subcategoryKey = params.get("subcategory");

  const [data, setData] = useState<SearchResponse | null>(null);
  const [tree, setTree] = useState<CategoryGroupOut[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [retryKey, setRetryKey] = useState(0);

  useEffect(() => {
    api
      .categories()
      .then(setTree)
      .catch(() => {});
  }, [retryKey]);

  useEffect(() => {
    if (!q && !categoryKey) return;
    let stale = false;
    setLoading(true);
    setError(null);
    api
      .search(q, {
        category: categoryKey ?? undefined,
        subcategory: subcategoryKey ?? undefined,
      })
      .then((d) => {
        if (!stale) setData(d);
      })
      .catch((e) => {
        if (!stale) setError(String(e));
      })
      .finally(() => {
        if (!stale) setLoading(false);
      });
    return () => {
      stale = true;
    };
  }, [q, categoryKey, subcategoryKey, retryKey]);

  const activeCategory: CategoryOut | undefined = useMemo(() => {
    if (!tree || !categoryKey) return undefined;
    for (const g of tree) for (const c of g.categories) if (c.key === categoryKey) return c;
    return undefined;
  }, [tree, categoryKey]);

  const buildHref = (overrides: { category?: string | null; subcategory?: string | null }) => {
    const next = new URLSearchParams();
    if (q) next.set("q", q);
    const cat = overrides.category !== undefined ? overrides.category : categoryKey;
    const sub = overrides.subcategory !== undefined ? overrides.subcategory : subcategoryKey;
    if (cat) next.set("category", cat);
    if (sub) next.set("subcategory", sub);
    return `/search?${next.toString()}`;
  };

  return (
    <div className="space-y-6">
      {/* Search Header Container */}
      <div className="rounded-3xl border border-white/10 bg-gradient-to-b from-white/10 to-white/5 p-5 backdrop-blur-2xl shadow-xl">
        <SearchBar initial={q} />

        <div className="mt-4">
          <ActiveFilters
            q={q}
            category={activeCategory}
            subcategoryKey={subcategoryKey}
            buildHref={buildHref}
          />
        </div>

        {activeCategory && activeCategory.subcategories.length > 0 && (
          <div className="mt-4 border-t border-white/10 pt-4">
            <SubcategoryStrip
              category={activeCategory}
              activeKey={subcategoryKey}
              buildHref={buildHref}
            />
          </div>
        )}
      </div>

      {data && (
        <div className="flex items-center justify-between text-xs text-white/60">
          <div>
            Showing <strong className="text-white">{data.total_groups}</strong>{" "}
            {data.total_groups === 1 ? "product group" : "product groups"}
            {q ? <> for &ldquo;{q}&rdquo;</> : null}
          </div>
          <span className="rounded-full bg-save px-2.5 py-0.5 text-xs font-black text-white shadow-xs">
            Sorted Cheapest First
          </span>
        </div>
      )}

      {loading && (
        <div className="space-y-4">
          <div className="flex items-center gap-2 text-xs font-bold text-white/60">
            <span className="h-2 w-2 rounded-full bg-orange-400 animate-ping" />
            <span>Comparing across 6 supermarkets live…</span>
          </div>
          <div className="grid gap-4">
            {Array.from({ length: 3 }).map((_, i) => (
              <div
                key={i}
                className="h-44 animate-pulse rounded-3xl border border-white/10 bg-white/5"
              />
            ))}
          </div>
        </div>
      )}

      {error && (
        <div className="space-y-3 rounded-3xl border border-error/40 bg-black/40 p-6 text-sm text-white/70 backdrop-blur-xl">
          <div className="flex items-center gap-2 text-error">
            <p className="font-bold text-white">Search failed</p>
          </div>
          <p className="text-xs text-white/50">
            {error.includes("timed out")
              ? "The search server is waking up. Please give it a few seconds and try again."
              : "Unable to complete search. Please retry."}
          </p>
          <button
            type="button"
            onClick={() => setRetryKey((k) => k + 1)}
            className="rounded-full bg-white px-5 py-2 text-xs font-black text-black shadow-lg hover:bg-orange-100"
          >
            Retry Search
          </button>
        </div>
      )}

      <div className="grid gap-5">
        {data?.groups.map((g, i) => (
          <AggregatedGroupCard
            key={`${g.category}-${g.subcategory ?? ""}-${g.size_value ?? ""}-${i}`}
            group={g}
          />
        ))}

        {data && data.groups.length === 0 && !loading && (
          <div className="space-y-4 rounded-3xl border border-white/10 bg-black/30 px-6 py-16 text-center text-sm text-white/70 backdrop-blur-xl">
            <p className="font-display text-xl font-black text-white">No matches found</p>
            <p className="text-xs text-white/50 max-w-sm mx-auto">
              We couldn&apos;t find equivalent listings for this search term. Try searching for
              broader terms like &ldquo;oil&rdquo;, &ldquo;rice&rdquo;, &ldquo;dal&rdquo;, or
              &ldquo;eggs&rdquo;.
            </p>
            <div className="pt-2">
              <Link
                href="/categories"
                className="inline-flex rounded-full bg-white px-6 py-3 text-xs font-black text-black shadow-lg hover:bg-orange-100"
              >
                Browse All Categories ›
              </Link>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function ActiveFilters({
  q,
  category,
  subcategoryKey,
  buildHref,
}: {
  q: string;
  category: CategoryOut | undefined;
  subcategoryKey: string | null;
  buildHref: (o: { category?: string | null; subcategory?: string | null }) => string;
}) {
  if (!category && !subcategoryKey) return null;
  const sub = category?.subcategories.find((s) => s.key === subcategoryKey);
  return (
    <div className="flex items-center flex-wrap gap-2 text-xs">
      <span className="font-semibold text-white/40">Filters:</span>
      {category && (
        <FilterChip
          label={category.display}
          removeHref={buildHref({ category: null, subcategory: null })}
        />
      )}
      {sub && <FilterChip label={sub.display} removeHref={buildHref({ subcategory: null })} />}
      {(category || subcategoryKey) && (
        <Link
          href={q ? `/search?q=${encodeURIComponent(q)}` : "/categories"}
          className="text-xs text-white/40 underline underline-offset-2 hover:text-white"
        >
          Clear filters
        </Link>
      )}
    </div>
  );
}

function FilterChip({ label, removeHref }: { label: string; removeHref: string }) {
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full border border-white/20 bg-white/10 px-3 py-1 text-xs font-bold text-white">
      <span>{label}</span>
      <Link
        href={removeHref}
        className="flex h-4 w-4 items-center justify-center rounded-full text-white/60 hover:bg-white/20 hover:text-white"
        aria-label={`Remove ${label}`}
      >
        ×
      </Link>
    </span>
  );
}

function SubcategoryStrip({
  category,
  activeKey,
  buildHref,
}: {
  category: CategoryOut;
  activeKey: string | null;
  buildHref: (o: { category?: string | null; subcategory?: string | null }) => string;
}) {
  return (
    <div className="flex flex-wrap items-center gap-2 text-xs">
      <span className="text-white/40 font-semibold">Subcategory:</span>
      <Link
        href={buildHref({ subcategory: null })}
        className={`rounded-full px-3 py-1 transition-colors ${
          !activeKey
            ? "bg-white text-black font-black shadow-sm"
            : "border border-white/15 bg-white/5 text-white/70 hover:bg-white/15 hover:text-white"
        }`}
      >
        All
      </Link>
      {category.subcategories.map((sc) => (
        <Link
          key={sc.key}
          href={buildHref({ subcategory: sc.key })}
          className={`rounded-full px-3 py-1 transition-colors ${
            activeKey === sc.key
              ? "bg-white text-black font-black shadow-sm"
              : "border border-white/15 bg-white/5 text-white/70 hover:bg-white/15 hover:text-white"
          }`}
        >
          {sc.display}
        </Link>
      ))}
    </div>
  );
}

export default function SearchPage() {
  return (
    <Suspense fallback={<p className="text-sm text-white/50">Loading…</p>}>
      <SearchInner />
    </Suspense>
  );
}
