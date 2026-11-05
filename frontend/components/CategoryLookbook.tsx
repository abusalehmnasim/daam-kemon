"use client";

import Link from "next/link";

const CATEGORIES = [
  {
    key: "cooking_oil",
    name: "Cooking Oil",
    bnName: "ভোজ্য তেল",
    desc: "Soybean, Mustard, Sunflower, Olive oil",
    gradient: "from-amber-900/30 via-orange-950/20 to-transparent",
    border: "border-amber-500/20 hover:border-amber-500/50",
    badgeColor: "text-amber-400 bg-amber-500/10",
  },
  {
    key: "rice",
    name: "Rice & Grains",
    bnName: "চাল ও খাদ্যশস্য",
    desc: "Miniket, Nazirshail, Chinigura, Basmati",
    gradient: "from-emerald-900/30 via-emerald-950/20 to-transparent",
    border: "border-emerald-500/20 hover:border-emerald-500/50",
    badgeColor: "text-emerald-400 bg-emerald-500/10",
  },
  {
    key: "dairy",
    name: "Dairy & Eggs",
    bnName: "দুধ ও ডিম",
    desc: "Fresh Liquid Milk, Powder Milk, Eggs",
    gradient: "from-blue-900/30 via-blue-950/20 to-transparent",
    border: "border-blue-500/20 hover:border-blue-500/50",
    badgeColor: "text-blue-400 bg-blue-500/10",
  },
  {
    key: "lentils",
    name: "Dal & Pulses",
    bnName: "ডাল ও শস্য",
    desc: "Masoor, Moong, Chhola, Booter dal",
    gradient: "from-orange-900/30 via-orange-950/20 to-transparent",
    border: "border-orange-500/20 hover:border-orange-500/50",
    badgeColor: "text-orange-400 bg-orange-500/10",
  },
  {
    key: "spices",
    name: "Spices & Seasoning",
    bnName: "মসলা ও লবণ",
    desc: "Turmeric, Chilli, Whole spices, Salt",
    gradient: "from-rose-900/30 via-rose-950/20 to-transparent",
    border: "border-rose-500/20 hover:border-rose-500/50",
    badgeColor: "text-rose-400 bg-rose-500/10",
  },
  {
    key: "beverages",
    name: "Tea & Snacks",
    bnName: "চা ও স্ন্যাকস",
    desc: "Black tea, Biscuits, Noodles, Toast",
    gradient: "from-purple-900/30 via-purple-950/20 to-transparent",
    border: "border-purple-500/20 hover:border-purple-500/50",
    badgeColor: "text-purple-400 bg-purple-500/10",
  },
];

export function CategoryLookbook() {
  return (
    <section className="space-y-5">
      <div className="flex items-end justify-between">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-extrabold tracking-tight text-white sm:text-2xl">
              Curated Category Lookbook
            </h2>
            <span className="rounded-full bg-white/10 px-2.5 py-0.5 text-xs font-bold text-orange-300">
              ক্যাটাগরি
            </span>
          </div>
          <p className="mt-1 text-xs text-white/60 sm:text-sm">
            Browse normalized essential grocery buckets with store-by-store unit comparisons.
          </p>
        </div>

        <Link
          href="/categories"
          className="text-xs font-bold text-orange-400 hover:text-orange-300 sm:text-sm"
        >
          All Categories ›
        </Link>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {CATEGORIES.map((cat) => (
          <Link
            key={cat.key}
            href={`/search?category=${encodeURIComponent(cat.key)}`}
            className={`group flex flex-col justify-between rounded-3xl border bg-gradient-to-br ${cat.gradient} p-6 backdrop-blur-xl shadow-lg transition-all hover:scale-[1.02] ${cat.border}`}
          >
            <div>
              <div className="flex items-center justify-between">
                <span
                  className={`rounded-full px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wider ${cat.badgeColor}`}
                >
                  {cat.bnName}
                </span>
                <span className="text-white/40 transition-transform group-hover:translate-x-1 group-hover:text-white">
                  ›
                </span>
              </div>

              <h3 className="mt-4 font-display text-xl font-black text-white group-hover:text-orange-300">
                {cat.name}
              </h3>
              <p className="mt-1 text-xs text-white/60 leading-relaxed">{cat.desc}</p>
            </div>

            <div className="mt-6 flex items-center justify-between border-t border-white/10 pt-3 text-xs text-white/50">
              <span>View store prices</span>
              <span className="font-bold text-white">Compare →</span>
            </div>
          </Link>
        ))}
      </div>
    </section>
  );
}
