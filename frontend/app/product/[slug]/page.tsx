import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { getProduct } from "@/lib/server-api";
import { parseProductId, productSlug } from "@/lib/slug";
import type { ProductGroupOut } from "@/types";

export const revalidate = 21600;

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || "https://daamkemon.vercel.app";
const CURRENCY = "BDT";

function taka(n: number): string {
  return `৳${Math.round(n).toLocaleString("en-US")}`;
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
    <article>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />

      <nav className="text-xs text-gray-500 mb-3">
        <Link href="/" className="hover:underline">
          Home
        </Link>
        <span className="mx-1">/</span>
        <Link href="/categories" className="hover:underline">
          Categories
        </Link>
      </nav>

      <h1 className="text-xl font-bold tracking-tight">{p.name} — price in Bangladesh</h1>
      {low != null ? (
        <p className="mt-1 text-sm text-gray-600">
          From <span className="font-semibold text-brand">{taka(low)}</span> across{" "}
          {offerings.length} {offerings.length === 1 ? "listing" : "listings"}
          {group.cheapest_store ? `, cheapest at ${group.cheapest_store}` : ""}.
        </p>
      ) : (
        <p className="mt-1 text-sm text-gray-600">Currently out of stock across tracked stores.</p>
      )}

      <div className="mt-4 overflow-x-auto">
        <table className="w-full text-sm border-collapse">
          <thead>
            <tr className="text-left text-gray-500 border-b">
              <th className="py-2 pr-3 font-medium">Store</th>
              <th className="py-2 pr-3 font-medium">Listing</th>
              <th className="py-2 pr-3 font-medium">Price</th>
              <th className="py-2 pr-3 font-medium">Stock</th>
              <th className="py-2 font-medium"></th>
            </tr>
          </thead>
          <tbody>
            {offerings.map((o, i) => {
              const cheapest = o.in_stock && o.price === low;
              return (
                <tr key={o.store_product_id} className={i === 0 ? "" : "border-t"}>
                  <td className="py-2 pr-3 font-medium">{o.store_display_name}</td>
                  <td className="py-2 pr-3 text-gray-600">{o.name}</td>
                  <td className="py-2 pr-3">
                    <span className={cheapest ? "font-semibold text-brand" : ""}>
                      {taka(o.price)}
                    </span>
                    {o.original_price && o.original_price > o.price ? (
                      <span className="ml-1 text-xs text-gray-400 line-through">
                        {taka(o.original_price)}
                      </span>
                    ) : null}
                  </td>
                  <td className="py-2 pr-3 text-xs">
                    {o.in_stock ? (
                      <span className="text-green-700">In stock</span>
                    ) : (
                      <span className="text-gray-400">Out</span>
                    )}
                  </td>
                  <td className="py-2">
                    <a
                      href={`/api/click/${o.store_product_id}`}
                      rel="nofollow sponsored noopener"
                      className="text-brand hover:underline"
                    >
                      Visit
                    </a>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <p className="mt-6 text-xs text-gray-500">
        Prices are collected automatically and may lag store changes. Daam Kemon is independent and
        not affiliated with the listed stores.
      </p>
    </article>
  );
}
