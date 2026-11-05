"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

const POPULAR_SEARCHES = [
  { label: "5L Soybean Oil", q: "5L soybean oil", tag: "Save ৳70" },
  { label: "Miniket Rice 5kg", q: "miniket rice 5kg", tag: "Save ৳50" },
  { label: "12 Eggs", q: "12 eggs", tag: "Save ৳17" },
  { label: "Sugar 1kg", q: "sugar 1kg", tag: "Save ৳14" },
  { label: "Masoor Dal 1kg", q: "masoor dal 1kg", tag: "Save ৳17" },
  { label: "Beef 1kg", q: "beef 1kg", tag: "Live rates" },
];

export function FloatingSearch() {
  const [q, setQ] = useState("");
  const router = useRouter();

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (q.trim()) {
      router.push(`/search?q=${encodeURIComponent(q.trim())}`);
    }
  };

  return (
    <div className="mx-auto max-w-3xl space-y-3">
      {/* Search Input Bar */}
      <form
        onSubmit={handleSearch}
        className="flex items-center gap-2 rounded-full border border-white/15 bg-white/5 p-2 shadow-2xl backdrop-blur-xl transition-all focus-within:border-white/30 focus-within:bg-white/10"
      >
        <div className="pl-4 text-white/50">
          <svg
            className="h-5 w-5"
            fill="none"
            viewBox="0 0 24 24"
            strokeWidth={2.2}
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
          type="search"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Search any grocery item across all 6 stores (e.g. 5L oil, miniket, 12 eggs)..."
          className="h-11 flex-1 bg-transparent px-2 text-sm text-white placeholder:text-white/40 focus:outline-none sm:text-base"
        />

        {q && (
          <button
            type="button"
            onClick={() => setQ("")}
            className="flex h-8 w-8 items-center justify-center rounded-full text-white/50 hover:bg-white/10 hover:text-white"
          >
            ×
          </button>
        )}

        <button
          type="submit"
          className="inline-flex h-11 items-center justify-center rounded-full bg-white px-7 text-xs font-black text-black shadow-lg transition-all hover:bg-orange-100 hover:scale-105 active:scale-95"
        >
          <span>Search</span>
        </button>
      </form>

      {/* Suggested Search Pills */}
      <div className="flex flex-wrap items-center justify-center gap-2 pt-1 text-xs">
        <span className="font-semibold text-white/40">Trending:</span>
        {POPULAR_SEARCHES.map((item) => (
          <Link
            key={item.q}
            href={`/search?q=${encodeURIComponent(item.q)}`}
            className="group inline-flex items-center gap-1.5 rounded-full border border-white/10 bg-white/5 px-3.5 py-1 text-white/70 backdrop-blur-md transition-all hover:border-white/25 hover:bg-white/15 hover:text-white"
          >
            <span>{item.label}</span>
            {item.tag && (
              <span className="rounded-full bg-save-weak/20 px-1.5 py-0.2 text-[10px] font-bold text-emerald-300">
                {item.tag}
              </span>
            )}
          </Link>
        ))}
      </div>
    </div>
  );
}
