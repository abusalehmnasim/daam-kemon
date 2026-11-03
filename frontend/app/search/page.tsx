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

  // Load the category tree once for the filter sidebar
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
      <div className="rounded-2xl border border-line bg-card p-4 shadow-xs">
        <SearchBar initial={q} />

        <div className="mt-3">
          <ActiveFilters
            q={q}
            category={activeCategory}
            subcategoryKey={subcategoryKey}
            buildHref={buildHref}
          />
        </div>

        {activeCategory && activeCategory.subcategories.length > 0 && (
          <div className="mt-3 border-t border-line/60 pt-3">
            <SubcategoryStrip
              category={activeCategory}
              activeKey={subcategoryKey}
              buildHref={buildHref}
            />
          </div>
        )}
      </div>

      {data && (
        <div className="flex items-center justify-between text-xs text-muted">
          <div>
            Showing <strong className="text-ink">{data.total_groups}</strong>{" "}
            {data.total_groups === 1 ? "product group" : "product groups"}
            {q ? <> for &ldquo;{q}&rdquo;</> : null}
          </div>
          <span className="rounded-full bg-save-weak px-2 py-0.5 text-[11px] font-bold text-save-dark">
            Sorted Cheapest First
          </span>
        </div>
      )}

      {loading && (
        <div className="space-y-3">
          <div className="flex items-center gap-2 text-xs font-semibold text-muted">
            <span className="h-2 w-2 rounded-full bg-brand animate-ping" />
            <span>Searching across 6 supermarkets…</span>
          </div>
          <div className="grid gap-4">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="h-44 animate-pulse rounded-2xl border border-line bg-card" />
            ))}
          </div>
        </div>
      )}

      {error && (
        <div className="space-y-3 rounded-2xl border border-error/30 bg-card p-6 text-sm text-muted">
          <div className="flex items-center gap-2 text-error">
            <svg
              className="h-5 w-5"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={2}
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z"
              />
            </svg>
            <p className="font-bold text-ink">Search failed</p>
          </div>
          <p className="text-xs text-muted">
            {error.includes("timed out")
              ? "The search server is waking up. Please give it a few seconds and try again."
              : "Unable to complete search. Please retry."}
          </p>
          <button
            type="button"
            onClick={() => setRetryKey((k) => k + 1)}
            className="rounded-xl bg-brand px-4 py-2 text-xs font-bold text-white shadow-xs transition-colors hover:bg-brand-dark"
          >
            Retry Search
          </button>
        </div>
      )}

      <div className="grid gap-4">
        {data?.groups.map((g, i) => (
          <AggregatedGroupCard
            key={`${g.category}-${g.subcategory ?? ""}-${g.size_value ?? ""}-${i}`}
            group={g}
          />
        ))}

        {data && data.groups.length === 0 && !loading && (
          <div className="space-y-3 rounded-2xl border border-line bg-card px-4 py-12 text-center text-sm text-muted">
            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-paper text-muted">
              <svg
                className="h-6 w-6"
                fill="none"
                viewBox="0 0 24 24"
                strokeWidth={1.8}
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z"
                />
              </svg>
            </div>
            <p className="font-bold text-ink text-base">No matches found</p>
            <p className="text-xs text-muted max-w-sm mx-auto">
              We couldn&apos;t find equivalent listings for this search term. Try searching for
              broader terms like &ldquo;oil&rdquo;, &ldquo;rice&rdquo;, &ldquo;dal&rdquo;, or
              &ldquo;eggs&rdquo;.
            </p>
            <div className="pt-2">
              <Link
                href="/categories"
                className="inline-flex rounded-xl bg-brand px-4 py-2 text-xs font-bold text-white shadow-xs hover:bg-brand-dark"
              >
                Browse All Categories →
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
      <span className="font-medium text-muted">Filters:</span>
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
          className="text-xs text-faint underline underline-offset-2 hover:text-ink"
        >
          Clear filters
        </Link>
      )}
    </div>
  );
}

function FilterChip({ label, removeHref }: { label: string; removeHref: string }) {
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full border border-line bg-paper px-2.5 py-1 text-xs font-semibold text-ink">
      <span>{label}</span>
      <Link
        href={removeHref}
        className="flex h-3.5 w-3.5 items-center justify-center rounded-full text-muted hover:bg-line hover:text-ink"
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
    <div className="flex flex-wrap items-center gap-1.5 text-xs">
      <span className="text-faint">Narrow:</span>
      <Link
        href={buildHref({ subcategory: null })}
        className={`rounded-full px-2.5 py-1 transition-colors ${
          !activeKey
            ? "bg-brand text-white font-bold shadow-xs"
            : "border border-line text-muted hover:border-line-strong hover:text-ink"
        }`}
      >
        All
      </Link>
      {category.subcategories.map((sc) => (
        <Link
          key={sc.key}
          href={buildHref({ subcategory: sc.key })}
          className={`rounded-full px-2.5 py-1 transition-colors ${
            activeKey === sc.key
              ? "bg-brand text-white font-bold shadow-xs"
              : "border border-line text-muted hover:border-line-strong hover:text-ink"
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
    <Suspense fallback={<p className="text-sm text-faint">Loading…</p>}>
      <SearchInner />
    </Suspense>
  );
}
