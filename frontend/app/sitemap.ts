import type { MetadataRoute } from "next";
import { getProductsForSitemap } from "@/lib/server-api";
import { productSlug } from "@/lib/slug";

export const revalidate = 86400;

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || "https://daamkemon.vercel.app";

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const staticUrls: MetadataRoute.Sitemap = [
    { url: SITE_URL, priority: 1, changeFrequency: "daily" },
    { url: `${SITE_URL}/categories`, priority: 0.8, changeFrequency: "daily" },
  ];

  const products = (await getProductsForSitemap()) || [];
  const productUrls: MetadataRoute.Sitemap = products.map((p) => ({
    url: `${SITE_URL}/product/${productSlug(p)}`,
    changeFrequency: "daily",
    priority: 0.6,
  }));

  return [...staticUrls, ...productUrls];
}
