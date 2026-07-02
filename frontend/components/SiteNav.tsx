"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const LINKS = [
  { href: "/", label: "Search" },
  { href: "/categories", label: "Categories" },
  { href: "/basket", label: "Basket" },
];

export function SiteNav() {
  const pathname = usePathname();
  return (
    <nav className="flex items-center gap-0.5 text-sm">
      {LINKS.map((l) => {
        const active =
          l.href === "/" ? pathname === "/" || pathname === "/search" : pathname.startsWith(l.href);
        return (
          <Link
            key={l.href}
            href={l.href}
            aria-current={active ? "page" : undefined}
            className={`rounded-md px-2.5 py-1.5 transition-colors ${
              active ? "font-medium text-ink" : "text-muted hover:bg-line/60 hover:text-ink"
            }`}
          >
            {l.label}
          </Link>
        );
      })}
    </nav>
  );
}
