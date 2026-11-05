"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useBasket } from "@/lib/useBasket";

const LINKS = [
  { href: "/", label: "Explore" },
  { href: "/categories", label: "Categories" },
  { href: "/basket", label: "Basket" },
];

export function SiteNav() {
  const pathname = usePathname();
  const { totalCount } = useBasket();

  return (
    <nav className="flex items-center gap-1 text-sm">
      {LINKS.map((l) => {
        const isBasket = l.href === "/basket";
        const active =
          l.href === "/" ? pathname === "/" || pathname === "/search" : pathname.startsWith(l.href);
        return (
          <Link
            key={l.href}
            href={l.href}
            aria-current={active ? "page" : undefined}
            className={`relative flex items-center gap-1.5 rounded-full px-4 py-1.5 text-xs font-bold transition-all ${
              active
                ? "bg-white text-black shadow-md scale-105"
                : "text-white/70 hover:bg-white/10 hover:text-white"
            }`}
          >
            <span>{l.label}</span>
            {isBasket && totalCount > 0 && (
              <span className="flex h-5 min-w-[20px] items-center justify-center rounded-full bg-save px-1.5 text-[10px] font-black text-white shadow-xs">
                {totalCount}
              </span>
            )}
          </Link>
        );
      })}
    </nav>
  );
}
