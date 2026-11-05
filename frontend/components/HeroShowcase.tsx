"use client";

import Link from "next/link";
import { useState } from "react";
import { StoreBadge } from "@/components/StoreBadge";
import { add as addToBasket } from "@/lib/basketStore";
import { useBasket } from "@/lib/useBasket";

interface ProductShowcase {
  id: string;
  name: string;
  bnSubtitle: string;
  category: string;
  headline: string;
  subheadline: string;
  desc: string;
  tagline: string;
  query: string;
  image: string;
  sizes: {
    label: string;
    lowestPrice: number;
    lowestStore: string;
    highestPrice: number;
    highestStore: string;
    savings: number;
  }[];
}

const SHOWCASE_PRODUCTS: ProductShowcase[] = [
  {
    id: "oil",
    name: "Pure Soybean Oil",
    bnSubtitle: "তীর / রূপচাঁদা / ফ্রেশ ৫ লিটার বোতল",
    category: "COOKING OIL",
    headline: "Bazaar intelligence.\nWithout trying.",
    subheadline: "বাজারের আসল দর · কোনো লুকোচুরি ছাড়া",
    desc: "It's not just about shopping. It's about knowing the exact price of every litre and kilo across 6 supermarkets before stepping outside. One canonical catalog. Sorted cheapest first.",
    tagline: "Confidence, wrapped in savings.",
    query: "5L soybean oil",
    image: "/products/oil_5l.jpg",
    sizes: [
      {
        label: "1L",
        lowestPrice: 190,
        lowestStore: "shwapno",
        highestPrice: 205,
        highestStore: "chaldal",
        savings: 15,
      },
      {
        label: "2L",
        lowestPrice: 375,
        lowestStore: "shwapno",
        highestPrice: 410,
        highestStore: "unimart",
        savings: 35,
      },
      {
        label: "5L",
        lowestPrice: 890,
        lowestStore: "shwapno",
        highestPrice: 960,
        highestStore: "chaldal",
        savings: 70,
      },
    ],
  },
  {
    id: "rice",
    name: "Premium Miniket Rice",
    bnSubtitle: "মিনিকেট চাল প্রিমিয়াম পলিশ",
    category: "RICE & GRAINS",
    headline: "Pure grain quality.\nHonest weights.",
    subheadline: "প্রতি কেজিতে সাশ্রয় · নিখুঁত বাজার দর",
    desc: "Long grain, finely sorted Miniket rice. Filter by pack size and see who delivers cheapest to your door without carrying heavy sacks from the bazaar.",
    tagline: "Purity, weighed in accuracy.",
    query: "miniket rice 5kg",
    image: "/products/rice_5kg.jpg",
    sizes: [
      {
        label: "1kg",
        lowestPrice: 75,
        lowestStore: "chaldal",
        highestPrice: 85,
        highestStore: "unimart",
        savings: 10,
      },
      {
        label: "5kg",
        lowestPrice: 365,
        lowestStore: "chaldal",
        highestPrice: 415,
        highestStore: "unimart",
        savings: 50,
      },
      {
        label: "25kg",
        lowestPrice: 1780,
        lowestStore: "agora",
        highestPrice: 1980,
        highestStore: "shwapno",
        savings: 200,
      },
    ],
  },
  {
    id: "eggs",
    name: "Farm Fresh Brown Eggs",
    bnSubtitle: "১২টি লাল ডিমের হালি প্যাক",
    category: "DAIRY & EGGS",
    headline: "Fresh mornings.\nFair daily rates.",
    subheadline: "প্রতি ডিমে সঠিক হিসাব · কোনো বাড়তি দর নয়",
    desc: "Daily fresh eggs compared across 6 supermarkets. Transparent per-egg rate calculation so you never overpay for your morning breakfast.",
    tagline: "Freshness, delivered every sunrise.",
    query: "12 eggs",
    image: "/products/eggs_12.jpg",
    sizes: [
      {
        label: "4 pcs",
        lowestPrice: 50,
        lowestStore: "shwapno",
        highestPrice: 56,
        highestStore: "agora",
        savings: 6,
      },
      {
        label: "12 pcs",
        lowestPrice: 148,
        lowestStore: "shwapno",
        highestPrice: 165,
        highestStore: "agora",
        savings: 17,
      },
      {
        label: "30 pcs",
        lowestPrice: 365,
        lowestStore: "chaldal",
        highestPrice: 410,
        highestStore: "unimart",
        savings: 45,
      },
    ],
  },
  {
    id: "milk",
    name: "Pure Dairy Milk Powder",
    bnSubtitle: "ফুল ক্রিম মিল্ক পাউডার ১ কেজি টিন",
    category: "DAIRY POWDER",
    headline: "Imported quality.\nDomestic savings.",
    subheadline: "আসল ডেইরি টেস্ট · সর্বনিম্ন অফার মূল্য",
    desc: "Full cream dairy powder. Compare bulk tin versus refill packs across all supermarkets with verified brand authenticity.",
    tagline: "Rich taste, weighed in purity.",
    query: "dano milk powder 1kg",
    image: "/products/milk_1kg.jpg",
    sizes: [
      {
        label: "400g",
        lowestPrice: 360,
        lowestStore: "unimart",
        highestPrice: 395,
        highestStore: "shwapno",
        savings: 35,
      },
      {
        label: "500g",
        lowestPrice: 445,
        lowestStore: "unimart",
        highestPrice: 485,
        highestStore: "chaldal",
        savings: 40,
      },
      {
        label: "1kg",
        lowestPrice: 885,
        lowestStore: "unimart",
        highestPrice: 960,
        highestStore: "shwapno",
        savings: 75,
      },
    ],
  },
];

export function HeroShowcase() {
  const [productIdx, setProductIdx] = useState(0);
  const [sizeIdx, setSizeIdx] = useState(2); // Default to largest/popular pack
  const [added, setAdded] = useState(false);
  const { totalCount } = useBasket();

  const product = SHOWCASE_PRODUCTS[productIdx];
  const size = product.sizes[sizeIdx] || product.sizes[0];

  const handleNext = () => {
    setProductIdx((prev) => (prev + 1) % SHOWCASE_PRODUCTS.length);
    setSizeIdx(SHOWCASE_PRODUCTS[(productIdx + 1) % SHOWCASE_PRODUCTS.length].sizes.length - 1);
  };

  const handlePrev = () => {
    setProductIdx((prev) => (prev - 1 + SHOWCASE_PRODUCTS.length) % SHOWCASE_PRODUCTS.length);
    setSizeIdx(
      SHOWCASE_PRODUCTS[(productIdx - 1 + SHOWCASE_PRODUCTS.length) % SHOWCASE_PRODUCTS.length]
        .sizes.length - 1
    );
  };

  const handleAdd = () => {
    addToBasket({
      query: `${product.name} ${size.label}`,
      label: `${product.name} (${size.label})`,
      quantity: 1,
    });
    setAdded(true);
    setTimeout(() => setAdded(false), 1500);
  };

  return (
    <div className="relative">
      {/* Radiant ambient glow in background (from Pinterest reference) */}
      <div className="pointer-events-none absolute -top-24 left-1/2 h-80 w-full max-w-4xl -translate-x-1/2 rounded-full bg-gradient-to-b from-[#EA580C]/25 via-[#CF4E2B]/15 to-transparent blur-[120px]" />

      {/* Main Luxury Canvas Card */}
      <section className="relative overflow-hidden rounded-[32px] border border-white/15 bg-gradient-to-b from-[#2B1B15]/95 via-[#1E120D]/98 to-[#120B08] p-6 text-white shadow-[0_30px_100px_rgba(0,0,0,0.7)] backdrop-blur-2xl sm:rounded-[44px] sm:p-10 lg:p-12">
        {/* Ambient inner radial lighting spotlight */}
        <div className="pointer-events-none absolute left-1/2 top-1/2 h-[500px] w-[500px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-radial-glow from-[#E8623D]/15 via-amber-600/5 to-transparent blur-3xl" />

        {/* Top Header Row within Canvas */}
        <div className="relative z-10 flex flex-col items-center justify-between gap-4 border-b border-white/10 pb-6 sm:flex-row">
          {/* Logo / Monogram */}
          <Link href="/" className="group flex items-center gap-2.5">
            <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-white font-display text-sm font-black text-black shadow-md transition-transform group-hover:scale-105">
              DK
            </span>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-display text-base font-extrabold tracking-tight text-white">
                  DAAM KEMON
                </span>
                <span className="rounded-full bg-white/10 px-2 py-0.5 text-[10px] font-bold text-orange-300">
                  দাম কেমন
                </span>
              </div>
            </div>
          </Link>

          {/* Floating Frosted Pill Navigation (Pinterest style) */}
          <div className="flex flex-wrap items-center justify-center rounded-full border border-white/10 bg-black/40 p-1 backdrop-blur-xl shadow-inner">
            {SHOWCASE_PRODUCTS.map((p, idx) => (
              <button
                key={p.id}
                onClick={() => {
                  setProductIdx(idx);
                  setSizeIdx(p.sizes.length - 1);
                }}
                className={`rounded-full px-4 py-1.5 text-xs font-bold transition-all ${
                  productIdx === idx
                    ? "bg-white text-black shadow-md"
                    : "text-white/60 hover:text-white"
                }`}
              >
                {p.category}
              </button>
            ))}
            <Link
              href="/categories"
              className="rounded-full px-3.5 py-1.5 text-xs font-semibold text-white/50 transition-colors hover:text-white"
            >
              ALL BAZAAR
            </Link>
          </div>

          {/* Basket Trigger Pill on Top Right */}
          <Link
            href="/basket"
            className="flex items-center gap-2 rounded-full border border-white/15 bg-white/5 px-4 py-1.5 text-xs font-bold text-white transition-all hover:bg-white/15 active:scale-95"
          >
            <span>🧺 Basket</span>
            {totalCount > 0 && (
              <span className="flex h-5 min-w-[20px] items-center justify-center rounded-full bg-save px-1.5 text-[10px] font-black text-white shadow-xs">
                {totalCount}
              </span>
            )}
          </Link>
        </div>

        {/* 3-Column Hero Grid (Replicating Pinterest Puffer Jacket Showcase) */}
        <div className="relative z-10 mt-8 grid grid-cols-1 items-center gap-8 lg:grid-cols-12 lg:gap-6">
          {/* LEFT COLUMN: Controls & Bold Editorial Headline (4 cols) */}
          <div className="space-y-5 lg:col-span-5">
            {/* Stepper Controls < > */}
            <div className="flex items-center gap-2">
              <button
                onClick={handlePrev}
                aria-label="Previous product"
                className="flex h-9 w-9 items-center justify-center rounded-full border border-white/15 bg-white/10 text-white shadow-sm transition-all hover:bg-white/20 active:scale-90"
              >
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
                    d="M15.75 19.5L8.25 12l7.5-7.5"
                  />
                </svg>
              </button>
              <button
                onClick={handleNext}
                aria-label="Next product"
                className="flex h-9 w-9 items-center justify-center rounded-full border border-white/15 bg-white/10 text-white shadow-sm transition-all hover:bg-white/20 active:scale-90"
              >
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
                    d="M8.25 4.5l7.5 7.5-7.5 7.5"
                  />
                </svg>
              </button>
              <span className="ml-2 text-xs font-semibold uppercase tracking-wider text-white/40">
                {productIdx + 1} / {SHOWCASE_PRODUCTS.length}
              </span>
            </div>

            {/* Headline */}
            <div>
              <p className="text-xs font-bold uppercase tracking-widest text-orange-400">
                {product.subheadline}
              </p>
              <h1 className="mt-2 font-display text-3xl font-black leading-[1.08] tracking-tight text-white sm:text-5xl">
                {product.headline.split("\n")[0]} <br />
                <span className="bg-gradient-to-r from-orange-400 via-amber-300 to-yellow-200 bg-clip-text text-transparent">
                  {product.headline.split("\n")[1]}
                </span>
              </h1>
            </div>

            {/* Editorial Body */}
            <p className="text-xs leading-relaxed text-white/70 sm:text-sm">{product.desc}</p>

            {/* White Pill Action Button (From Pinterest Pin) */}
            <div className="pt-2">
              <Link
                href={`/search?q=${encodeURIComponent(product.query)}`}
                className="inline-flex items-center gap-2 rounded-full bg-white px-7 py-3.5 text-xs font-black text-black shadow-xl transition-all hover:bg-orange-100 hover:scale-105 active:scale-95"
              >
                <span>Compare all stores</span>
                <span className="text-base leading-none">›</span>
              </Link>
            </div>

            {/* Micro Ticker */}
            <div className="flex items-center gap-2 pt-4 text-[11px] font-medium text-white/50 border-t border-white/10">
              <span className="h-2 w-2 rounded-full bg-save animate-pulse" />
              <span>Shwapno · Chaldal · Unimart · Agora · Daraz · Othoba</span>
            </div>
          </div>

          {/* CENTER COLUMN: Floating 3D Product Showcase (4 cols) */}
          <div className="relative flex flex-col items-center justify-center py-4 lg:col-span-4">
            <div className="group relative transition-transform duration-500 hover:scale-105">
              {/* Floating Product Image */}
              <div className="relative h-64 w-64 sm:h-80 sm:w-80">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={product.image}
                  alt={product.name}
                  width={320}
                  height={320}
                  className="h-full w-full object-contain filter drop-shadow-[0_20px_35px_rgba(0,0,0,0.8)]"
                />
              </div>

              {/* Realistic Ground Shadow (From Pinterest Pin) */}
              <div className="mx-auto -mt-2 h-6 w-44 rounded-full bg-black/70 blur-md" />
            </div>

            {/* Tagline Beneath Spotlight */}
            <p className="mt-4 text-center font-display text-xs font-medium italic tracking-wide text-white/60">
              {product.tagline}
            </p>
          </div>

          {/* RIGHT COLUMN: Pricing & Interactive Pack Size Selector (3 cols) */}
          <div className="flex flex-col justify-between space-y-6 lg:col-span-3 lg:border-l lg:border-white/10 lg:pl-6">
            <div>
              {/* Big Bold Price Display */}
              <div className="flex items-baseline gap-3">
                <span className="tnum text-4xl font-black tracking-tight text-white sm:text-5xl">
                  ৳{size.lowestPrice}
                </span>
                <span className="tnum text-lg font-semibold text-white/40 line-through">
                  ৳{size.highestPrice}
                </span>
              </div>

              {/* Savings Badge */}
              <div className="mt-2">
                <span className="inline-flex items-center gap-1 rounded-full bg-save px-3 py-1 text-xs font-extrabold text-white shadow-sm">
                  <span>৳{size.savings} সাশ্রয়</span>
                  <span className="opacity-80">· Lowest at</span>
                  <span className="capitalize">{size.lowestStore}</span>
                </span>
              </div>

              {/* Size Selector (Replicating 'Choose your size: 36 38 40' from Pinterest Pin) */}
              <div className="mt-8">
                <p className="text-[11px] font-bold uppercase tracking-wider text-white/50">
                  Choose pack size:
                </p>
                <div className="mt-2.5 flex items-center gap-2">
                  {product.sizes.map((s, idx) => (
                    <button
                      key={s.label}
                      onClick={() => setSizeIdx(idx)}
                      className={`h-11 min-w-[44px] rounded-full px-3 text-xs font-extrabold transition-all active:scale-90 ${
                        sizeIdx === idx
                          ? "bg-white text-black shadow-lg scale-105"
                          : "border border-white/20 bg-white/10 text-white hover:bg-white/20"
                      }`}
                    >
                      {s.label}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Floating Mini-Card in Corner (Pinterest style) */}
            <div className="rounded-2xl border border-white/15 bg-white/10 p-4 backdrop-blur-xl shadow-lg">
              <div className="flex items-center justify-between text-xs">
                <span className="text-white/60">Best Store Option</span>
                <StoreBadge storeName={size.lowestStore} size="sm" />
              </div>

              <div className="mt-2 text-xs text-white/80">
                <span>Vs {size.highestStore.toUpperCase()}: </span>
                <span className="tnum font-bold text-white line-through">৳{size.highestPrice}</span>
              </div>

              <button
                onClick={handleAdd}
                className={`mt-3 flex w-full items-center justify-center gap-1.5 rounded-xl py-2.5 text-xs font-extrabold transition-all active:scale-95 ${
                  added
                    ? "bg-save text-white shadow-md"
                    : "bg-white/20 text-white hover:bg-white hover:text-black shadow-sm"
                }`}
              >
                <span>{added ? "Added to Basket ✓" : "+ Add to Basket"}</span>
              </button>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
