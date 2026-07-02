"use client";

import { api } from "@/lib/api";
import type { CategoryGroupOut } from "@/types";
import Link from "next/link";
import { useEffect, useState } from "react";

export default function CategoriesPage() {
  const [tree, setTree] = useState<CategoryGroupOut[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .categories()
      .then(setTree)
      .catch((e) => setError(String(e)));
  }, []);

  if (error) return <p className="text-sm text-muted">Couldn&apos;t load categories.</p>;
  if (!tree) return <p className="text-sm text-faint">Loading categories…</p>;

  return (
    <div className="space-y-8">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight text-ink">Browse by category</h1>
        <p className="mt-1 text-[15px] text-muted">Every brand and store, compared side by side.</p>
      </header>

      {tree.map((group) => (
        <section key={group.group}>
          <h2 className="mb-2.5 text-[11px] font-medium uppercase tracking-wider text-faint">
            {group.group}
          </h2>
          <div className="grid grid-cols-2 gap-2.5 sm:grid-cols-3 lg:grid-cols-4">
            {group.categories.map((c) => (
              <CategoryCard key={c.key} c={c} />
            ))}
          </div>
        </section>
      ))}
    </div>
  );
}

function CategoryCard({ c }: { c: CategoryGroupOut["categories"][number] }) {
  const empty = c.listing_count === 0;
  return (
    <div
      className={`flex h-full flex-col rounded-card border border-line bg-card p-3.5 transition-colors ${
        empty ? "opacity-70" : "hover:border-line-strong"
      }`}
    >
      <Link
        href={`/search?category=${encodeURIComponent(c.key)}`}
        className="text-sm font-medium text-ink hover:text-brand"
      >
        {c.display}
      </Link>
      <p className="mt-0.5 text-[11px] text-faint">
        {empty
          ? "Not yet stocked"
          : `${c.listing_count.toLocaleString("en-US")} listing${c.listing_count === 1 ? "" : "s"}`}
      </p>
      {c.subcategories.length > 0 && (
        <ul className="mt-auto flex flex-wrap gap-1 pt-2.5">
          {c.subcategories.slice(0, 6).map((sc) => (
            <li key={sc.key}>
              <Link
                href={`/search?category=${encodeURIComponent(c.key)}&subcategory=${encodeURIComponent(sc.key)}`}
                className="inline-block rounded border border-line px-1.5 py-0.5 text-[11px] text-muted transition-colors hover:border-brand hover:text-brand"
              >
                {sc.display}
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
