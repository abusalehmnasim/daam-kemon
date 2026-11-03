"use client";

import { useEffect, useState } from "react";
import { load, type BasketEntry } from "./basketStore";

export function useBasket() {
  const [entries, setEntries] = useState<BasketEntry[]>([]);

  useEffect(() => {
    // Initial load
    setEntries(load());

    const handleUpdate = () => {
      setEntries(load());
    };

    window.addEventListener("daamkemon:basket", handleUpdate);
    window.addEventListener("storage", handleUpdate);

    return () => {
      window.removeEventListener("daamkemon:basket", handleUpdate);
      window.removeEventListener("storage", handleUpdate);
    };
  }, []);

  const totalCount = entries.reduce((acc, it) => acc + (it.quantity || 1), 0);

  return { entries, totalCount };
}
