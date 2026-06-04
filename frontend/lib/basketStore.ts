// Tiny localStorage-backed basket store. No external dep, no overengineering.

import type { BasketItemIn } from "@/types";

const KEY = "daamkemon.basket.v1";

export interface BasketEntry {
  id: string;       // local UID, stable across reorders
  productId?: number;
  query?: string;
  label: string;    // what we render in the basket list
  quantity: number;
}

export function load(): BasketEntry[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = window.localStorage.getItem(KEY);
    return raw ? (JSON.parse(raw) as BasketEntry[]) : [];
  } catch {
    return [];
  }
}

export function save(entries: BasketEntry[]) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(KEY, JSON.stringify(entries));
}

export function add(entry: Omit<BasketEntry, "id">): BasketEntry[] {
  const cur = load();
  const id = `${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
  cur.push({ ...entry, id });
  save(cur);
  return cur;
}

export function remove(id: string): BasketEntry[] {
  const cur = load().filter((e) => e.id !== id);
  save(cur);
  return cur;
}

export function setQuantity(id: string, quantity: number): BasketEntry[] {
  const cur = load().map((e) => (e.id === id ? { ...e, quantity } : e));
  save(cur);
  return cur;
}

export function toApi(entries: BasketEntry[]): BasketItemIn[] {
  return entries.map((e) => ({
    product_id: e.productId,
    query: e.query,
    quantity: e.quantity,
  }));
}
