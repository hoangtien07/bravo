"""Database reachability helpers shared by integration tests."""
from __future__ import annotations

import asyncio


def _asyncpg_dsn() -> str:
    from app.config import get_settings
    return get_settings().database_url.replace("postgresql+asyncpg://", "postgresql://", 1)


def db_available() -> bool:
    import asyncpg

    async def check() -> bool:
        try:
            connection = await asyncpg.connect(_asyncpg_dsn())
            await connection.close()
            return True
        except Exception:
            return False

    return asyncio.run(check())
