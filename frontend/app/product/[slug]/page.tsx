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

  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "Product",
    name: p.name,
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

      <h1 className="text-xl font-semibold tracking-tight text-ink">
        {p.name} — price in Bangladesh
      </h1>
      {low != null ? (
        <p className="mt-1.5 text-[15px] text-muted">
          From <span className="font-semibold text-brand">{taka(low)}</span>
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

      {history.length >= 2 && (
        <div className="mt-5">
          <PriceSparkline points={history} />
        </div>
      )}

      <div className="mt-5 overflow-hidden rounded-card border border-line bg-card">
        <div className="overflow-x-auto">
          <div className="min-w-[560px]">
            <div className="grid grid-cols-[8rem_minmax(0,1fr)_5.5rem_7rem_auto] items-center gap-x-3 border-b border-line px-4 py-2 text-[10px] uppercase tracking-wide text-faint">
              <span>Store</span>
              <span>Listing</span>
              <span className="text-right">Unit</span>
              <span className="text-right">Price</span>
              <span />
            </div>
            <ul className="divide-y divide-line/60">
              {offerings.map((o) => {
                const cheapest = o.in_stock && o.price === low;
                return (
                  <li
                    key={o.store_product_id}
                    className={`grid grid-cols-[8rem_minmax(0,1fr)_5.5rem_7rem_auto] items-center gap-x-3 px-4 py-2.5 text-sm ${
                      o.in_stock ? "" : "opacity-60"
                    }`}
                  >
                    <div className="flex min-w-0 items-center gap-1.5">
                      {cheapest && (
                        <span
                          className="h-1.5 w-1.5 shrink-0 rounded-full bg-brand"
                          aria-hidden="true"
                        />
                      )}
                      <span className="truncate font-medium text-ink">{o.store_display_name}</span>
                    </div>
                    <span className="truncate text-muted">{o.name}</span>
                    <span className="tnum text-right text-[13px] text-muted">
                      {basis ? unitPrice(o.price, basis) : "—"}
                    </span>
                    <div className="text-right">
                      {o.in_stock ? (
                        <span
                          className={`tnum text-[15px] font-semibold ${
                            cheapest ? "text-brand" : "text-ink"
                          }`}
                        >
                          {taka(o.price)}
                        </span>
                      ) : (
                        <span className="text-xs text-faint">Out of stock</span>
                      )}
                      {o.in_stock && o.original_price && o.original_price > o.price ? (
                        <span className="tnum ml-1.5 text-xs text-faint line-through">
                          {taka(o.original_price)}
                        </span>
                      ) : null}
                    </div>
                    <a
                      href={`/api/click/${o.store_product_id}`}
                      rel="nofollow sponsored noopener"
                      className="justify-self-end text-xs font-medium text-muted underline-offset-2 hover:text-ink hover:underline"
                    >
                      Visit
                    </a>
                  </li>
                );
              })}
            </ul>
          </div>
        </div>
      </div>

      <p className="mt-6 text-xs text-faint">
        Prices are collected automatically and may lag store changes. Daam Kemon is independent and
        not affiliated with the listed stores.
      </p>
    </article>
  );
}
