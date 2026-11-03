"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

export function SearchBar({
  initial = "",
  autoFocus = false,
}: {
  initial?: string;
  autoFocus?: boolean;
}) {
  const [q, setQ] = useState(initial);
  const router = useRouter();

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        if (q.trim()) router.push(`/search?q=${encodeURIComponent(q.trim())}`);
      }}
      className="relative flex items-center gap-2 rounded-2xl border border-line bg-card p-1.5 shadow-sm transition-all focus-within:border-brand focus-within:ring-4 focus-within:ring-brand/10 hover:border-line-strong hover:shadow"
      role="search"
    >
      <div className="pointer-events-none flex items-center pl-3 text-muted">
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
            d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z"
          />
        </svg>
      </div>

      <input
        value={q}
        onChange={(e) => setQ(e.target.value)}
        type="search"
        placeholder="Search grocery items (e.g. 5L oil, miniket 5kg, 12 eggs, sugar)..."
        aria-label="Search products"
        className="h-11 flex-1 bg-transparent px-2 text-base text-ink placeholder:text-faint focus:outline-none"
        autoFocus={autoFocus}
      />

      {q && (
        <button
          type="button"
          onClick={() => setQ("")}
          className="flex h-8 w-8 items-center justify-center rounded-full text-muted hover:bg-line/50 hover:text-ink"
          aria-label="Clear search"
        >
          <svg
            className="h-4 w-4"
            fill="none"
            viewBox="0 0 24 24"
            strokeWidth={2}
            stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      )}

      <button
        type="submit"
        className="inline-flex h-11 items-center justify-center rounded-xl bg-brand px-6 text-sm font-bold text-white shadow-sm transition-all hover:bg-brand-dark active:scale-95"
      >
        <span>Search</span>
      </button>
    </form>
  );
}
