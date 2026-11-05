"use client";

import { HeroShowcase } from "@/components/HeroShowcase";
import { FloatingSearch } from "@/components/FloatingSearch";
import { MarketShowdown } from "@/components/MarketShowdown";
import { BazaarBundles } from "@/components/BazaarBundles";
import { CategoryLookbook } from "@/components/CategoryLookbook";
import { StoreMatrix } from "@/components/StoreMatrix";

export default function HomePage() {
  return (
    <div className="space-y-16 sm:space-y-20">
      {/* 1. THE HERO SHOWCASE CANVAS (Inspired by Pinterest Pin) */}
      <HeroShowcase />

      {/* 2. FLOATING SEARCH COMMAND CENTER */}
      <FloatingSearch />

      {/* 3. TODAY'S TOP MARKET DISCREPANCIES */}
      <MarketShowdown />

      {/* 4. 1-CLICK BAZAAR BUNDLES */}
      <BazaarBundles />

      {/* 5. CURATED CATEGORY LOOKBOOK */}
      <CategoryLookbook />

      {/* 6. SUPERMARKET DELIVERY ECONOMICS */}
      <StoreMatrix />

      {/* 7. WHY DAAM KEMON (Value Props in Dark Glassmorphism) */}
      <section className="grid gap-5 sm:grid-cols-3">
        <div className="rounded-3xl border border-white/10 bg-gradient-to-b from-white/10 to-white/5 p-6 backdrop-blur-xl shadow-lg">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-orange-500/20 text-orange-400">
            <svg
              className="h-6 w-6"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={2}
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M3.75 6A2.25 2.25 0 016 3.75h2.25A2.25 2.25 0 0110.5 6v2.25a2.25 2.25 0 01-2.25 2.25H6a2.25 2.25 0 01-2.25-2.25V6zM3.75 15.75A2.25 2.25 0 016 13.5h2.25a2.25 2.25 0 012.25 2.25V18a2.25 2.25 0 01-2.25 2.25H6A2.25 2.25 0 013.75 18v-2.25zM13.5 6a2.25 2.25 0 012.25-2.25H18A2.25 2.25 0 0120.25 6v2.25A2.25 2.25 0 0118 10.5h-2.25a2.25 2.25 0 01-2.25-2.25V6zM13.5 15.75a2.25 2.25 0 012.25-2.25H18a2.25 2.25 0 012.25 2.25V18A2.25 2.25 0 0118 20.25h-2.25A2.25 2.25 0 0113.5 18v-2.25z"
              />
            </svg>
          </div>
          <h3 className="mt-4 font-display text-lg font-bold text-white">Canonical Matching</h3>
          <p className="mt-2 text-xs leading-relaxed text-white/60">
            Whether a store writes &ldquo;Fresh Soyabean 5L&rdquo; or &ldquo;রূপচাঁদা ৫
            লিটার&rdquo;, our tiered confidence matcher groups them into one canonical bucket so you
            compare true equivalents.
          </p>
        </div>

        <div className="rounded-3xl border border-white/10 bg-gradient-to-b from-white/10 to-white/5 p-6 backdrop-blur-xl shadow-lg">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-500/20 text-emerald-400">
            <svg
              className="h-6 w-6"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={2}
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M2.25 18.75a60.07 60.07 0 0115.797 2.101c.727.198 1.453-.342 1.453-1.096V18.75M3.75 4.5v.75A.75.75 0 013 6H2.25m0 0v10.5m0-10.5h.75a.75.75 0 01.75.75v.75m0 0h16.5m0 0h.75a.75.75 0 01.75.75v10.5a.75.75 0 01-.75.75H3.75"
              />
            </svg>
          </div>
          <h3 className="mt-4 font-display text-lg font-bold text-white">
            Multi-Store Basket Split
          </h3>
          <p className="mt-2 text-xs leading-relaxed text-white/60">
            Add your whole grocery list. We calculate whether ordering everything from one store or
            splitting between two saves you more money after tiered delivery fees.
          </p>
        </div>

        <div className="rounded-3xl border border-white/10 bg-gradient-to-b from-white/10 to-white/5 p-6 backdrop-blur-xl shadow-lg">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-amber-500/20 text-amber-400">
            <svg
              className="h-6 w-6"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={2}
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M12 6v12m-3-2.818l.879.659c1.171.879 3.07.879 4.242 0 1.172-.879 1.172-2.303 0-3.182C13.536 12.219 12.768 12 12 12c-.725 0-1.45-.22-2.003-.659-1.106-.879-1.106-2.303 0-3.182s2.9-.879 4.006 0l.415.33M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </div>
          <h3 className="mt-4 font-display text-lg font-bold text-white">True Per-Unit Pricing</h3>
          <p className="mt-2 text-xs leading-relaxed text-white/60">
            See the exact price per litre or per kilogram across varying package sizes. Never get
            confused by irregular quantities.
          </p>
        </div>
      </section>
    </div>
  );
}
