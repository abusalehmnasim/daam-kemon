# Gold matching corpus — `gold_pairs.jsonl`

The first labeled evaluation set for Daam Kemon's product matching. Each line
is one pair of **raw listing names exactly as scraped** (`store_products.
store_product_name`, untouched), labeled with the relationship a shopper would
assign to the two real-world products:

```json
{"a": "<raw name>", "b": "<raw name>", "label": "same|same_bucket|different",
 "note": "<why, when non-obvious>", "labeler": "<who>", "stratum": "A|B|C|D"}
```

Only `a`, `b`, `label` are read by the harness (`tests/test_gold_corpus.py`);
the rest is provenance. `stratum` records which sampling stratum of
`analytics/export_pair_candidates.py` the pair came from (A: matcher-merged
cross-store, B: same-bucket different-canonical cross-store, C: same-category
controls, D: within-store fragmentation candidates).

## Labels — from the shopper's view, not the pipeline's

- **`same`** — the same real-world product: same brand, same variant, same
  size. Spelling, language (Bangla/English), word order, and store noise may
  differ. This is the **ingest** question: these two listings belong on one
  canonical `products` row.
- **`same_bucket`** — different brand (or unbranded/loose), but the same
  product type at the same size — rows a shopper price-comparing one item
  would want in a single comparison table ("1kg miniket rice", "500g
  detergent powder"). This is the **search** question: group, but never merge
  canonicals.
- **`different`** — everything else: different product type (cardamom vs
  curry masala, even at the same size), different size beyond tolerance, or a
  variant difference that changes the product itself (scent/flavor lines,
  official vs unofficial imports).

Judge `same_bucket` **semantically**, not by the current bucket key. The
bucket key collapses `(category, subcategory=None, size)` — so "any two 50g
spices" share a bucket today. If the two items are not real substitutes
(poppy seed vs white pepper), the label is `different`; the corpus must
measure that blind spot, not inherit it.

Rules of thumb:

- Size difference beyond `SIZE_TOLERANCE` (2%, `app/core/matcher.py`) →
  `different`, even for the identical brand and product.
- Same brand, same product, one listing omits the variant word the other has
  ("UHT Milk 1L (New Zealand)" vs "Cowhead Pure Milk UHT 1L (New Zealand)"):
  label what the names alone support. If the unbranded name could be a
  different brand's product, prefer `same_bucket` and say why in `note` —
  wrong merges (silent corruption) cost more than missed merges.
- Loose/khola goods have no brand; two loose listings of the same commodity
  and unit are `same_bucket` (or `same` only when the store-given names make
  the identical origin explicit).
- Multipacks: "12 pcs" vs "1 dozen" is the same size; "8 pcs family pack" vs
  "single" is `different`.

## Provenance / trust levels

`labeler` values:

- `claude-seed-v0` — machine-proposed seed labels (2026-07-12), from real
  production pairs, awaiting owner review. Good enough to wire the harness
  and set a provisional baseline; **not** yet citable as human gold.
- `owner` — reviewed/decided by the project owner. The target state: promote
  seed rows by re-labeling `labeler` after review; delete rows that are
  wrong.

Keep the file append-mostly: fix labels in place (git history is the audit
trail), add new tranches at the end, never re-order existing lines.

## Regenerating candidates

```bash
cd backend
python -m analytics.export_pair_candidates --per-stratum 150 --out pairs.jsonl
```

Read-only against `DATABASE_URL` (env or `backend/.env`). Label from the
candidate `context` block plus the raw names; strip `context` before adding
records here.
