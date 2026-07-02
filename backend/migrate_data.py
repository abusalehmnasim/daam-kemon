"""Script to migrate all data from the source (Render) database to the target (Supabase) database.

Reads:
  - SOURCE_DATABASE_URL: Connection URL for Render database (defaults to the DATABASE_URL in .env)
  - TARGET_DATABASE_URL: Connection URL for Supabase database
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from urllib.parse import urlparse

from dotenv import load_dotenv
from sqlalchemy import MetaData, Table, text
from sqlalchemy.ext.asyncio import create_async_engine

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# List of tables to migrate in dependency order
TABLES = [
    "stores",
    "products",
    "store_products",
    "price_history",
    "baskets",
    "outbound_clicks",
    "scrape_runs"
]

def _host_label(url: str) -> str:
    """host:port/db with the password stripped — safe to log."""
    p = urlparse(url)
    return f"{p.hostname or '?'}:{p.port or ''}{p.path or ''}"


def clean_url(url: str | None) -> str:
    if not url:
        logger.error("Database connection URL is empty")
        sys.exit(1)
    # Rewrite sync to async connection strings for SQLAlchemy + asyncpg
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://") and not url.startswith("postgresql+asyncpg://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url

async def migrate_table(source_conn, target_conn, metadata, table_name: str):
    logger.info(f"Migrating table '{table_name}'...")

    # 1. Fetch data from source
    source_result = await source_conn.execute(text(f"SELECT * FROM {table_name}"))
    columns = source_result.keys()
    rows = [dict(zip(columns, row, strict=True)) for row in source_result.fetchall()]

    if not rows:
        logger.info(f"Table '{table_name}' is empty. Skipping.")
        return

    logger.info(f"Fetched {len(rows)} rows from source table '{table_name}'")

    # 2. Clear target table (just in case)
    await target_conn.execute(text(f"TRUNCATE TABLE {table_name} CASCADE"))

    # 3. Get reflected Table object
    table_obj = Table(table_name, metadata)

    # 4. Insert data in chunks to prevent memory/connection issues
    chunk_size = 500
    for i in range(0, len(rows), chunk_size):
        chunk = rows[i:i + chunk_size]
        await target_conn.execute(table_obj.insert(), chunk)

    logger.info(f"Successfully inserted {len(rows)} rows into target table '{table_name}'")

    # 5. Reset primary key sequence if table has a serial/bigserial id column
    # Exception: 'stores' uses 'name' as primary key, not a sequence
    if table_name != "stores":
        seq_query = text(f"""
            SELECT setval(
                pg_get_serial_sequence('{table_name}', 'id'),
                COALESCE((SELECT MAX(id) FROM {table_name}), 1)
            )
        """)
        await target_conn.execute(seq_query)
        logger.info(f"Reset sequence for target table '{table_name}'")

async def main():
    source_raw = os.getenv("SOURCE_DATABASE_URL") or os.getenv("DATABASE_URL")
    target_raw = os.getenv("TARGET_DATABASE_URL")

    if not source_raw:
        logger.error("SOURCE_DATABASE_URL or DATABASE_URL not set in environment or .env file")
        sys.exit(1)

    if not target_raw:
        logger.error("TARGET_DATABASE_URL environment variable is not set. Please supply the Supabase connection string.")
        sys.exit(1)

    source_url = clean_url(source_raw)
    target_url = clean_url(target_raw)

    source_host = _host_label(source_url)
    target_host = _host_label(target_url)
    target_hostname = urlparse(target_url).hostname or ""

    # Never truncate the database we're reading from.
    if source_host == target_host:
        logger.error(
            "SOURCE and TARGET are the same database (%s). Aborting — this would "
            "TRUNCATE the very data being copied.", target_host,
        )
        sys.exit(1)

    logger.info("Initializing database engines...")
    source_engine = create_async_engine(source_url, future=True)
    target_engine = create_async_engine(target_url, future=True)

    metadata = MetaData()

    try:
        # --- Preflight: show exactly what will be destroyed, then require an
        # explicit confirmation. This script TRUNCATEs every target table with
        # CASCADE; a swapped/leftover TARGET_DATABASE_URL would otherwise wipe
        # production silently. ---
        async with target_engine.connect() as pre:
            counts: dict[str, object] = {}
            for t in TABLES:
                try:
                    # t comes from the hardcoded TABLES list, never user input.
                    r = await pre.execute(text(f"SELECT COUNT(*) FROM {t}"))
                    counts[t] = r.scalar_one()
                except Exception:
                    counts[t] = "(missing)"
        total = sum(v for v in counts.values() if isinstance(v, int))

        logger.warning("DESTRUCTIVE data migration — review carefully:")
        logger.warning("  FROM (source): %s", source_host)
        logger.warning("  TO   (target): %s   <-- will be OVERWRITTEN", target_host)
        for t in TABLES:
            logger.warning("    TRUNCATE %-16s (%s existing rows destroyed)", t, counts[t])

        confirmed = "--yes" in sys.argv or os.getenv("CONFIRM_TARGET_HOST") == target_hostname
        if not confirmed:
            logger.error(
                "Refusing to proceed without confirmation. This will destroy %s rows in "
                "%s. Re-run with --yes, or set CONFIRM_TARGET_HOST=%s to confirm.",
                total, target_host, target_hostname,
            )
            sys.exit(1)

        async with source_engine.connect() as source_conn, target_engine.begin() as target_conn:
            logger.info("Database connections established.")
            logger.info("Reflecting target database schema...")
            await target_conn.run_sync(metadata.reflect)
            logger.info("Schema reflected successfully.")

            for table in TABLES:
                await migrate_table(source_conn, target_conn, metadata, table)
            logger.info("All tables migrated successfully!")
    except Exception:
        logger.exception("Migration failed:")
        sys.exit(1)
    finally:
        await source_engine.dispose()
        await target_engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
