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

  // Load the category tree once for the filter sidebar
  useEffect(() => {
    api
      .categories()
      .then(setTree)
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (!q && !categoryKey) return;
    setLoading(true);
    setError(null);
    api
      .search(q, {
        category: categoryKey ?? undefined,
        subcategory: subcategoryKey ?? undefined,
      })
      .then(setData)
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  }, [q, categoryKey, subcategoryKey]);

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
    <div className="space-y-5">
      <SearchBar initial={q} />

      <ActiveFilters
        q={q}
        category={activeCategory}
        subcategoryKey={subcategoryKey}
        buildHref={buildHref}
      />

      {activeCategory && activeCategory.subcategories.length > 0 && (
        <SubcategoryStrip
          category={activeCategory}
          activeKey={subcategoryKey}
          buildHref={buildHref}
        />
      )}

      {data && (
        <div className="text-sm text-gray-600">
          {data.total_groups} {data.total_groups === 1 ? "match" : "matches"}
          {q ? <> for &ldquo;{q}&rdquo;</> : null}
        </div>
      )}

      {loading && <p className="text-sm text-gray-500">Searching…</p>}
      {error && <p className="text-sm text-red-600">Search failed: {error}</p>}

      <div className="grid gap-3">
        {data?.groups.map((g, i) => (
          <AggregatedGroupCard
            key={`${g.category}-${g.subcategory ?? ""}-${g.size_value ?? ""}-${i}`}
            group={g}
          />
        ))}
        {data && data.groups.length === 0 && !loading && (
          <div className="text-sm text-gray-500 space-y-2">
            <p>No matches.</p>
            {categoryKey && (
              <p>
                This category may not have any scraped listings yet.{" "}
                <Link href="/categories" className="text-brand underline">
                  Browse other categories
                </Link>
                .
              </p>
            )}
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
    <div className="flex items-center flex-wrap gap-2 text-sm">
      <span className="text-xs text-gray-500">Filters:</span>
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
          className="text-xs text-gray-500 underline hover:text-brand"
        >
          clear all
        </Link>
      )}
    </div>
  );
}

function FilterChip({ label, removeHref }: { label: string; removeHref: string }) {
  return (
    <span className="inline-flex items-center gap-1 bg-brand/10 text-brand px-2 py-1 rounded-full text-xs">
      {label}
      <Link href={removeHref} className="hover:text-brand-dark" aria-label={`Remove ${label}`}>
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
      <span className="text-gray-500">Narrow by:</span>
      <Link
        href={buildHref({ subcategory: null })}
        className={`px-2 py-1 rounded-full border ${
          !activeKey ? "border-brand text-brand bg-brand/10" : "border-gray-200 hover:border-brand"
        }`}
      >
        All
      </Link>
      {category.subcategories.map((sc) => (
        <Link
          key={sc.key}
          href={buildHref({ subcategory: sc.key })}
          className={`px-2 py-1 rounded-full border ${
            activeKey === sc.key
              ? "border-brand text-brand bg-brand/10"
              : "border-gray-200 hover:border-brand"
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
    <Suspense fallback={<p className="text-sm text-gray-500">Loading…</p>}>
      <SearchInner />
    </Suspense>
  );
}
