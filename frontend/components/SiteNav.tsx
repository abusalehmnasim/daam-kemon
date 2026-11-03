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
            className={`relative flex items-center gap-1.5 rounded-lg px-3 py-1.5 transition-colors ${
              active
                ? "bg-card font-semibold text-ink shadow-sm ring-1 ring-line"
                : "text-muted hover:bg-line/50 hover:text-ink"
            }`}
          >
            <span>{l.label}</span>
            {isBasket && totalCount > 0 && (
              <span className="flex h-5 min-w-[20px] items-center justify-center rounded-full bg-save px-1.5 text-[11px] font-bold text-white shadow-sm">
                {totalCount}
              </span>
            )}
          </Link>
        );
      })}
    </nav>
  );
}
