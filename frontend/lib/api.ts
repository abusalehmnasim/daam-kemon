import type {
  BasketItemIn,
  BasketOptimizeResponse,
  CategoryGroupOut,
  SearchResponse,
} from "@/types";

const BASE = process.env.NEXT_PUBLIC_API_URL || "/api";
const TIMEOUT_MS = 25000;

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);
  try {
    const res = await fetch(`${BASE}${path}`, {
      ...init,
      signal: init?.signal || controller.signal,
      headers: {
        "Content-Type": "application/json",
        ...(init?.headers || {}),
      },
      cache: "no-store",
    });
    if (!res.ok) {
      throw new Error(`API ${res.status}: ${await res.text()}`);
    }
    return (await res.json()) as Promise<T>;
  } catch (err: unknown) {
    if (err instanceof Error && err.name === "AbortError") {
      throw new Error("Request timed out. The server may still be waking up — please try again.");
    }
    throw err;
  } finally {
    clearTimeout(timer);
  }
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
