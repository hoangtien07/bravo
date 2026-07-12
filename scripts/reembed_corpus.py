"""Q5 — re-embed every existing Source in place (idempotent).

Run after changing the embedding model OR after a chunker/heading-aware-embedding change so the
whole corpus is re-vectorized consistently. Each source is re-ingested via ingest_source, which
deletes its old chunks first, so this is safe to re-run.

CAVEAT (dimension change): if the NEW embedding model has a different dimension than the DB
`chunks.embedding` Vector column, you must run an Alembic migration that alters the column (and
`archival_passages.embedding`) BEFORE this script — re-embedding alone won't resize the column.
Truncating a 3072-d model to 1536 (OpenAI/Gemini MRL) avoids the migration.

Usage: python -m scripts.reembed_corpus [--dry-run]
"""
from __future__ import annotations

import asyncio
import sys

from sqlalchemy import select

from app.api.routes_sources import _locate_source_file
from app.database import async_session_factory
from app.database.models import Source
from app.ingestion.pipeline import ingest_source


async def reembed(dry_run: bool = False) -> tuple[int, int]:
    ok = missing = 0
    async with async_session_factory() as db:
        sources = list((await db.execute(select(Source))).scalars().all())
        for src in sources:
            path = _locate_source_file(src)
            if path is None:
                print(f"  SKIP (no file): {src.filename}")
                missing += 1
                continue
            if dry_run:
                print(f"  would re-embed: {src.filename} [{src.visibility}]")
                ok += 1
                continue
            try:
                n = await ingest_source(db, src.id, str(path),
                                        trusted_knowledge_type=src.knowledge_type)
                print(f"  ok {src.filename}: {n} chunks")
                ok += 1
            except Exception as exc:  # noqa: BLE001
                print(f"  FAIL {src.filename}: {exc}")
                missing += 1
    return ok, missing


def main() -> int:
    dry = "--dry-run" in sys.argv
    ok, bad = asyncio.run(reembed(dry_run=dry))
    print(f"re-embed done: {ok} ok, {bad} skipped/failed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
