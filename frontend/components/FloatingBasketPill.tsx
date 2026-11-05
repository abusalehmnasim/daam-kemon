"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useBasket } from "@/lib/useBasket";

export function FloatingBasketPill() {
  const pathname = usePathname();
  const { entries, totalCount } = useBasket();

  // Don't show if on the basket page itself or if basket is empty
  if (pathname === "/basket" || entries.length === 0) {
    return null;
  }

  return (
    <aside
      aria-label="Quick Basket"
      className="fixed bottom-16 left-0 right-0 z-40 px-4 sm:bottom-6"
    >
      <div className="mx-auto flex max-w-xl items-center justify-between gap-4 rounded-3xl border border-white/20 bg-[#1A120E]/90 p-3.5 shadow-2xl backdrop-blur-2xl ring-1 ring-white/10 transition-transform animate-in fade-in slide-in-from-bottom-3">
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-save/20 text-save-bright">
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
                d="M15.75 10.5V6a3.75 3.75 0 10-7.5 0v4.5m11.356-1.993l1.263 12c.07.665-.45 1.243-1.119 1.243H4.25a1.125 1.125 0 01-1.12-1.243l1.264-12A1.125 1.125 0 015.513 7.5h12.974c.576 0 1.059.435 1.119 1.007zM8.625 10.5a.375.375 0 11-.75 0 .375.375 0 01.75 0zm7.5 0a.375.375 0 11-.75 0 .375.375 0 01.75 0z"
              />
            </svg>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-sm font-black text-white">
                {totalCount} {totalCount === 1 ? "item" : "items"} in basket
              </span>
              <span className="rounded-full bg-save px-2 py-0.5 text-[10px] font-extrabold text-white">
                Multi-Store Split
              </span>
            </div>
            <p className="text-xs text-white/60">Find cheapest store & best split delivery</p>
          </div>
        </div>

        <Link
          href="/basket"
          className="inline-flex shrink-0 items-center gap-1.5 rounded-full bg-white px-5 py-2.5 text-xs font-black text-black shadow-lg transition-all hover:bg-orange-100 hover:scale-105 active:scale-95"
        >
          <span>Optimize</span>
          <span>›</span>
        </Link>
      </div>
    </aside>
  );
}
