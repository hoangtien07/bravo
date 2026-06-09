"""Background worker (arq) — heavy/async ingestion off the request path.

A separate process (docker-compose `worker`) so on-prem deploy stays simple: one
monolith API + one worker + Postgres + LLM server (ADR-0007).
"""
from __future__ import annotations

import uuid

from app.config import get_settings
from app.database import async_session_factory
from app.ingestion.pipeline import ingest_source

_settings = get_settings()


async def ingest_task(ctx, source_id: str, path: str) -> int:
    async with async_session_factory() as db:
        return await ingest_source(db, uuid.UUID(source_id), path)


class WorkerSettings:
    functions = [ingest_task]
    redis_settings = None  # parsed from REDIS_URL at deploy

    @staticmethod
    def get_redis_url() -> str:
        return _settings.redis_url
