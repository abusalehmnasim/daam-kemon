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
      className="flex gap-2"
      role="search"
    >
      <input
        value={q}
        onChange={(e) => setQ(e.target.value)}
        type="search"
        placeholder="আজ কী কিনতে চান? (e.g. 5L oil, miniket 5kg)"
        aria-label="Search products"
        className="h-11 flex-1 rounded-lg border border-line bg-card px-4 text-[15px] text-ink placeholder:text-faint focus:border-brand focus:outline-none focus:ring-2 focus:ring-brand/20"
        autoFocus={autoFocus}
      />
      <button
        type="submit"
        className="h-11 rounded-lg bg-brand px-5 text-sm font-semibold text-white transition-colors hover:bg-brand-dark focus-visible:outline-offset-2"
      >
        Search
      </button>
    </form>
  );
}
