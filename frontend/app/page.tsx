import Link from "next/link";
import { SearchBar } from "@/components/SearchBar";

const SUGGESTIONS = [
  { label: "5L Soybean Oil", q: "5L soybean oil" },
  { label: "Miniket Rice 5kg", q: "miniket rice 5kg" },
  { label: "12 Eggs", q: "12 eggs" },
  { label: "Sugar 1kg", q: "sugar 1kg" },
  { label: "Masoor Dal 1kg", q: "masoor dal 1kg" },
];

const FEATURES = [
  {
    title: "Matched across stores",
    body: "The same product is grouped even when names, brands or spellings differ.",
  },
  {
    title: "Cheapest basket",
    body: "Add everything you need; get the cheapest single store and the best split.",
  },
  {
    title: "Per-unit prices",
    body: "A 5L bottle, a 4-pack and loose oil compared by price per litre or kilo.",
  },
];

export default function HomePage() {
  return (
    <div className="mx-auto max-w-2xl">
      <section className="pt-6 sm:pt-12">
        <h1 className="text-[26px] font-semibold leading-tight tracking-tight text-ink sm:text-3xl">
          Compare grocery prices across Bangladesh.
        </h1>
        <p className="mt-2 text-[15px] leading-relaxed text-muted">
          One search across Chaldal, Shwapno, Othoba, Unimart and Daraz — see who is cheapest, per
          litre or per kilo.
        </p>

        <div className="mt-5">
          <SearchBar autoFocus />
        </div>

        <div className="mt-3 flex flex-wrap gap-2">
          {SUGGESTIONS.map((s) => (
            <Link
              key={s.q}
              href={`/search?q=${encodeURIComponent(s.q)}`}
              className="rounded-full border border-line bg-card px-3 py-1.5 text-[13px] text-muted transition-colors hover:border-line-strong hover:text-ink"
            >
              {s.label}
            </Link>
          ))}
        </div>
      </section>

      <section className="mt-12 grid gap-3 sm:grid-cols-3">
        {FEATURES.map((f) => (
          <div key={f.title} className="rounded-card border border-line bg-card p-4">
            <h2 className="text-[13px] font-medium text-ink">{f.title}</h2>
            <p className="mt-1 text-[13px] leading-relaxed text-muted">{f.body}</p>
          </div>
        ))}
      </section>
    </div>
  );
}
