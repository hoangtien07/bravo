"""Database reachability helpers shared by integration tests."""
from __future__ import annotations

import asyncio
from functools import lru_cache


def _asyncpg_dsn() -> str:
    from app.config import get_settings
    return get_settings().database_url.replace("postgresql+asyncpg://", "postgresql://", 1)


@lru_cache(maxsize=1)
def db_available() -> bool:
    import asyncpg

    async def check() -> bool:
        try:
            # CI/local developer runs must skip unavailable Postgres quickly rather than
            # spending the driver default timeout once for every DB-marked test module.
            connection = await asyncpg.connect(_asyncpg_dsn(), timeout=2)
            await connection.close()
            return True
        except Exception:
            return False

    return asyncio.run(check())
