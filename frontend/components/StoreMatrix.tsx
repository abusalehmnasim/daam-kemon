import { StoreBadge } from "@/components/StoreBadge";

const STORES = [
  {
    name: "chaldal",
    displayName: "Chaldal",
    fee: "৳19 - ৳39",
    freeThreshold: "৳999+",
    speed: "1-2 Hour Express",
    note: "Instant warehouse dispatch across Dhaka, Ctg & Jashore.",
  },
  {
    name: "shwapno",
    displayName: "Shwapno",
    fee: "৳30",
    freeThreshold: "৳1,500+",
    speed: "Same Day Slot",
    note: "Bangladesh's largest retail chain with store pickup.",
  },
  {
    name: "unimart",
    displayName: "Unimart",
    fee: "৳50",
    freeThreshold: "None",
    speed: "Premium Slot",
    note: "High-end imported selections & Gulshan/Dhanmondi retail.",
  },
  {
    name: "agora",
    displayName: "Agora",
    fee: "৳40",
    freeThreshold: "৳2,000+",
    speed: "Scheduled Delivery",
    note: "Pioneer supermarket chain with trusted daily groceries.",
  },
  {
    name: "daraz",
    displayName: "Daraz Mart",
    fee: "৳35 - ৳50",
    freeThreshold: "Offers vary",
    speed: "Next Day",
    note: "Alibaba-backed logistics network covering 64 districts.",
  },
  {
    name: "othoba",
    displayName: "Othoba",
    fee: "৳35",
    freeThreshold: "৳1,000+",
    speed: "Standard Slot",
    note: "Pran-RFL official e-commerce with direct brand stock.",
  },
];

export function StoreMatrix() {
  return (
    <section className="rounded-3xl border border-white/10 bg-gradient-to-b from-white/10 to-white/5 p-6 backdrop-blur-2xl shadow-xl sm:p-8">
      <div className="flex flex-col justify-between gap-3 border-b border-white/10 pb-5 sm:flex-row sm:items-center">
        <div>
          <h2 className="text-xl font-extrabold tracking-tight text-white sm:text-2xl">
            Tracked Supermarkets & Delivery Tiers
          </h2>
          <p className="mt-1 text-xs text-white/60">
            Real automated daily scrapes directly factored into our Multi-Store Basket Optimizer.
          </p>
        </div>
        <div className="flex items-center gap-2 rounded-full border border-white/10 bg-black/30 px-3 py-1 text-xs text-emerald-400">
          <span className="h-2 w-2 rounded-full bg-save animate-pulse" />
          <span className="font-bold">Daily sync: 01:00 UTC</span>
        </div>
      </div>

      <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {STORES.map((st) => (
          <div
            key={st.name}
            className="flex flex-col justify-between rounded-2xl border border-white/10 bg-black/30 p-4 transition-all hover:border-white/25"
          >
            <div>
              <div className="flex items-center justify-between">
                <StoreBadge storeName={st.name} displayName={st.displayName} size="md" />
                <span className="rounded-full bg-white/10 px-2 py-0.5 text-[10px] font-bold text-white/70">
                  {st.speed}
                </span>
              </div>

              <div className="mt-3 flex items-baseline justify-between border-b border-white/10 pb-2">
                <span className="text-xs text-white/50">Delivery fee:</span>
                <span className="tnum font-extrabold text-white text-sm">{st.fee}</span>
              </div>
            </div>

            <p className="mt-3 text-[11px] leading-relaxed text-white/60">{st.note}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
