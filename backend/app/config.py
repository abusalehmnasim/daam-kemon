import os
from functools import lru_cache
from dotenv import load_dotenv

load_dotenv()


class Settings:
    @property
    def database_url(self) -> str:
        url = os.getenv(
            "DATABASE_URL",
            "postgresql+asyncpg://daamkemon:daamkemon@localhost:5432/daamkemon",
        ).strip()  # trailing newline in the env var would corrupt the db name
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://") and not url.startswith("postgresql+asyncpg://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url

    @property
    def admin_api_key(self) -> str:
        """Token required by /admin/* endpoints (via the X-Admin-Key header).

        Read live (not cached at import) so tests and deploys can set it
        through the environment. Empty string means "unset"."""
        return os.getenv("ADMIN_API_KEY", "")

    @property
    def environment(self) -> str:
        # Read live so tests / deploys can set it via the environment.
        return os.getenv("ENVIRONMENT", "development")

    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    cors_origins: list[str] = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    # If True, the search service will live-match scraped names against canonical
    # products. False (default) trusts the matcher run at ingest time.
    live_match: bool = os.getenv("LIVE_MATCH", "false").lower() == "true"


@lru_cache(maxsize=1)
def settings() -> Settings:
    return Settings()
