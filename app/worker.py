"""Background worker (arq) — heavy/async ingestion off the request path.

A separate process (docker-compose `worker`) so on-prem deploy stays simple: one
monolith API + one worker + Postgres + LLM server (ADR-0007).
"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from arq.cron import cron

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


async def consultant_gap_curation_task(ctx) -> dict[str, int | str]:
    """Hourly, internal-only gap clustering for the review queue.

    The job is opt-in and produces review-required candidate briefs only. It deliberately has
    no provider credential, no raw conversation payload, and no activation/index side effect.
    """
    if not _settings.consultant_curation_enabled:
        return {"status": "disabled", "created": 0}
    from app.consultant.jobs import create_candidates_from_open_gaps

    async with async_session_factory() as db:
        created = await create_candidates_from_open_gaps(
            db, limit=_settings.consultant_curation_max_gaps)
    return {"status": "review_required", "created": created}


async def consultant_state_retention_task(ctx) -> dict[str, int | str]:
    """Purge only expired Consultant task-state blocks after an explicit policy opt-in.

    It never touches transcript, attachments, archival memory, evidence, or orphan sessions.
    A conversation must be inactive past the policy cutoff, so unfinished active work cannot be
    erased by a scheduler race. The caller must separately approve the duration and backup/erase
    semantics through the release gate.
    """
    if not _settings.consultant_state_retention_enabled:
        return {"status": "disabled", "deleted": 0}
    from sqlalchemy import delete, select

    from app.database.models import Conversation, MemoryBlock

    cutoff = datetime.now(UTC) - timedelta(days=_settings.consultant_state_retention_days)
    inactive_sessions = select(Conversation.id).where(Conversation.last_message_at < cutoff)
    async with async_session_factory() as db:
        result = await db.execute(delete(MemoryBlock).where(
            MemoryBlock.label == "consultant_task_state/v1",
            MemoryBlock.updated_at < cutoff,
            MemoryBlock.session_id.in_(inactive_sessions),
        ))
        await db.commit()
    return {"status": "purged_task_state_only", "deleted": int(result.rowcount or 0)}


async def _on_startup(ctx) -> None:
    """P0.5: the worker performs egress-relevant work (cloud embedding during ingest), so it must
    pass the SAME fail-closed boot-guard as the API — previously only app.main called it, leaving
    the worker able to boot with default creds / misconfigured egress."""
    get_settings().validate_boot()


class WorkerSettings:
    functions = [ingest_task, attachment_extract_task, consultant_gap_curation_task,
                 consultant_state_retention_task]
    on_startup = _on_startup
    # ARQ runs this on the hour. The config gate defaults to disabled, so merely starting the
    # worker does not create candidates until an owner explicitly enables internal curation.
    cron_jobs = [cron(consultant_gap_curation_task, minute=0),
                 cron(consultant_state_retention_task, hour=3, minute=17)]
    redis_settings = redis_settings()
