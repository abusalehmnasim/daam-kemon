-- Daam Kemon initial schema
-- Designed for messy Bangladesh grocery data: products are canonical,
-- store_products are observed listings that map (probabilistically) onto products.

CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS unaccent;

-- Canonical product groups. One row per "thing the shopper actually wants"
-- (e.g. "Fresh Soybean Oil 5L", or for loose goods "Miniket Rice (loose)").
CREATE TABLE IF NOT EXISTS products (
    id              BIGSERIAL PRIMARY KEY,
    name            TEXT        NOT NULL,
    normalized_name TEXT        NOT NULL,
    brand           TEXT,
    category        TEXT        NOT NULL,
    subcategory     TEXT,
    size_value      NUMERIC(10,3),          -- e.g. 5.000
    size_unit       TEXT,                   -- L, ML, KG, G, PCS
    base_unit_qty   NUMERIC(12,4),          -- normalized to base unit (ml / g / pcs) for per-unit pricing
    is_loose        BOOLEAN     NOT NULL DEFAULT FALSE,
    barcode         TEXT,
    metadata        JSONB       NOT NULL DEFAULT '{}'::jsonb,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS products_normalized_name_trgm ON products USING gin (normalized_name gin_trgm_ops);
-- Search also fuzzy-matches the raw `name`; index it so the pg_trgm `%` operator
-- can use a GIN scan instead of a seq scan as the catalog grows.
CREATE INDEX IF NOT EXISTS products_name_trgm            ON products USING gin (name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS products_category_idx         ON products (category, subcategory);
CREATE INDEX IF NOT EXISTS products_brand_idx            ON products (brand);
CREATE UNIQUE INDEX IF NOT EXISTS products_dedupe_key
    ON products (category, COALESCE(subcategory,''), COALESCE(brand,''), COALESCE(size_unit,''), COALESCE(size_value, 0), is_loose);

-- One row per (store, listing). The price/availability snapshot lives here;
-- history is appended into price_history on every scrape cycle.
CREATE TABLE IF NOT EXISTS store_products (
    id                  BIGSERIAL PRIMARY KEY,
    product_id          BIGINT REFERENCES products(id) ON DELETE SET NULL,
    store_name          TEXT        NOT NULL,
    store_product_id    TEXT        NOT NULL,        -- store's own SKU / slug
    store_product_name  TEXT        NOT NULL,
    store_product_url   TEXT,
    image_url           TEXT,
    price               NUMERIC(10,2) NOT NULL,
    original_price      NUMERIC(10,2),
    currency            TEXT        NOT NULL DEFAULT 'BDT',
    in_stock            BOOLEAN     NOT NULL DEFAULT TRUE,
    delivery_fee        NUMERIC(10,2),               -- nullable; some stores tier this
    match_confidence    NUMERIC(4,3),                -- 0..1, how sure are we about product_id
    match_method        TEXT,                        -- exact | brand | category | manual | unmatched
    raw                 JSONB       NOT NULL DEFAULT '{}'::jsonb,
    first_seen_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_seen_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (store_name, store_product_id)
);

CREATE INDEX IF NOT EXISTS store_products_product_idx     ON store_products (product_id);
CREATE INDEX IF NOT EXISTS store_products_store_idx       ON store_products (store_name);
CREATE INDEX IF NOT EXISTS store_products_name_trgm       ON store_products USING gin (store_product_name gin_trgm_ops);

-- Append-only price history. Keep small per row, query by (store_product_id, observed_at).
CREATE TABLE IF NOT EXISTS price_history (
    id                BIGSERIAL PRIMARY KEY,
    store_product_id  BIGINT NOT NULL REFERENCES store_products(id) ON DELETE CASCADE,
    price             NUMERIC(10,2) NOT NULL,
    in_stock          BOOLEAN NOT NULL,
    observed_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS price_history_sp_time_idx ON price_history (store_product_id, observed_at DESC);

-- Store metadata. Delivery fee tiers stay here as JSON (each store has different rules).
CREATE TABLE IF NOT EXISTS stores (
    name              TEXT PRIMARY KEY,
    display_name      TEXT NOT NULL,
    base_url          TEXT NOT NULL,
    delivery_config   JSONB NOT NULL DEFAULT '{}'::jsonb,
    affiliate_config  JSONB NOT NULL DEFAULT '{}'::jsonb,    -- monetization hook
    active            BOOLEAN NOT NULL DEFAULT TRUE
);

-- Baskets (anonymous-friendly: user_id nullable, session_id supported).
CREATE TABLE IF NOT EXISTS baskets (
    id           BIGSERIAL PRIMARY KEY,
    user_id      TEXT,
    session_id   TEXT,
    items        JSONB       NOT NULL DEFAULT '[]'::jsonb,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS baskets_session_idx ON baskets (session_id);

-- Outbound click tracking (monetization hook only; do not build attribution yet).
CREATE TABLE IF NOT EXISTS outbound_clicks (
    id                BIGSERIAL PRIMARY KEY,
    store_product_id  BIGINT REFERENCES store_products(id) ON DELETE SET NULL,
    store_name        TEXT NOT NULL,
    session_id        TEXT,
    referrer          TEXT,
    clicked_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Scrape run log (so a flaky day on one store doesn't silently kill the pipeline).
CREATE TABLE IF NOT EXISTS scrape_runs (
    id            BIGSERIAL PRIMARY KEY,
    store_name    TEXT NOT NULL,
    started_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    finished_at   TIMESTAMPTZ,
    status        TEXT NOT NULL DEFAULT 'running',  -- running | success | partial | failed
    items_scraped INT NOT NULL DEFAULT 0,
    items_matched INT NOT NULL DEFAULT 0,
    error         TEXT
);
CREATE INDEX IF NOT EXISTS scrape_runs_store_time_idx ON scrape_runs (store_name, started_at DESC);

-- is_sponsored promoted out of the raw JSONB payload so search never needs to
-- load raw (deferred in the ORM; ~3x the rest of the row, egress fix Jul 2026).
-- The backfill's WHERE guard keeps re-runs cheap (idempotent, no row rewrites).
ALTER TABLE store_products ADD COLUMN IF NOT EXISTS is_sponsored BOOLEAN NOT NULL DEFAULT FALSE;
UPDATE store_products
SET is_sponsored = COALESCE((raw->>'sponsored')::boolean, FALSE)
WHERE is_sponsored IS DISTINCT FROM COALESCE((raw->>'sponsored')::boolean, FALSE);

-- Row Level Security: the app never uses Supabase's auto-generated Data API
-- (PostgREST) — the backend connects directly as the table owner, which RLS
-- does not restrict. Enabling RLS with no policies closes the Data API surface
-- (anon/authenticated roles get denied by default) without affecting the app.
-- Dynamic so new tables added above are covered on the next migrate run.
DO $$
DECLARE t RECORD;
BEGIN
    FOR t IN SELECT tablename FROM pg_tables WHERE schemaname = 'public' LOOP
        EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY', t.tablename);
    END LOOP;
END $$;
