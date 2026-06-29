"""Database migration script for production.

Reads connection URL from DATABASE_URL env var, applies sync-to-async conversions,
and executes all SQL commands in migrations/001_initial.sql.
"""

from __future__ import annotations

import asyncio
import logging
import os
import socket
import sys

from dotenv import load_dotenv

load_dotenv()

from sqlalchemy.ext.asyncio import create_async_engine

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def fatal_db_hint(exc: Exception) -> str | None:
    """Return a human explanation if `exc` is a DB error that retrying won't fix.

    Transient errors (the DB is still booting, a brief network blip) are worth
    retrying. DNS failures, a paused project, or bad credentials are not — they
    need a config change, so we should fail fast instead of looping 20 times.
    """
    msg = str(exc).lower()

    if isinstance(exc, socket.gaierror) or any(
        s in msg for s in ("enotfound", "getaddrinfo", "name or service not known",
                            "could not translate host name", "nodename nor servname")
    ):
        return ("Could not resolve the database host (DNS lookup failed). Verify the "
                "host in DATABASE_URL is correct and the database is provisioned.")

    if "tenant" in msg and "not found" in msg:
        return ("The pooler reports the tenant/user was not found. On Supabase free tier "
                "this almost always means the PROJECT IS PAUSED — resume it in the Supabase "
                "dashboard, then redeploy. Otherwise double-check DATABASE_URL.")

    if "password authentication failed" in msg:
        return "Password authentication failed — check the credentials in DATABASE_URL."

    return None


def get_db_url() -> str:
    url = os.getenv("DATABASE_URL")
    if not url:
        logger.error("DATABASE_URL environment variable is not set")
        sys.exit(1)

    # Strip stray whitespace/newlines — a trailing newline pasted into the env
    # var ends up inside the database name (e.g. "postgres\n") and the connection
    # is rejected with InvalidCatalogNameError.
    url = url.strip()

    # Rewrite sync to async connection strings for SQLAlchemy + asyncpg
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://") and not url.startswith("postgresql+asyncpg://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


async def run_migrations() -> None:
    db_url = get_db_url()

    # Locate initial migrations sql file
    script_dir = os.path.dirname(os.path.abspath(__file__))
    sql_path = os.path.join(script_dir, "migrations", "001_initial.sql")

    if not os.path.exists(sql_path):
        logger.error(f"Migration script not found at: {sql_path}")
        sys.exit(1)

    logger.info(f"Reading migrations from: {sql_path}")
    with open(sql_path, "r", encoding="utf-8") as f:
        sql_content = f.read()

    # Create async engine and execute SQL statements
    logger.info("Connecting to the database...")
    engine = create_async_engine(db_url, future=True)

    try:
        max_retries = 20
        retry_delay = 3
        connected = False

        for attempt in range(1, max_retries + 1):
            try:
                async with engine.begin() as conn:
                    logger.info("Accessing raw connection...")
                    dbapi_conn = await conn.get_raw_connection()
                    # Retrieve the underlying raw asyncpg Connection object from the wrapper
                    raw_conn = dbapi_conn.driver_connection
                    logger.info("Executing migration SQL raw...")
                    await raw_conn.execute(sql_content)
                connected = True
                logger.info("Migrations completed successfully")
                break
            except Exception as e:
                hint = fatal_db_hint(e)
                if hint:
                    logger.error(
                        "Database is unreachable and retrying will not help.\n"
                        "  -> %s\n  Underlying error: %s",
                        hint, e,
                    )
                    sys.exit(1)
                logger.warning(f"Database connection attempt {attempt}/{max_retries} failed: {e}")
                if attempt == max_retries:
                    logger.exception("Migration failed after maximum retries:")
                    sys.exit(1)
                await asyncio.sleep(retry_delay)

        if connected:
            # Run seeding automatically
            logger.info("Running database seeding...")
            try:
                from app.database import dispose as dispose_db
                from seed.seed_data import seed
                await seed()
                await dispose_db()
                logger.info("Seeding completed successfully")
            except Exception as seed_err:
                logger.error(f"Seeding failed: {seed_err}")
                # Do not fail the whole migration if just seeding fails, but log it
    except Exception:
        logger.exception("Migration failed:")
        sys.exit(1)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(run_migrations())
