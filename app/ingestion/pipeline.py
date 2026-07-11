"""Ingestion pipeline: parse -> chunk -> embed -> store (with scope for RLS).

Each chunk is tagged with the source's department_ids so RLS-on-vector can filter in
the query later (findings/J). Resumability (docsgpt pattern) is a Phase 1B TODO.
"""
from __future__ import annotations

import uuid

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Chunk, Department, Source, SourceDepartment
from app.ingestion.chunker import chunk as chunk_blocks
from app.ingestion.parser import detect_kind, parse
from app.rag.embedding import embed
from app.security.sensitivity import ingest_sensitive


async def ingest_source(
    db: AsyncSession,
    source_id: uuid.UUID,
    path: str,
    source_extra: dict | None = None,
    trusted_knowledge_type: str | None = None,
) -> int:
    """Ingest one source file. Returns number of chunks stored.

    ``Source.knowledge_type`` can be caller display metadata. Only a trusted corpus
    caller may provide ``trusted_knowledge_type`` for cloud-eligible classification.
    """
    source = await db.get(Source, source_id)
    if source is None:
        raise ValueError(f"Source {source_id} not found")
    # Explicit query (avoid lazy relationship load in async context). Empty => global.
    dept_ids = list((await db.execute(
        select(SourceDepartment.department_id).where(SourceDepartment.source_id == source_id)
    )).scalars().all())

    # Re-index idempotent: xoá chunk cũ của source TRƯỚC khi nạp lại (tránh nhân đôi chunk
    # khi ingest lại — deep-dive: pipeline cũ chỉ add, freshness=0).
    await db.execute(delete(Chunk).where(Chunk.source_id == source_id))

    kind = detect_kind(path)
    blocks = parse(path)
    # Text-PDFs: re-segment per-page blocks into heading-bounded sections (better
    # retrieval + section-level citations). Docling kinds (pdf_table/docx/xlsx) already
    # emit semantic blocks with their own provenance — pass straight to the chunker so
    # tables stay whole (is_table) and sheet/cell provenance is preserved.
    if kind == "pdf_text":
        from app.ingestion.heading_chunker import heading_chunk
        blocks = heading_chunk(blocks)  # section-level chunks (heading + start page)
    blocks = chunk_blocks(blocks)       # split over-long sections + drop tiny ones

    # Egress-guard (invariant #4, fail-closed): nguồn nhạy (loại tri thức/phòng ban nhạy) HOẶC
    # 'không rõ scope' (global + không knowledge_type) -> embed LOCAL (raise nếu provider cloud).
    # Quyết định tập trung ở sensitivity.ingest_sensitive (thuần, test được).
    touches_sensitive_dept = False
    if dept_ids:
        n_sensitive = (await db.execute(
            select(func.count()).select_from(Department)
            .where(Department.id.in_(dept_ids), Department.sensitive.is_(True))
        )).scalar() or 0
        touches_sensitive_dept = n_sensitive > 0
    is_sensitive = ingest_sensitive(
        trusted_knowledge_type, has_departments=bool(dept_ids),
        touches_sensitive_dept=touches_sensitive_dept)
    vectors = embed([b.text for b in blocks], sensitive=is_sensitive)

    for b, vec in zip(blocks, vectors, strict=True):
        extra = dict(source_extra or {})
        extra.update(b.extra or {})
        extra["is_sensitive"] = is_sensitive
        db.add(Chunk(
            source_id=source.id, content=b.text, embedding=vec,
            page_number=b.page_number, sheet_name=b.sheet_name, cell_range=b.cell_range,
            heading_path=b.heading_path, is_table=b.is_table, extra=extra,
            department_ids=dept_ids,
        ))
    source.status = "ready"
    await db.commit()
    return len(blocks)
