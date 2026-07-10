import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { AddToBasket } from "@/components/AddToBasket";
import { PriceSparkline } from "@/components/PriceSparkline";
import { getProduct, getProductHistory } from "@/lib/server-api";
import { parseProductId, productSlug } from "@/lib/slug";
import type { ProductGroupOut, ProductOut } from "@/types";

export const revalidate = 21600;

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || "https://daamkemon.vercel.app";
const CURRENCY = "BDT";

function taka(n: number): string {
  return `৳${Math.round(n).toLocaleString("en-US")}`;
}

function unitBasis(p: ProductOut): { divisor: number; label: string } | null {
  const v = p.size_value;
  if (!v || v <= 0 || !p.size_unit) return null;
  const u = p.size_unit.toUpperCase();
  if (u === "L") return { divisor: v, label: "/L" };
  if (u === "ML") return { divisor: v / 1000, label: "/L" };
  if (u === "KG") return { divisor: v, label: "/kg" };
  if (u === "G") return { divisor: v / 1000, label: "/kg" };
  if (u === "PCS") return { divisor: v, label: p.category === "eggs" ? "/egg" : "/pc" };
  return null;
}

function unitPrice(price: number, basis: { divisor: number; label: string }): string {
  const val = price / basis.divisor;
  const rounded = val >= 100 ? Math.round(val) : Math.round(val * 10) / 10;
  return "৳" + rounded.toLocaleString("en-US") + basis.label;
}

async function load(slug: string): Promise<ProductGroupOut | null> {
  const id = parseProductId(slug);
  if (id === null) return null;
  return getProduct(id);
}

export async function generateMetadata({
  params,
}: {
  params: { slug: string };
}): Promise<Metadata> {
  const group = await load(params.slug);
  if (!group) return { title: "Product not found — Daam Kemon" };

  const p = group.product;
  const stores = group.offerings.length;
  const canonical = `${SITE_URL}/product/${productSlug(p)}`;
  const title = `${p.name} price in Bangladesh — compare ${stores} stores | Daam Kemon`;
  const description =
    group.cheapest_price != null
      ? `Compare ${p.name} prices across ${stores} stores. Cheapest ${taka(group.cheapest_price)}${
          group.cheapest_store ? ` at ${group.cheapest_store}` : ""
        }. Updated daily.`
      : `Compare ${p.name} prices across Bangladeshi online stores. Updated daily.`;

  return {
    title,
    description,
    alternates: { canonical },
    openGraph: { title, description, url: canonical, type: "website" },
  };
}

export default async function ProductPage({ params }: { params: { slug: string } }) {
  const group = await load(params.slug);
  if (!group) notFound();

  const p = group.product;
  const history = await getProductHistory(p.id);
  const basis = unitBasis(p);
  const offerings = [...group.offerings].sort(
    (a, b) => Number(!a.in_stock) - Number(!b.in_stock) || a.price - b.price
  );
  const inStock = offerings.filter((o) => o.in_stock);
  const prices = inStock.map((o) => o.price);
  const low = prices.length ? Math.min(...prices) : null;
  const high = prices.length ? Math.max(...prices) : null;
  // Product image from the cheapest offering that has one (offerings are sorted
  // in-stock + cheapest first). Scraped store-CDN URLs across many domains.
  const image = offerings.find((o) => o.image_url)?.image_url ?? null;

  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "Product",
    name: p.name,
    ...(image ? { image: [image] } : {}),
    ...(p.brand ? { brand: { "@type": "Brand", name: p.brand } } : {}),
    ...(low != null
      ? {
          offers: {
            "@type": "AggregateOffer",
            priceCurrency: CURRENCY,
            lowPrice: low,
            highPrice: high,
            offerCount: offerings.length,
            availability: inStock.length
              ? "https://schema.org/InStock"
              : "https://schema.org/OutOfStock",
          },
        }
      : {}),
  };

  return (
    <article className="mx-auto max-w-3xl">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify(jsonLd).replace(/</g, "\\u003c"),
        }}
      />

      <nav className="mb-4 text-xs text-faint">
        <Link href="/" className="hover:text-ink">
          Home
        </Link>
        <span className="mx-1.5">/</span>
        <Link href="/categories" className="hover:text-ink">
          Categories
        </Link>
      </nav>

      <div className="flex flex-col gap-4 sm:flex-row sm:items-start">
        {image && (
          <div className="shrink-0 self-start rounded-card border border-line bg-white p-2">
            {/* eslint-disable-next-line @next/next/no-img-element -- scraped store-CDN images span arbitrary domains; next/image remotePatterns would need constant maintenance */}
            <img
              src={image}
              alt={p.name}
              width={112}
              height={112}
              loading="lazy"
              referrerPolicy="no-referrer"
              className="h-28 w-28 object-contain"
            />
          </div>
        )}
        <div className="min-w-0">
          <h1 className="text-xl font-semibold tracking-tight text-ink">
            {p.name} — price in Bangladesh
          </h1>
          {low != null ? (
            <p className="mt-1.5 text-[15px] text-muted">
              From <span className="font-semibold text-save">{taka(low)}</span>
              {basis ? ` (${unitPrice(low, basis)})` : ""} across {offerings.length}{" "}
              {offerings.length === 1 ? "listing" : "listings"}
              {group.cheapest_store ? `, cheapest at ${group.cheapest_store}` : ""}.
            </p>
          ) : (
            <p className="mt-1.5 text-[15px] text-muted">
              Currently out of stock across tracked stores.
            </p>
          )}
          <div className="mt-4">
            <AddToBasket productId={p.id} label={p.name} />
          </div>
        </div>
      </div>

      {history.length >= 2 && (
        <div className="mt-5">
          <PriceSparkline points={history} />
        </div>
      )}

      {/* Mobile-first rows: no horizontal scroll, no fixed columns. */}
      <div className="mt-5 overflow-hidden rounded-card border border-line bg-card">
        <ul className="divide-y divide-line/60">
          {offerings.map((o) => {
            const cheapest = o.in_stock && o.price === low;
            return (
              <li
                key={o.store_product_id}
                className={`px-4 py-3 text-sm ${cheapest ? "bg-save-weak/60" : ""} ${
                  o.in_stock ? "" : "opacity-60"
                }`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-1.5">
                      {cheapest && (
                        <span className="shrink-0 rounded-full bg-save px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-white">
                          Cheapest
                        </span>
                      )}
                      <span className="truncate font-medium text-ink">{o.store_display_name}</span>
                    </div>
                    <p className="mt-0.5 truncate text-xs text-muted">{o.name}</p>
                  </div>
                  <div className="shrink-0 text-right">
                    {o.in_stock ? (
                      <>
                        <div
                          className={`tnum text-[15px] font-semibold leading-tight ${
                            cheapest ? "text-save" : "text-ink"
                          }`}
                        >
                          {taka(o.price)}
                        </div>
                        {o.original_price && o.original_price > o.price ? (
                          <div className="tnum text-xs text-faint line-through">
                            {taka(o.original_price)}
                          </div>
                        ) : null}
                        {basis && (
                          <div className="tnum text-[11px] text-muted">
                            {unitPrice(o.price, basis)}
                          </div>
                        )}
                      </>
                    ) : (
                      <span className="text-xs text-faint">Out of stock</span>
                    )}
                  </div>
                </div>
                <div className="mt-2 flex justify-end">
                  <a
                    href={`/api/click/${o.store_product_id}`}
                    rel="nofollow sponsored noopener"
                    className="inline-flex h-9 items-center px-2 text-xs font-medium text-muted underline-offset-2 hover:text-ink hover:underline"
                  >
                    Visit
                  </a>
                </div>
              </li>
            );
          })}
        </ul>
      </div>

      <p className="mt-6 text-xs text-faint">
        Prices are collected automatically and may lag store changes. Daam Kemon is independent and
        not affiliated with the listed stores.
      </p>
    </article>
  );
}
