// Keyword-rich, ID-resolvable slugs: "fresh-soybean-oil-5l-42".
// The trailing integer is the canonical product id — parse it back out to fetch.

export function slugify(text: string): string {
  return text
    .toLowerCase()
    .normalize("NFKD")
    .replace(/[^a-z0-9\s-]/g, "")
    .trim()
    .replace(/\s+/g, "-")
    .replace(/-+/g, "-");
}

export function productSlug(p: { id: number; name: string }): string {
  const base = slugify(p.name) || "product";
  return `${base}-${p.id}`;
}

export function parseProductId(slug: string): number | null {
  const match = slug.match(/-(\d+)$/);
  if (match) return Number(match[1]);
  const bare = Number(slug);
  return Number.isInteger(bare) && bare > 0 ? bare : null;
}
