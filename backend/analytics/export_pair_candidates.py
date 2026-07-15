"""Export candidate listing-name pairs for the gold matching corpus.

Read-only. Pulls real (store_product_name, store_product_name) pairs from
store_products, stratified so the corpus over-samples the hard cases instead
of easy exacts:

  A  cross-store pairs the matcher put on the SAME canonical
     (checks ingest precision: a wrong merge here is silent corruption)
  B  cross-store pairs in the same (category, subcategory, ~size) bucket but
     on DIFFERENT canonicals
     (contains both the recall misses — same product split by brand spelling —
      and the true same_bucket pairs the split is supposed to produce)
  C  cross-store pairs in the same category but different subcategory or a
     size well outside tolerance (expected "different"; control stratum)
  D  same-store pairs in the same bucket on different canonicals with high
     name similarity (within-store catalog fragmentation candidates)

Output is JSONL, one candidate per line:
    {"a": ..., "b": ..., "stratum": "A|B|C|D",
     "context": {stores, categories, brands, sizes, matcher verdicts}}

The candidates are NOT labels. A human labels a/b into
backend/tests/fixtures/gold_pairs.jsonl per the guide in
backend/tests/fixtures/README.md; the context block exists to make labeling
faster and is dropped from the corpus record.

Usage (from backend/, where .env lives):
    python -m analytics.export_pair_candidates --per-stratum 150 --out pairs.jsonl

DATABASE_URL comes from the environment or backend/.env (quoted values OK).
Size tolerance mirrors matcher.SIZE_TOLERANCE (0.02) without importing app
code, so this script stays runnable with only asyncpg installed.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys

import asyncpg

SIZE_TOLERANCE = 0.02  # keep in sync with app/core/matcher.py


def dsn() -> str:
    url = os.environ.get("DATABASE_URL", "").strip()
    if not url and os.path.exists(".env"):
        with open(".env", encoding="utf-8") as f:
            for line in f:
                if line.startswith("DATABASE_URL="):
                    url = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break
    if not url:
        sys.exit("DATABASE_URL is not set (env or backend/.env)")
    return (url.replace("postgresql+asyncpg://", "postgresql://", 1)
               .replace("postgres://", "postgresql://", 1))


# Every stratum yields the same column list so rows serialize uniformly.
COLS = """
    sa.store_product_name AS a,  sb.store_product_name AS b,
    sa.store_name AS store_a,    sb.store_name AS store_b,
    pa.category   AS cat_a,      pb.category   AS cat_b,
    pa.subcategory AS sub_a,     pb.subcategory AS sub_b,
    pa.brand AS brand_a,         pb.brand AS brand_b,
    pa.size_value AS size_a,     pa.size_unit AS unit_a,
    pb.size_value AS size_b,     pb.size_unit AS unit_b,
    sa.match_method AS method_a, sb.match_method AS method_b,
    (sa.product_id = sb.product_id) AS same_canonical
"""

STRATA = {
    # A: same canonical, cross-store. Random sample; every store pair welcome.
    "A": f"""
        SELECT {COLS}
        FROM store_products sa
        JOIN store_products sb ON sb.product_id = sa.product_id
                              AND sb.store_name > sa.store_name
        JOIN products pa ON pa.id = sa.product_id
        JOIN products pb ON pb.id = sb.product_id
        ORDER BY random() LIMIT $1
    """,
    # B: same bucket (category + subcategory-or-both-null + size within
    # tolerance + same loose flag), different canonicals, cross-store.
    "B": f"""
        SELECT {COLS}
        FROM products pa
        JOIN products pb
          ON pb.id > pa.id
         AND pb.category = pa.category
         AND COALESCE(pb.subcategory,'') = COALESCE(pa.subcategory,'')
         AND pb.is_loose = pa.is_loose
         AND pa.base_unit_qty IS NOT NULL AND pb.base_unit_qty IS NOT NULL
         AND abs(pa.base_unit_qty - pb.base_unit_qty)
             <= {SIZE_TOLERANCE} * greatest(pa.base_unit_qty, pb.base_unit_qty)
        JOIN store_products sa ON sa.product_id = pa.id
        JOIN store_products sb ON sb.product_id = pb.id
                              AND sb.store_name <> sa.store_name
        ORDER BY random() LIMIT $1
    """,
    # C: control — same category but a clearly different size (>25% apart) or
    # different subcategory; expected label is almost always "different".
    "C": f"""
        SELECT {COLS}
        FROM products pa
        JOIN products pb
          ON pb.id > pa.id
         AND pb.category = pa.category
         AND (
              COALESCE(pb.subcategory,'') <> COALESCE(pa.subcategory,'')
              OR (pa.base_unit_qty IS NOT NULL AND pb.base_unit_qty IS NOT NULL
                  AND abs(pa.base_unit_qty - pb.base_unit_qty)
                      > 0.25 * greatest(pa.base_unit_qty, pb.base_unit_qty))
             )
        JOIN store_products sa ON sa.product_id = pa.id
        JOIN store_products sb ON sb.product_id = pb.id
                              AND sb.store_name <> sa.store_name
        ORDER BY random() LIMIT $1
    """,
    # D: within-store fragmentation — same store, same bucket, different
    # canonicals, similar names. These are the matcher's likely recall misses.
    "D": f"""
        SELECT {COLS}
        FROM products pa
        JOIN products pb
          ON pb.id > pa.id
         AND pb.category = pa.category
         AND COALESCE(pb.subcategory,'') = COALESCE(pa.subcategory,'')
         AND pb.is_loose = pa.is_loose
         AND pa.base_unit_qty IS NOT NULL AND pb.base_unit_qty IS NOT NULL
         AND abs(pa.base_unit_qty - pb.base_unit_qty)
             <= {SIZE_TOLERANCE} * greatest(pa.base_unit_qty, pb.base_unit_qty)
        JOIN store_products sa ON sa.product_id = pa.id
        JOIN store_products sb ON sb.product_id = pb.id
                              AND sb.store_name = sa.store_name
        WHERE similarity(sa.store_product_name, sb.store_product_name) > 0.45
        ORDER BY random() LIMIT $1
    """,
}


async def export(per_stratum: int, out_path: str) -> None:
    conn = await asyncpg.connect(dsn(), timeout=30)
    n_written = 0
    try:
        with open(out_path, "w", encoding="utf-8") as out:
            for tag, sql in STRATA.items():
                rows = await conn.fetch(sql, per_stratum)
                for r in rows:
                    rec = {
                        "a": r["a"],
                        "b": r["b"],
                        "stratum": tag,
                        "context": {
                            "stores": [r["store_a"], r["store_b"]],
                            "categories": [r["cat_a"], r["cat_b"]],
                            "subcategories": [r["sub_a"], r["sub_b"]],
                            "brands": [r["brand_a"], r["brand_b"]],
                            "sizes": [
                                f"{r['size_a']}{r['unit_a']}",
                                f"{r['size_b']}{r['unit_b']}",
                            ],
                            "matcher_same_canonical": r["same_canonical"],
                            "match_methods": [r["method_a"], r["method_b"]],
                        },
                    }
                    out.write(json.dumps(rec, ensure_ascii=False) + "\n")
                n_written += len(rows)
                print(f"stratum {tag}: {len(rows)} pairs", file=sys.stderr)
    finally:
        await conn.close()
    print(f"wrote {n_written} candidates -> {out_path}", file=sys.stderr)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--per-stratum", type=int, default=150)
    ap.add_argument("--out", default="pair_candidates.jsonl")
    args = ap.parse_args()
    asyncio.run(export(args.per_stratum, args.out))
