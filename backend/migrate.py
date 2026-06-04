"""Database migration script for production.

Reads connection URL from DATABASE_URL env var, applies sync-to-async conversions,
and executes all SQL commands in migrations/001_initial.sql.
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys

from sqlalchemy.ext.asyncio import create_async_engine

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def get_db_url() -> str:
    url = os.getenv("DATABASE_URL")
    if not url:
        logger.error("DATABASE_URL environment variable is not set")
        sys.exit(1)
    
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
        async with engine.begin() as conn:
            logger.info("Accessing raw connection...")
            dbapi_conn = await conn.get_raw_connection()
            # Retrieve the underlying raw asyncpg Connection object from the wrapper
            raw_conn = dbapi_conn.driver_connection
            logger.info("Executing migration SQL raw...")
            await raw_conn.execute(sql_content)
        logger.info("Migrations completed successfully")
    except Exception as e:
        logger.exception("Migration failed:")
        sys.exit(1)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(run_migrations())
