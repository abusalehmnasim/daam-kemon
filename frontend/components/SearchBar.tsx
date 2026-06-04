"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

export function SearchBar({ initial = "" }: { initial?: string }) {
  const [q, setQ] = useState(initial);
  const router = useRouter();

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        if (q.trim()) router.push(`/search?q=${encodeURIComponent(q.trim())}`);
      }}
      className="flex gap-2 w-full"
    >
      <input
        value={q}
        onChange={(e) => setQ(e.target.value)}
        type="search"
        placeholder="আজ কী কিনতে চান? (e.g. 5L oil, miniket 5kg)"
        className="flex-1 px-4 py-3 rounded-lg border border-gray-300 bg-white text-base focus:outline-none focus:ring-2 focus:ring-brand"
        autoFocus
      />
      <button
        type="submit"
        className="px-4 py-3 rounded-lg bg-brand text-white font-medium hover:bg-brand-dark"
      >
        Search
      </button>
    </form>
  );
}
