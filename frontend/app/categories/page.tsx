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
      <div className="rounded-3xl border border-white/10 bg-black/40 p-10 text-center text-white backdrop-blur-xl">
        <p className="text-sm font-bold text-white/70">Couldn&apos;t load categories.</p>
        <button
          onClick={() => {
            setError(null);
            setTree(null);
            api
              .categories()
              .then(setTree)
              .catch((e) => setError(String(e)));
          }}
          className="mt-4 rounded-full bg-white px-6 py-2.5 text-xs font-black text-black shadow-lg hover:bg-orange-100"
        >
          Try Again
        </button>
      </div>
    );
  }

  if (!tree) {
    return (
      <div className="space-y-6">
        <div className="h-8 w-48 animate-pulse rounded-full bg-white/10" />
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <div
              key={i}
              className="h-36 animate-pulse rounded-3xl border border-white/10 bg-white/5"
            />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-10">
      <header className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="font-display text-3xl font-black tracking-tight text-white sm:text-4xl">
              Browse Categories
            </h1>
            <span className="rounded-full bg-white/10 px-3 py-1 text-xs font-bold text-orange-300">
              {totalCategories} Categories
            </span>
          </div>
          <p className="mt-1 text-sm text-white/60">
            All grocery buckets, cross-matched across 6 supermarkets.
          </p>
        </div>

        <div className="w-full sm:w-72">
          <input
            type="search"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            placeholder="Filter categories (e.g. oil, rice, dal)..."
            className="w-full rounded-full border border-white/15 bg-white/5 px-4 py-2.5 text-xs text-white placeholder:text-white/40 backdrop-blur-xl focus:border-white/30 focus:outline-none"
          />
        </div>
      </header>

      {filteredGroups.length === 0 ? (
        <div className="rounded-3xl border border-white/10 bg-black/30 p-12 text-center text-sm text-white/50">
          No categories found matching &ldquo;{filter}&rdquo;.
        </div>
      ) : (
        filteredGroups.map((group) => (
          <section key={group.group} className="space-y-4">
            <h2 className="flex items-center gap-2 text-xs font-black uppercase tracking-wider text-white/40">
              <span className="h-1.5 w-1.5 rounded-full bg-orange-400" />
              <span>{group.group}</span>
            </h2>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
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
      className={`group flex h-full flex-col justify-between rounded-3xl border border-white/10 bg-gradient-to-b from-white/10 to-white/5 p-5 backdrop-blur-xl shadow-lg transition-all hover:border-white/25 hover:scale-[1.02] ${
        empty ? "opacity-40" : ""
      }`}
    >
      <div>
        <Link
          href={`/search?category=${encodeURIComponent(c.key)}`}
          className="font-display font-bold text-base text-white group-hover:text-orange-300"
        >
          {c.display}
        </Link>
        <p className="mt-1 text-xs text-white/50">
          {empty ? "Not yet stocked" : `${c.listing_count.toLocaleString("en-US")} listings`}
        </p>
      </div>

      {c.subcategories.length > 0 && (
        <ul className="mt-4 flex flex-wrap gap-1.5 border-t border-white/10 pt-3">
          {c.subcategories.slice(0, 5).map((sc) => (
            <li key={sc.key}>
              <Link
                href={`/search?category=${encodeURIComponent(c.key)}&subcategory=${encodeURIComponent(sc.key)}`}
                className="inline-block rounded-full border border-white/10 bg-white/5 px-2.5 py-0.5 text-[11px] font-semibold text-white/70 transition-colors hover:border-white/30 hover:bg-white/15 hover:text-white"
              >
                {sc.display}
              </Link>
            </li>
          ))}
          {c.subcategories.length > 5 && (
            <li className="text-[11px] font-bold text-white/40 self-center px-1">
              +{c.subcategories.length - 5}
            </li>
          )}
        </ul>
      )}
    </div>
  );
}
