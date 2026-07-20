"""Async job queue (arq) — single seam for enqueuing background work from request handlers.

Ingestion + attachment extraction run off the request path (DOCUMENT-MANAGEMENT.md §3c async
ingest). The API holds one lazily-created arq pool; the worker process (app/worker.py) consumes.

`settings.ingest_sync=True` bypasses the queue and lets callers run the work inline — the
test/dev fallback so the suite runs without a live Redis. Prod keeps it False.
"""
from __future__ import annotations

from arq.connections import RedisSettings, create_pool

from app.config import get_settings

_settings = get_settings()
_pool = None


def redis_settings() -> RedisSettings:
    settings = RedisSettings.from_dsn(_settings.redis_url)
    password = _settings.resolved_redis_password()
    if password:
        settings.password = password
    return settings


async def get_pool():
    """Lazily create (and cache) the shared arq redis pool."""
    global _pool
    if _pool is None:
        _pool = await create_pool(redis_settings())
    return _pool


async def enqueue(function: str, *args, **kwargs):
    """Enqueue a job by function name. Returns the arq Job (or None under ingest_sync)."""
    if _settings.ingest_sync:
        return None
    pool = await get_pool()
    return await pool.enqueue_job(function, *args, **kwargs)
