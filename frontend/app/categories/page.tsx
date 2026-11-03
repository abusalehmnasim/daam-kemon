"use client";

import { api } from "@/lib/api";
import type { CategoryGroupOut } from "@/types";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

export default function CategoriesPage() {
  const [tree, setTree] = useState<CategoryGroupOut[] | null>(null);
  const [filter, setFilter] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .categories()
      .then(setTree)
      .catch((e) => setError(String(e)));
  }, []);

  const totalCategories = useMemo(() => {
    if (!tree) return 0;
    return tree.reduce((acc, g) => acc + g.categories.length, 0);
  }, [tree]);

  const filteredGroups = useMemo(() => {
    if (!tree) return [];
    if (!filter.trim()) return tree;
    const term = filter.toLowerCase().trim();

    return tree
      .map((g) => {
        const matchingCats = g.categories.filter(
          (c) =>
            c.display.toLowerCase().includes(term) ||
            c.key.toLowerCase().includes(term) ||
            c.subcategories.some((sc) => sc.display.toLowerCase().includes(term))
        );
        return { ...g, categories: matchingCats };
      })
      .filter((g) => g.categories.length > 0);
  }, [tree, filter]);

  if (error) {
    return (
      <div className="rounded-2xl border border-line bg-card p-8 text-center">
        <p className="text-sm font-semibold text-muted">Couldn&apos;t load categories.</p>
        <button
          onClick={() => {
            setError(null);
            setTree(null);
            api
              .categories()
              .then(setTree)
              .catch((e) => setError(String(e)));
          }}
          className="mt-3 rounded-lg bg-brand px-4 py-2 text-xs font-bold text-white shadow-xs"
        >
          Try Again
        </button>
      </div>
    );
  }

  if (!tree) {
    return (
      <div className="space-y-6">
        <div className="h-8 w-48 animate-pulse rounded-lg bg-line/60" />
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="h-32 animate-pulse rounded-2xl bg-card border border-line" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <header className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-extrabold tracking-tight text-ink sm:text-3xl">
              Browse Categories
            </h1>
            <span className="rounded-full bg-brand/10 px-2.5 py-0.5 text-xs font-bold text-brand">
              {totalCategories} Categories
            </span>
          </div>
          <p className="mt-1 text-sm text-muted">
            All Bangladeshi grocery categories, with live store comparison side-by-side.
          </p>
        </div>

        <div className="w-full sm:w-64">
          <input
            type="search"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            placeholder="Filter categories (e.g. oil, rice, dal)..."
            className="w-full rounded-xl border border-line bg-card px-3.5 py-2 text-xs text-ink placeholder:text-faint focus:border-brand focus:outline-none focus:ring-2 focus:ring-brand/10"
          />
        </div>
      </header>

      {filteredGroups.length === 0 ? (
        <div className="rounded-2xl border border-line bg-card p-10 text-center text-sm text-muted">
          No categories found matching &ldquo;{filter}&rdquo;.
        </div>
      ) : (
        filteredGroups.map((group) => (
          <section key={group.group} className="space-y-3">
            <h2 className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-faint">
              <span className="h-1.5 w-1.5 rounded-full bg-brand" />
              <span>{group.group}</span>
            </h2>
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
              {group.categories.map((c) => (
                <CategoryCard key={c.key} c={c} />
              ))}
            </div>
          </section>
        ))
      )}
    </div>
  );
}

function CategoryCard({ c }: { c: CategoryGroupOut["categories"][number] }) {
  const empty = c.listing_count === 0;
  return (
    <div
      className={`flex h-full flex-col justify-between rounded-2xl border border-line bg-card p-4 transition-all hover:border-brand/40 hover:shadow-md ${
        empty ? "opacity-60" : ""
      }`}
    >
      <div>
        <Link
          href={`/search?category=${encodeURIComponent(c.key)}`}
          className="font-bold text-ink hover:text-brand"
        >
          {c.display}
        </Link>
        <p className="mt-0.5 text-xs text-muted">
          {empty ? "Not yet stocked" : `${c.listing_count.toLocaleString("en-US")} listings`}
        </p>
      </div>

      {c.subcategories.length > 0 && (
        <ul className="mt-3 flex flex-wrap gap-1 border-t border-line/60 pt-2.5">
          {c.subcategories.slice(0, 5).map((sc) => (
            <li key={sc.key}>
              <Link
                href={`/search?category=${encodeURIComponent(c.key)}&subcategory=${encodeURIComponent(sc.key)}`}
                className="inline-block rounded-md border border-line bg-paper/50 px-2 py-0.5 text-[11px] font-medium text-muted transition-colors hover:border-brand hover:bg-brand/5 hover:text-brand"
              >
                {sc.display}
              </Link>
            </li>
          ))}
          {c.subcategories.length > 5 && (
            <li className="text-[11px] font-semibold text-faint self-center px-1">
              +{c.subcategories.length - 5}
            </li>
          )}
        </ul>
      )}
    </div>
  );
}
