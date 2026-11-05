"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useBasket } from "@/lib/useBasket";

export function MobileBottomNav() {
  const pathname = usePathname();
  const { totalCount } = useBasket();

  const isExplore = pathname === "/" || pathname === "/search";
  const isCategories = pathname.startsWith("/categories");
  const isBasket = pathname.startsWith("/basket");

  return (
    <nav
      aria-label="Mobile Navigation"
      className="fixed bottom-0 left-0 right-0 z-40 border-t border-white/10 bg-[#0E0A08]/90 backdrop-blur-2xl sm:hidden"
    >
      <div className="grid grid-cols-3 items-center py-2">
        <Link
          href="/"
          className={`flex flex-col items-center justify-center gap-1 py-1 text-center transition-colors ${
            isExplore ? "font-bold text-orange-400" : "text-white/60 hover:text-white"
          }`}
        >
          <svg
            className="h-5 w-5"
            fill="none"
            viewBox="0 0 24 24"
            strokeWidth={isExplore ? 2.5 : 1.8}
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z"
            />
          </svg>
          <span className="text-[10px]">Explore</span>
        </Link>

        <Link
          href="/categories"
          className={`flex flex-col items-center justify-center gap-1 py-1 text-center transition-colors ${
            isCategories ? "font-bold text-orange-400" : "text-white/60 hover:text-white"
          }`}
        >
          <svg
            className="h-5 w-5"
            fill="none"
            viewBox="0 0 24 24"
            strokeWidth={isCategories ? 2.5 : 1.8}
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M3.75 6A2.25 2.25 0 016 3.75h2.25A2.25 2.25 0 0110.5 6v2.25a2.25 2.25 0 01-2.25 2.25H6a2.25 2.25 0 01-2.25-2.25V6zM3.75 15.75A2.25 2.25 0 016 13.5h2.25a2.25 2.25 0 012.25 2.25V18a2.25 2.25 0 01-2.25 2.25H6A2.25 2.25 0 013.75 18v-2.25zM13.5 6a2.25 2.25 0 012.25-2.25H18A2.25 2.25 0 0120.25 6v2.25A2.25 2.25 0 0118 10.5h-2.25a2.25 2.25 0 01-2.25-2.25V6zM13.5 15.75a2.25 2.25 0 012.25-2.25H18a2.25 2.25 0 012.25 2.25V18A2.25 2.25 0 0118 20.25h-2.25A2.25 2.25 0 0113.5 18v-2.25z"
            />
          </svg>
          <span className="text-[10px]">Categories</span>
        </Link>

        <Link
          href="/basket"
          className={`relative flex flex-col items-center justify-center gap-1 py-1 text-center transition-colors ${
            isBasket ? "font-bold text-orange-400" : "text-white/60 hover:text-white"
          }`}
        >
          <div className="relative">
            <svg
              className="h-5 w-5"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={isBasket ? 2.5 : 1.8}
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M15.75 10.5V6a3.75 3.75 0 10-7.5 0v4.5m11.356-1.993l1.263 12c.07.665-.45 1.243-1.119 1.243H4.25a1.125 1.125 0 01-1.12-1.243l1.264-12A1.125 1.125 0 015.513 7.5h12.974c.576 0 1.059.435 1.119 1.007zM8.625 10.5a.375.375 0 11-.75 0 .375.375 0 01.75 0zm7.5 0a.375.375 0 11-.75 0 .375.375 0 01.75 0z"
              />
            </svg>
            {totalCount > 0 && (
              <span className="absolute -right-2.5 -top-1.5 flex h-4 min-w-[16px] items-center justify-center rounded-full bg-save px-1 text-[9px] font-black text-white shadow">
                {totalCount}
              </span>
            )}
          </div>
          <span className="text-[10px]">Basket</span>
        </Link>
      </div>
    </nav>
  );
}
