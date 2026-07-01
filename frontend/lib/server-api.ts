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

async function serverFetch<T>(path: string): Promise<T | null> {
  try {
    const res = await fetch(`${API_BASE}${path}`, { next: { revalidate: REVALIDATE } });
    if (!res.ok) return null;
    return (await res.json()) as T;
  } catch {
    return null;
  }
}

export function getProduct(id: number): Promise<ProductGroupOut | null> {
  return serverFetch<ProductGroupOut>(`/products/${id}`);
}

export interface ProductSlugData {
  id: number;
  name: string;
  brand: string | null;
  category: string;
  subcategory: string | null;
}

export function getProductsForSitemap(): Promise<ProductSlugData[] | null> {
  return serverFetch<ProductSlugData[]>(`/products/sitemap`);
}
