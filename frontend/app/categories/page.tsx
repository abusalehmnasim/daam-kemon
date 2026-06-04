"use client";

import { api } from "@/lib/api";
import type { CategoryGroupOut } from "@/types";
import Link from "next/link";
import { useEffect, useState } from "react";

export default function CategoriesPage() {
  const [tree, setTree] = useState<CategoryGroupOut[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.categories().then(setTree).catch((e) => setError(String(e)));
  }, []);

  if (error) return <p className="text-sm text-red-600">{error}</p>;
  if (!tree) return <p className="text-sm text-gray-500">Loading categories…</p>;

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-bold">Browse by category</h1>
        <p className="text-sm text-gray-600 mt-1">
          Tap any category to see every brand and store offering side-by-side.
        </p>
      </header>

      {tree.map((group) => (
        <section key={group.group} className="space-y-2">
          <h2 className="text-xs uppercase tracking-wider text-gray-500 font-semibold">
            {group.group}
          </h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2">
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
    <div className={`bg-white border rounded-xl p-3 ${empty ? "border-gray-200 opacity-60" : "border-gray-200"}`}>
      <Link
        href={`/search?category=${encodeURIComponent(c.key)}`}
        className="block font-semibold text-sm hover:text-brand"
      >
        {c.display}
      </Link>
      <p className="text-[11px] text-gray-500 mt-0.5">
        {c.listing_count === 0
          ? "Not yet stocked"
          : `${c.listing_count} listing${c.listing_count === 1 ? "" : "s"}`}
      </p>
      {c.subcategories.length > 0 && (
        <ul className="mt-2 flex flex-wrap gap-1">
          {c.subcategories.slice(0, 6).map((sc) => (
            <li key={sc.key}>
              <Link
                href={`/search?category=${encodeURIComponent(c.key)}&subcategory=${encodeURIComponent(sc.key)}`}
                className="inline-block text-[11px] px-1.5 py-0.5 rounded bg-gray-100 hover:bg-brand hover:text-white transition"
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
