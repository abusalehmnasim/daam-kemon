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
    // Guard against out-of-order responses: a slow earlier request must not
    // overwrite a newer one's results (or kill its spinner).
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
        <div className="text-sm text-muted">
          {data.total_groups} {data.total_groups === 1 ? "match" : "matches"}
          {q ? <> for &ldquo;{q}&rdquo;</> : null}
        </div>
      )}

      {loading && <p className="text-sm text-faint">Searching…</p>}
      {error && <p className="text-sm text-muted">Search failed. Please try again.</p>}

      <div className="grid gap-3">
        {data?.groups.map((g, i) => (
          <AggregatedGroupCard
            key={`${g.category}-${g.subcategory ?? ""}-${g.size_value ?? ""}-${i}`}
            group={g}
          />
        ))}
        {data && data.groups.length === 0 && !loading && (
          <div className="space-y-2 rounded-card border border-line bg-card px-4 py-8 text-center text-sm text-muted">
            <p className="font-medium text-ink">No matches found</p>
            <p className="text-faint">
              Nothing tracked for this yet.{" "}
              <Link href="/categories" className="text-ink underline underline-offset-2">
                Browse categories
              </Link>
            </p>
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
          className="text-xs text-faint underline underline-offset-2 hover:text-ink"
        >
          clear all
        </Link>
      )}
    </div>
  );
}

function FilterChip({ label, removeHref }: { label: string; removeHref: string }) {
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full bg-ink px-2.5 py-1 text-xs font-medium text-white">
      {label}
      <Link
        href={removeHref}
        className="text-white/70 hover:text-white"
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
      <span className="text-faint">Narrow by:</span>
      <Link
        href={buildHref({ subcategory: null })}
        className={`rounded-full border px-2.5 py-1 transition-colors ${
          !activeKey
            ? "border-ink bg-ink text-white"
            : "border-line text-muted hover:border-line-strong hover:text-ink"
        }`}
      >
        All
      </Link>
      {category.subcategories.map((sc) => (
        <Link
          key={sc.key}
          href={buildHref({ subcategory: sc.key })}
          className={`rounded-full border px-2.5 py-1 transition-colors ${
            activeKey === sc.key
              ? "border-ink bg-ink text-white"
              : "border-line text-muted hover:border-line-strong hover:text-ink"
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
