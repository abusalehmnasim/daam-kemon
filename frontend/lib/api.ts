import type {
  BasketItemIn,
  BasketOptimizeResponse,
  CategoryGroupOut,
  SearchResponse,
} from "@/types";

const BASE = process.env.NEXT_PUBLIC_API_URL || "/api";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {}),
    },
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(`API ${res.status}: ${await res.text()}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  search: (q: string, opts?: { category?: string; subcategory?: string }) => {
    const params = new URLSearchParams({ q });
    if (opts?.category) params.set("category", opts.category);
    if (opts?.subcategory) params.set("subcategory", opts.subcategory);
    return request<SearchResponse>(`/search?${params.toString()}`);
  },
  categories: () => request<CategoryGroupOut[]>(`/categories`),
  optimize: (items: BasketItemIn[], stores?: string[]) =>
    request<BasketOptimizeResponse>(`/basket/optimize`, {
      method: "POST",
      body: JSON.stringify({ items, stores }),
    }),
  clickUrl: (storeProductId: number) => `${BASE}/click/${storeProductId}`,
};
