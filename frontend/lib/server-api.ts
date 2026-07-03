// Server-only data fetching for SSR/ISR pages.
//
// Two reasons this is separate from lib/api.ts:
//  1. Server components can't use the relative "/api" rewrite — they need an
//     absolute backend URL (INTERNAL_API_URL, same value the rewrite uses).
//  2. These use Next's `revalidate` cache (ISR), not the client's `no-store`,
//     so product pages serve instantly from the edge even when the backend is
//     cold — and the backend never sees crawler traffic.

import type { ProductGroupOut } from "@/types";

const API_BASE =
  process.env.INTERNAL_API_URL || process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// 6h — matches the daily-ish scrape cadence; prices don't move faster than this.
const REVALIDATE = 21600;

// Returns null ONLY for a genuine 404 (product doesn't exist). Any other
// failure — network error, 5xx, cold-start timeout — THROWS, so Next serves the
// last-good ISR page and never caches the failure. Returning null on transient
// errors would make notFound() cache a 404 for the whole revalidate window,
// deindexing a real product every time the backend hiccups.
async function serverFetch<T>(path: string): Promise<T | null> {
  const res = await fetch(`${API_BASE}${path}`, { next: { revalidate: REVALIDATE } });
  if (res.status === 404) return null;
  if (!res.ok) throw new Error(`Backend ${res.status} for ${path}`);
  return (await res.json()) as T;
}

export function getProduct(id: number): Promise<ProductGroupOut | null> {
  return serverFetch<ProductGroupOut>(`/products/${id}`);
}

export interface PricePoint {
  day: string; // ISO date
  price: number; // cheapest recorded that day
}

export async function getProductHistory(id: number): Promise<PricePoint[]> {
  // History is enrichment — a failure should never break the product page.
  try {
    return (await serverFetch<PricePoint[]>(`/products/${id}/history`)) ?? [];
  } catch {
    return [];
  }
}

export interface ProductSlugData {
  id: number;
  name: string;
  brand: string | null;
  category: string;
  subcategory: string | null;
}

export async function getProductsForSitemap(): Promise<ProductSlugData[] | null> {
  // Swallow failures here: a transient backend blip should keep the last-good
  // sitemap (ISR) and must never fail the build — not deindex, unlike a page 404.
  try {
    return await serverFetch<ProductSlugData[]>(`/products/sitemap`);
  } catch {
    return null;
  }
}
