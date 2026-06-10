"""Ingestion pipeline: parse -> chunk -> embed -> store (with scope for RLS).

Each chunk is tagged with the source's department_ids so RLS-on-vector can filter in
the query later (findings/J). Resumability (docsgpt pattern) is a Phase 1B TODO.
"""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Chunk, Source, SourceDepartment
from app.ingestion.chunker import chunk as chunk_blocks
from app.ingestion.parser import parse
from app.rag.embedding import embed


async def ingest_source(db: AsyncSession, source_id: uuid.UUID, path: str) -> int:
    """Ingest one source file. Returns number of chunks stored."""
    source = await db.get(Source, source_id)
    if source is None:
        raise ValueError(f"Source {source_id} not found")
    # Explicit query (avoid lazy relationship load in async context). Empty => global.
    dept_ids = list((await db.execute(
        select(SourceDepartment.department_id).where(SourceDepartment.source_id == source_id)
    )).scalars().all())

    blocks = chunk_blocks(parse(path))
    vectors = embed([b.text for b in blocks])

    for b, vec in zip(blocks, vectors, strict=True):
        db.add(Chunk(
            source_id=source.id, content=b.text, embedding=vec,
            page_number=b.page_number, sheet_name=b.sheet_name, cell_range=b.cell_range,
            heading_path=b.heading_path, is_table=b.is_table, extra=b.extra,
            department_ids=dept_ids,
        ))
    source.status = "ready"
    await db.commit()
    return len(blocks)
