import type { PricePoint } from "@/lib/server-api";

function fmtDate(iso: string): string {
  const d = new Date(iso + "T00:00:00Z");
  return d.toLocaleDateString("en-GB", { day: "numeric", month: "short", timeZone: "UTC" });
}

function taka(n: number): string {
  return "৳" + Math.round(n).toLocaleString("en-US");
}

// Server-rendered price-history chart. Pure SVG, no client JS — it renders
// once per ISR revalidation alongside the rest of the page.
export function PriceSparkline({ points }: { points: PricePoint[] }) {
  if (points.length < 2) return null;

  const W = 640;
  const H = 120;
  const PAD_X = 6;
  const PAD_Y = 14;

  const prices = points.map((p) => p.price);
  const min = Math.min(...prices);
  const max = Math.max(...prices);
  const span = max - min || 1;

  const x = (i: number) => PAD_X + (i / (points.length - 1)) * (W - 2 * PAD_X);
  const y = (price: number) => PAD_Y + ((max - price) / span) * (H - 2 * PAD_Y);

  const path = points
    .map((p, i) => `${i === 0 ? "M" : "L"}${x(i).toFixed(1)},${y(p.price).toFixed(1)}`)
    .join(" ");

  const minIdx = prices.indexOf(min);
  const last = points[points.length - 1];

  return (
    <figure className="rounded-card border border-line bg-card p-4">
      <figcaption className="flex items-baseline justify-between">
        <span className="text-[13px] font-medium text-ink">Cheapest recorded price</span>
        <span className="tnum text-xs text-muted">
          low {taka(min)} · high {taka(max)}
        </span>
      </figcaption>
      <svg
        viewBox={`0 0 ${W} ${H}`}
        className="mt-2 w-full"
        role="img"
        aria-label={`Price history: lowest ${taka(min)}, highest ${taka(max)}, latest ${taka(last.price)}`}
      >
        <path d={path} fill="none" stroke="#0E7A46" strokeWidth="1.5" strokeLinejoin="round" />
        <circle cx={x(minIdx)} cy={y(min)} r="3" fill="#0E7A46" />
      </svg>
      <div className="mt-1 flex justify-between text-[11px] text-faint">
        <span>{fmtDate(points[0].day)}</span>
        <span>{fmtDate(last.day)}</span>
      </div>
    </figure>
  );
}
