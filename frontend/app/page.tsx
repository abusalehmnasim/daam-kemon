"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { SearchBar } from "@/components/SearchBar";
import { StoreBadge } from "@/components/StoreBadge";
import { add as addToBasket, addMultiple as addMultipleToBasket } from "@/lib/basketStore";

const SUGGESTIONS = [
  { emoji: "🛢️", label: "5L Soybean Oil", q: "5L soybean oil", tag: "Save up to ৳70" },
  { emoji: "🌾", label: "Miniket Rice 5kg", q: "miniket rice 5kg", tag: "Save up to ৳50" },
  { emoji: "🥚", label: "12 Eggs", q: "12 eggs", tag: "Save up to ৳17" },
  { emoji: "🧂", label: "Sugar 1kg", q: "sugar 1kg", tag: "Save up to ৳14" },
  { emoji: "🫘", label: "Masoor Dal 1kg", q: "masoor dal 1kg", tag: "Save up to ৳17" },
  { emoji: "🥩", label: "Beef 1kg", q: "beef 1kg", tag: "Fresh rates" },
];

const CATEGORIES = [
  {
    key: "cooking_oil",
    name: "Cooking Oil",
    bnName: "ভোজ্য তেল",
    desc: "Soybean, Mustard, Sunflower",
    color: "bg-amber-50 text-amber-800 border-amber-200/80 hover:border-amber-300",
    iconBg: "bg-amber-100 text-amber-700",
    icon: (
      <svg
        className="h-6 w-6"
        fill="none"
        viewBox="0 0 24 24"
        strokeWidth={1.8}
        stroke="currentColor"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0112 15a9.065 9.065 0 00-6.23-.693L5 14.5m14.8.8l1.402 1.402c1.232 1.232.65 3.318-1.067 3.611A48.309 48.309 0 0112 21c-2.773 0-5.491-.235-8.135-.687-1.718-.293-2.3-2.379-1.067-3.61L5 14.5"
        />
      </svg>
    ),
  },
  {
    key: "rice",
    name: "Rice & Grains",
    bnName: "চাল ও খাদ্যশস্য",
    desc: "Miniket, Nazirshail, Chinigura",
    color: "bg-emerald-50 text-emerald-800 border-emerald-200/80 hover:border-emerald-300",
    iconBg: "bg-emerald-100 text-emerald-700",
    icon: (
      <svg
        className="h-6 w-6"
        fill="none"
        viewBox="0 0 24 24"
        strokeWidth={1.8}
        stroke="currentColor"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M12 3v17.25m0 0c-1.472 0-2.882.265-4.185.75M12 20.25c1.472 0 2.882.265 4.185.75M18.75 4.97A48.416 48.416 0 0012 4.5c-2.291 0-4.545.16-6.75.47m13.5 0c1.01.143 2.01.317 3 .52m-16.5-.52c-.99.203-1.99.377-3 .52m16.5 4.72a48.557 48.557 0 00-13.5 0"
        />
      </svg>
    ),
  },
  {
    key: "dairy",
    name: "Dairy & Eggs",
    bnName: "দুধ ও ডিম",
    desc: "Fresh Milk, Powder, Farm Eggs",
    color: "bg-blue-50 text-blue-800 border-blue-200/80 hover:border-blue-300",
    iconBg: "bg-blue-100 text-blue-700",
    icon: (
      <svg
        className="h-6 w-6"
        fill="none"
        viewBox="0 0 24 24"
        strokeWidth={1.8}
        stroke="currentColor"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M12 9v6m3-3H9m12 0a9 9 0 11-18 0 9 9 0 0118 0z"
        />
      </svg>
    ),
  },
  {
    key: "lentils",
    name: "Dal & Pulses",
    bnName: "ডাল ও শস্য",
    desc: "Masoor, Moong, Chhola",
    color: "bg-orange-50 text-orange-800 border-orange-200/80 hover:border-orange-300",
    iconBg: "bg-orange-100 text-orange-700",
    icon: (
      <svg
        className="h-6 w-6"
        fill="none"
        viewBox="0 0 24 24"
        strokeWidth={1.8}
        stroke="currentColor"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M20.25 7.5l-.625 10.632a2.25 2.25 0 01-2.247 2.118H6.622a2.25 2.25 0 01-2.247-2.118L3.75 7.5M10 11.25h4M3.375 7.5h17.25c.621 0 1.125-.504 1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125H3.375c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125z"
        />
      </svg>
    ),
  },
  {
    key: "spices",
    name: "Spices & Salt",
    bnName: "মসলা ও লবণ",
    desc: "Turmeric, Chilli, Whole Spices",
    color: "bg-rose-50 text-rose-800 border-rose-200/80 hover:border-rose-300",
    iconBg: "bg-rose-100 text-rose-700",
    icon: (
      <svg
        className="h-6 w-6"
        fill="none"
        viewBox="0 0 24 24"
        strokeWidth={1.8}
        stroke="currentColor"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M15.362 5.214A8.252 8.252 0 0112 21 8.25 8.25 0 016.038 7.048 8.287 8.287 0 009 9.6a8.983 8.983 0 013.361-6.867 8.21 8.21 0 003 2.48z"
        />
      </svg>
    ),
  },
  {
    key: "beverages",
    name: "Tea & Snacks",
    bnName: "চা ও স্ন্যাকস",
    desc: "Black Tea, Biscuits, Noodles",
    color: "bg-purple-50 text-purple-800 border-purple-200/80 hover:border-purple-300",
    iconBg: "bg-purple-100 text-purple-700",
    icon: (
      <svg
        className="h-6 w-6"
        fill="none"
        viewBox="0 0 24 24"
        strokeWidth={1.8}
        stroke="currentColor"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5"
        />
      </svg>
    ),
  },
  {
    key: "flour",
    name: "Atta & Bakery",
    bnName: "আটা, ময়দা ও সুজি",
    desc: "Whole Wheat Atta, Maida",
    color: "bg-yellow-50 text-yellow-800 border-yellow-200/80 hover:border-yellow-300",
    iconBg: "bg-yellow-100 text-yellow-700",
    icon: (
      <svg
        className="h-6 w-6"
        fill="none"
        viewBox="0 0 24 24"
        strokeWidth={1.8}
        stroke="currentColor"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M3.75 6A2.25 2.25 0 016 3.75h2.25A2.25 2.25 0 0110.5 6v2.25a2.25 2.25 0 01-2.25 2.25H6a2.25 2.25 0 01-2.25-2.25V6z"
        />
      </svg>
    ),
  },
  {
    key: "cleaning",
    name: "Cleaning & Care",
    bnName: "টয়লেট্রিজ ও ক্লিনিং",
    desc: "Detergent, Handwash, Soap",
    color: "bg-cyan-50 text-cyan-800 border-cyan-200/80 hover:border-cyan-300",
    iconBg: "bg-cyan-100 text-cyan-700",
    icon: (
      <svg
        className="h-6 w-6"
        fill="none"
        viewBox="0 0 24 24"
        strokeWidth={1.8}
        stroke="currentColor"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z"
        />
      </svg>
    ),
  },
];

const TOP_DEALS = [
  {
    id: "deal-1",
    name: "5L Soybean Oil",
    bnSubtitle: "ফ্রেশ / তীর / রূপচাঁদা বোতল",
    query: "5L soybean oil",
    lowestPrice: 890,
    lowestStore: "shwapno",
    highestPrice: 960,
    highestStore: "chaldal",
    savings: 70,
  },
  {
    id: "deal-2",
    name: "Miniket Rice 5kg",
    bnSubtitle: "প্রিমিয়াম মিনিকেট চাল",
    query: "miniket rice 5kg",
    lowestPrice: 365,
    lowestStore: "chaldal",
    highestPrice: 415,
    highestStore: "unimart",
    savings: 50,
  },
  {
    id: "deal-3",
    name: "Dano Full Cream Milk 1kg",
    bnSubtitle: "ফুল ক্রিম মিল্ক পাউডার",
    query: "dano milk powder 1kg",
    lowestPrice: 885,
    lowestStore: "unimart",
    highestPrice: 960,
    highestStore: "shwapno",
    savings: 75,
  },
  {
    id: "deal-4",
    name: "Farm Fresh Brown Eggs (12 pcs)",
    bnSubtitle: "১২টি লাল ডিমের হালি প্যাক",
    query: "12 eggs",
    lowestPrice: 148,
    lowestStore: "shwapno",
    highestPrice: 165,
    highestStore: "agora",
    savings: 17,
  },
  {
    id: "deal-5",
    name: "Deshi Masoor Dal 1kg",
    bnSubtitle: "চিকন দেশি মসুর ডাল",
    query: "masoor dal 1kg",
    lowestPrice: 138,
    lowestStore: "agora",
    highestPrice: 155,
    highestStore: "chaldal",
    savings: 17,
  },
  {
    id: "deal-6",
    name: "Refined White Sugar 1kg",
    bnSubtitle: "সাদা পরিশোধিত চিনি",
    query: "sugar 1kg",
    lowestPrice: 134,
    lowestStore: "chaldal",
    highestPrice: 148,
    highestStore: "daraz",
    savings: 14,
  },
];

const BAZAAR_BUNDLES = [
  {
    id: "weekly",
    badge: "Most Popular",
    title: "সাপ্তাহিক নিত্যবাজার",
    subtitle: "Weekly Family Essentials",
    estTotal: 1675,
    estSavings: 145,
    items: [
      { label: "5L Soybean Oil", query: "5L soybean oil", quantity: 1 },
      { label: "Miniket Rice 5kg", query: "miniket rice 5kg", quantity: 1 },
      { label: "Masoor Dal 1kg", query: "masoor dal 1kg", quantity: 1 },
      { label: "12 Eggs", query: "12 eggs", quantity: 1 },
      { label: "Sugar 1kg", query: "sugar 1kg", quantity: 1 },
    ],
  },
  {
    id: "breakfast",
    badge: "Quick Combo",
    title: "সকালের নাস্তা কম্বো",
    subtitle: "Breakfast & Morning Chai",
    estTotal: 460,
    estSavings: 45,
    items: [
      { label: "12 Eggs", query: "12 eggs", quantity: 1 },
      { label: "Dano Milk Powder 500g", query: "dano milk 500g", quantity: 1 },
      { label: "Sugar 1kg", query: "sugar 1kg", quantity: 1 },
    ],
  },
  {
    id: "bachelor",
    badge: "Fast Cart",
    title: "ব্যাচেলর স্পেশাল",
    subtitle: "Student & Bachelor Weekly",
    estTotal: 620,
    estSavings: 60,
    items: [
      { label: "Soybean Oil 1L", query: "soybean oil 1L", quantity: 1 },
      { label: "12 Eggs", query: "12 eggs", quantity: 1 },
      { label: "Masoor Dal 1kg", query: "masoor dal 1kg", quantity: 1 },
      { label: "Instant Noodles", query: "maggi noodles", quantity: 1 },
    ],
  },
];

const STORES = [
  {
    name: "chaldal",
    displayName: "Chaldal",
    fee: "৳19 - ৳39",
    speed: "1-2 hour delivery",
    coverage: "Dhaka, Ctg, Jashore",
  },
  {
    name: "shwapno",
    displayName: "Shwapno",
    fee: "৳30",
    speed: "Same day express",
    coverage: "Nationwide retail",
  },
  {
    name: "unimart",
    displayName: "Unimart",
    fee: "৳50",
    speed: "Premium superstore",
    coverage: "Gulshan, Dhanmondi, Uttara",
  },
  {
    name: "agora",
    displayName: "Agora",
    fee: "৳40",
    speed: "Same day slot",
    coverage: "Major Dhaka hubs",
  },
  {
    name: "daraz",
    displayName: "Daraz Mart",
    fee: "৳35 - ৳50",
    speed: "Next day standard",
    coverage: "64 districts",
  },
  {
    name: "othoba",
    displayName: "Othoba",
    fee: "৳35",
    speed: "Pran-RFL network",
    coverage: "Nationwide delivery",
  },
];

export default function HomePage() {
  const router = useRouter();
  const [addedDeal, setAddedDeal] = useState<string | null>(null);
  const [addingBundle, setAddingBundle] = useState<string | null>(null);

  const handleAddDeal = (deal: (typeof TOP_DEALS)[number]) => {
    addToBasket({
      query: deal.query,
      label: deal.name,
      quantity: 1,
    });
    setAddedDeal(deal.id);
    setTimeout(() => setAddedDeal(null), 1500);
  };

  const handleAddBundle = (bundle: (typeof BAZAAR_BUNDLES)[number]) => {
    setAddingBundle(bundle.id);
    addMultipleToBasket(
      bundle.items.map((it) => ({
        query: it.query,
        label: it.label,
        quantity: it.quantity,
      }))
    );
    setTimeout(() => {
      setAddingBundle(null);
      router.push("/basket");
    }, 400);
  };

  return (
    <div className="space-y-12">
      {/* 1. HERO SECTION */}
      <section className="relative overflow-hidden rounded-3xl border border-line bg-gradient-to-b from-card via-card to-paper/60 p-6 shadow-sm sm:p-10">
        <div className="mx-auto max-w-2xl text-center">
          <div className="inline-flex items-center gap-2 rounded-full border border-save/30 bg-save-weak px-3 py-1 text-xs font-bold text-save-dark shadow-xs">
            <span className="h-2 w-2 rounded-full bg-save animate-pulse" />
            <span>প্রতিদিন ৬টি সুপারশপের লাইভ বাজার দর তুলনা</span>
          </div>

          <h1 className="mt-4 text-3xl font-extrabold tracking-tight text-ink sm:text-4xl">
            Compare Grocery Prices.
            <span className="mt-1 block font-display text-brand">
              Save up to 30% on your daily bazaar.
            </span>
          </h1>

          <p className="mt-3 text-sm leading-relaxed text-muted sm:text-base">
            One search across{" "}
            <strong className="text-ink">Chaldal, Shwapno, Unimart, Agora, Daraz & Othoba</strong>.
            We match equivalent items across stores and group them by volume so you always see the
            real cheapest price.
          </p>

          <div className="mt-6">
            <SearchBar autoFocus />
          </div>

          {/* Quick Trending Tags */}
          <div className="mt-4 flex flex-wrap items-center justify-center gap-2">
            <span className="text-xs font-medium text-faint">জনপ্রিয় সার্চ:</span>
            {SUGGESTIONS.map((s) => (
              <Link
                key={s.q}
                href={`/search?q=${encodeURIComponent(s.q)}`}
                className="group inline-flex items-center gap-1.5 rounded-full border border-line bg-card px-3 py-1 text-xs font-medium text-muted transition-all hover:border-brand/40 hover:text-brand hover:shadow-xs"
              >
                <span>{s.emoji}</span>
                <span>{s.label}</span>
                {s.tag && (
                  <span className="hidden rounded bg-save-weak px-1 text-[10px] font-bold text-save-dark sm:inline-block">
                    {s.tag}
                  </span>
                )}
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* 2. VISUAL CATEGORIES GRID (Foodpanda / Blinkit Style) */}
      <section className="space-y-4">
        <div className="flex items-end justify-between">
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-xl font-bold tracking-tight text-ink sm:text-2xl">
                Browse by Category
              </h2>
              <span className="rounded-full bg-brand/10 px-2 py-0.5 text-xs font-semibold text-brand">
                ক্যাটাগরি
              </span>
            </div>
            <p className="mt-0.5 text-xs text-muted sm:text-sm">
              Explore essential grocery buckets with store-by-store breakdowns.
            </p>
          </div>
          <Link
            href="/categories"
            className="text-xs font-bold text-brand hover:underline sm:text-sm"
          >
            All Categories →
          </Link>
        </div>

        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          {CATEGORIES.map((cat) => (
            <Link
              key={cat.key}
              href={`/search?category=${encodeURIComponent(cat.key)}`}
              className={`group flex flex-col justify-between rounded-2xl border p-4 transition-all hover:-translate-y-0.5 hover:shadow-md ${cat.color}`}
            >
              <div className="flex items-start justify-between">
                <div
                  className={`flex h-11 w-11 items-center justify-center rounded-xl shadow-xs transition-transform group-hover:scale-110 ${cat.iconBg}`}
                >
                  {cat.icon}
                </div>
                <span className="text-xs font-semibold text-faint group-hover:text-ink">→</span>
              </div>
              <div className="mt-3">
                <h3 className="font-bold text-ink leading-tight group-hover:text-brand">
                  {cat.name}
                </h3>
                <p className="text-xs font-medium opacity-80">{cat.bnName}</p>
                <p className="mt-1 line-clamp-1 text-[11px] text-muted">{cat.desc}</p>
              </div>
            </Link>
          ))}
        </div>
      </section>

      {/* 3. TOP PRICE DROPS & DISCREPANCIES (The Dopamine Rail) */}
      <section id="deals" className="space-y-4">
        <div className="flex items-end justify-between">
          <div>
            <div className="flex items-center gap-2">
              <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-save-weak text-save">
                <svg
                  className="h-4 w-4"
                  fill="none"
                  viewBox="0 0 24 24"
                  strokeWidth={2.5}
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M15.362 5.214A8.252 8.252 0 0112 21 8.25 8.25 0 016.038 7.048 8.287 8.287 0 009 9.6a8.983 8.983 0 013.361-6.867 8.21 8.21 0 003 2.48z"
                  />
                </svg>
              </span>
              <h2 className="text-xl font-bold tracking-tight text-ink sm:text-2xl">
                Today&apos;s Biggest Price Gaps
              </h2>
              <span className="rounded-full bg-save px-2 py-0.5 text-xs font-bold text-white shadow-xs">
                আজকের সেরা সাশ্রয়
              </span>
            </div>
            <p className="mt-0.5 text-xs text-muted sm:text-sm">
              Same item, different stores. Buy from the cheapest store and pocket the difference.
            </p>
          </div>
        </div>

        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {TOP_DEALS.map((deal) => (
            <div
              key={deal.id}
              className="flex flex-col justify-between rounded-2xl border border-line bg-card p-4 shadow-xs transition-shadow hover:shadow-md"
            >
              <div>
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <h3 className="font-bold text-ink leading-tight">{deal.name}</h3>
                    <p className="text-xs text-muted">{deal.bnSubtitle}</p>
                  </div>
                  <span className="shrink-0 rounded-full bg-save-weak px-2 py-0.5 text-xs font-extrabold text-save-dark ring-1 ring-save/30">
                    ৳{deal.savings} সাশ্রয়
                  </span>
                </div>

                <div className="mt-4 flex items-center justify-between rounded-xl bg-paper/60 p-2.5">
                  <div>
                    <div className="text-[10px] font-semibold uppercase text-save">Cheapest at</div>
                    <div className="mt-0.5">
                      <StoreBadge storeName={deal.lowestStore} size="sm" />
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-lg font-black text-save leading-none">
                      ৳{deal.lowestPrice}
                    </div>
                    <div className="text-[11px] text-faint line-through">
                      ৳{deal.highestPrice} elsewhere
                    </div>
                  </div>
                </div>
              </div>

              <div className="mt-4 flex items-center justify-between gap-2 pt-2 border-t border-line/60">
                <Link
                  href={`/search?q=${encodeURIComponent(deal.query)}`}
                  className="text-xs font-semibold text-muted hover:text-brand"
                >
                  Compare all stores →
                </Link>

                <button
                  onClick={() => handleAddDeal(deal)}
                  className={`h-8 rounded-lg px-3 text-xs font-bold transition-all active:scale-95 ${
                    addedDeal === deal.id
                      ? "bg-save text-white shadow-xs"
                      : "border border-line bg-card text-ink hover:border-brand hover:bg-brand/5 hover:text-brand"
                  }`}
                >
                  {addedDeal === deal.id ? "Added ✓" : "+ Add to Basket"}
                </button>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* 4. READY BAZAAR BUNDLES (1-Click Basket Funnel) */}
      <section className="space-y-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-brand/10 text-brand">
              <svg
                className="h-4 w-4"
                fill="none"
                viewBox="0 0 24 24"
                strokeWidth={2.5}
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M15.75 10.5V6a3.75 3.75 0 10-7.5 0v4.5m11.356-1.993l1.263 12c.07.665-.45 1.243-1.119 1.243H4.25a1.125 1.125 0 01-1.12-1.243l1.264-12A1.125 1.125 0 015.513 7.5h12.974c.576 0 1.059.435 1.119 1.007zM8.625 10.5a.375.375 0 11-.75 0 .375.375 0 01.75 0zm7.5 0a.375.375 0 11-.75 0 .375.375 0 01.75 0z"
                />
              </svg>
            </span>
            <h2 className="text-xl font-bold tracking-tight text-ink sm:text-2xl">
              1-Click Bazaar Bundles
            </h2>
            <span className="rounded-full bg-brand/10 px-2 py-0.5 text-xs font-bold text-brand">
              রেডি বাজার প্যাক
            </span>
          </div>
          <p className="mt-0.5 text-xs text-muted sm:text-sm">
            Load an entire grocery list with 1 tap. Our Basket Optimizer finds the cheapest
            combination across all stores.
          </p>
        </div>

        <div className="grid gap-4 sm:grid-cols-3">
          {BAZAAR_BUNDLES.map((b) => (
            <div
              key={b.id}
              className="flex flex-col justify-between rounded-2xl border border-line bg-card p-5 shadow-xs transition-shadow hover:shadow-md"
            >
              <div>
                <div className="flex items-center justify-between">
                  <span className="rounded-full bg-line/60 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-muted">
                    {b.badge}
                  </span>
                  <span className="rounded-full bg-save-weak px-2 py-0.5 text-[11px] font-bold text-save-dark">
                    বাঁচবে ৳{b.estSavings}+
                  </span>
                </div>

                <h3 className="mt-3 text-lg font-bold text-ink">{b.title}</h3>
                <p className="text-xs text-muted">{b.subtitle}</p>

                <ul className="mt-3 space-y-1.5 border-t border-line/60 pt-3 text-xs text-ink/80">
                  {b.items.map((it) => (
                    <li key={it.query} className="flex items-center gap-1.5">
                      <span className="text-save">✓</span>
                      <span>{it.label}</span>
                    </li>
                  ))}
                </ul>
              </div>

              <div className="mt-5 border-t border-line/60 pt-3">
                <div className="mb-3 flex items-baseline justify-between text-xs">
                  <span className="text-muted">Est. Total:</span>
                  <span className="text-base font-extrabold text-ink">৳{b.estTotal}</span>
                </div>

                <button
                  onClick={() => handleAddBundle(b)}
                  disabled={addingBundle === b.id}
                  className="flex w-full items-center justify-center gap-1.5 rounded-xl bg-brand py-2.5 text-xs font-bold text-white shadow-sm transition-all hover:bg-brand-dark active:scale-95 disabled:opacity-50"
                >
                  <span>
                    {addingBundle === b.id ? "Adding to Cart…" : "+ Add Bundle & Optimize"}
                  </span>
                  <span aria-hidden="true">→</span>
                </button>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* 5. TRACKED SUPERMARKETS & DELIVERY TIER GUIDE */}
      <section className="rounded-2xl border border-line bg-card p-6 shadow-xs">
        <div className="flex flex-col justify-between gap-2 sm:flex-row sm:items-center">
          <div>
            <h2 className="text-lg font-bold text-ink sm:text-xl">
              Tracked Supermarkets & Delivery Info
            </h2>
            <p className="text-xs text-muted">
              Live automated scrapes from Bangladesh&apos;s leading online and retail grocers.
            </p>
          </div>
          <div className="flex items-center gap-2 text-xs font-medium text-save-dark">
            <span className="h-2 w-2 rounded-full bg-save" />
            <span>Updated today at 01:00 UTC</span>
          </div>
        </div>

        <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
          {STORES.map((st) => (
            <div
              key={st.name}
              className="flex flex-col justify-between rounded-xl border border-line/80 bg-paper/40 p-3 text-xs"
            >
              <div>
                <StoreBadge storeName={st.name} displayName={st.displayName} size="sm" />
                <div className="mt-2 font-bold text-ink">{st.fee}</div>
                <div className="text-[11px] text-faint">delivery fee</div>
              </div>
              <div className="mt-2 border-t border-line/60 pt-1.5 text-[10px] text-muted">
                {st.speed}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* 6. WHY DAAM KEMON (Value Props) */}
      <section className="grid gap-4 sm:grid-cols-3">
        <div className="rounded-2xl border border-line bg-card p-5">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand/10 text-brand">
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
                d="M3.75 6A2.25 2.25 0 016 3.75h2.25A2.25 2.25 0 0110.5 6v2.25a2.25 2.25 0 01-2.25 2.25H6a2.25 2.25 0 01-2.25-2.25V6zM3.75 15.75A2.25 2.25 0 016 13.5h2.25a2.25 2.25 0 012.25 2.25V18a2.25 2.25 0 01-2.25 2.25H6A2.25 2.25 0 013.75 18v-2.25zM13.5 6a2.25 2.25 0 012.25-2.25H18A2.25 2.25 0 0120.25 6v2.25A2.25 2.25 0 0118 10.5h-2.25a2.25 2.25 0 01-2.25-2.25V6zM13.5 15.75a2.25 2.25 0 012.25-2.25H18a2.25 2.25 0 012.25 2.25V18A2.25 2.25 0 0118 20.25h-2.25A2.25 2.25 0 0113.5 18v-2.25z"
              />
            </svg>
          </div>
          <h3 className="mt-3 text-sm font-bold text-ink">Matched Across Messy Listings</h3>
          <p className="mt-1 text-xs leading-relaxed text-muted">
            Whether a store writes &ldquo;Fresh Soyabean 5L&rdquo; or &ldquo;রূপচাঁদা ৫
            লিটার&rdquo;, we normalize them into one canonical bucket so you compare true
            equivalents.
          </p>
        </div>

        <div className="rounded-2xl border border-line bg-card p-5">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-save-weak text-save">
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
                d="M2.25 18.75a60.07 60.07 0 0115.797 2.101c.727.198 1.453-.342 1.453-1.096V18.75M3.75 4.5v.75A.75.75 0 013 6H2.25m0 0v10.5m0-10.5h.75a.75.75 0 01.75.75v.75m0 0h16.5m0 0h.75a.75.75 0 01.75.75v10.5a.75.75 0 01-.75.75H3.75"
              />
            </svg>
          </div>
          <h3 className="mt-3 text-sm font-bold text-ink">Smart Basket Optimizer</h3>
          <p className="mt-1 text-xs leading-relaxed text-muted">
            Add your whole grocery list. We calculate whether ordering everything from one store or
            splitting between two saves you more money after delivery fees.
          </p>
        </div>

        <div className="rounded-2xl border border-line bg-card p-5">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-50 text-blue-700">
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
                d="M12 6v12m-3-2.818l.879.659c1.171.879 3.07.879 4.242 0 1.172-.879 1.172-2.303 0-3.182C13.536 12.219 12.768 12 12 12c-.725 0-1.45-.22-2.003-.659-1.106-.879-1.106-2.303 0-3.182s2.9-.879 4.006 0l.415.33M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </div>
          <h3 className="mt-3 text-sm font-bold text-ink">True Per-Unit Comparison</h3>
          <p className="mt-1 text-xs leading-relaxed text-muted">
            See the exact price per litre or per kilogram across different pack sizes. Never get
            confused by varying quantities.
          </p>
        </div>
      </section>
    </div>
  );
}
