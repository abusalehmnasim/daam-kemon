import Link from "next/link";
import { SearchBar } from "@/components/SearchBar";

const SUGGESTIONS = [
  { label: "5L Soybean Oil",   q: "5L soybean oil" },
  { label: "Miniket Rice 5kg", q: "miniket rice 5kg" },
  { label: "12 Eggs",          q: "12 eggs" },
  { label: "Sugar 1kg",        q: "sugar 1kg" },
  { label: "Masoor Dal 1kg",   q: "masoor dal 1kg" },
];

export default function HomePage() {
  return (
    <div className="space-y-8">
      <section className="pt-8 text-center space-y-3">
        <h1 className="text-3xl sm:text-4xl font-bold tracking-tight">
          One basket, every store. <span className="text-brand">Cheaper.</span>
        </h1>
        <p className="text-gray-600 max-w-xl mx-auto">
          Compare grocery prices across Chaldal, Shwapno, Othoba and Unimart — and find
          the cheapest way to buy your whole basket.
        </p>
        <div className="max-w-xl mx-auto pt-2">
          <SearchBar />
        </div>
        <div className="flex flex-wrap gap-2 justify-center pt-3">
          {SUGGESTIONS.map((s) => (
            <Link
              key={s.q}
              href={`/search?q=${encodeURIComponent(s.q)}`}
              className="text-sm px-3 py-1.5 rounded-full bg-white border border-gray-200 hover:border-brand hover:text-brand"
            >
              {s.label}
            </Link>
          ))}
        </div>
      </section>

      <section className="grid sm:grid-cols-3 gap-4 pt-6">
        <Feature title="Smart matching" body="We group the same product across stores — even when names, brands or spellings differ." />
        <Feature title="Basket optimization" body="Add everything you need; we find the cheapest single store and the best split." />
        <Feature title="Loose & packaged" body="Sugar, rice and dal sold loose are compared alongside branded packs, the way you actually shop." />
      </section>
    </div>
  );
}

function Feature({ title, body }: { title: string; body: string }) {
  return (
    <div className="bg-white border border-gray-200 rounded-xl p-4">
      <h3 className="font-semibold mb-1">{title}</h3>
      <p className="text-sm text-gray-600">{body}</p>
    </div>
  );
}
