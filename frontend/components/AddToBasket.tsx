"use client";

import { add as addToBasket } from "@/lib/basketStore";
import { useState } from "react";

// Small client island for the (otherwise fully server-rendered) product page.
export function AddToBasket({ productId, label }: { productId: number; label: string }) {
  const [added, setAdded] = useState(false);

  return (
    <button
      onClick={() => {
        addToBasket({ productId, label, quantity: 1 });
        setAdded(true);
        setTimeout(() => setAdded(false), 1500);
      }}
      className="inline-flex h-9 items-center rounded-lg bg-brand px-4 text-sm font-semibold text-white transition-colors hover:bg-brand-dark"
    >
      {added ? "Added ✓" : "Add to basket"}
    </button>
  );
}
