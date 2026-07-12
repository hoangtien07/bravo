"""Background worker (arq) — heavy/async ingestion off the request path.

A separate process (docker-compose `worker`) so on-prem deploy stays simple: one
monolith API + one worker + Postgres + LLM server (ADR-0007).
"""
from __future__ import annotations

import uuid

from app.config import get_settings
from app.database import async_session_factory
from app.ingestion.pipeline import ingest_source
from app.queue import redis_settings

_settings = get_settings()


async def ingest_task(ctx, source_id: str, path: str) -> int:
    async with async_session_factory() as db:
        return await ingest_source(db, uuid.UUID(source_id), path)


async def attachment_extract_task(ctx, attachment_id: str) -> str:
    """Extract text (or RAG-fallback for oversized) for a chat attachment (Track 3)."""
    from app.ingestion.attachments import extract_attachment

    async with async_session_factory() as db:
        return await extract_attachment(db, uuid.UUID(attachment_id))


class WorkerSettings:
    functions = [ingest_task, attachment_extract_task]
    redis_settings = redis_settings()
