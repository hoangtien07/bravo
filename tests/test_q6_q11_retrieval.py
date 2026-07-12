"""Q6 (section expansion) + Q11 (per-model min_score) retrieval tests."""
from __future__ import annotations

import asyncio
import uuid

import pytest

from app.config import get_settings
from app.rag import retriever
from app.rag.retriever import Retrieved
from app.security.rls import Identity


# --- Q11: per-model min_score resolver (pure) --------------------------------------- #
def test_resolved_min_score_known_and_unknown(monkeypatch):
    s = get_settings()
    monkeypatch.setattr(s, "embedding_model", "text-embedding-3-small")
    assert s.resolved_min_score() == 0.12
    monkeypatch.setattr(s, "embedding_model", "some-future-model")
    monkeypatch.setattr(s, "retrieval_min_score", 0.33)
    assert s.resolved_min_score() == 0.33   # falls back to the flat setting


# --- Q6: section expansion (DB) ----------------------------------------------------- #
def _db_available() -> bool:
    import asyncpg

    async def _check():
        try:
            conn = await asyncpg.connect("postgresql://bravo:bravo@localhost:5432/bravo")
            await conn.close()
            return True
        except Exception:
            return False

    return asyncio.run(_check())


pytestmark_db = pytest.mark.skipif(not _db_available(), reason="Postgres not reachable")
_DIM = get_settings().embedding_dim


def _factory():
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
    from sqlalchemy.pool import NullPool
    eng = create_async_engine(get_settings().database_url, poolclass=NullPool)
    return eng, async_sessionmaker(eng, expire_on_commit=False)


@pytestmark_db
def test_expand_sections_merges_sibling_chunks():
    from app.database.models import Chunk, Source

    async def run():
        eng, factory = _factory()
        tag = f"sec-{uuid.uuid4().hex}"
        heading = f"{tag} > Quy trình"
        try:
            async with factory() as db:
                src = Source(filename=f"{tag}.docx", knowledge_type="guide", status="ready",
                             visibility="global")
                db.add(src)
                await db.flush()
                for i in range(3):
                    db.add(Chunk(source_id=src.id, content=f"{tag} bước {i}",
                                 embedding=[0.1] * _DIM, department_ids=[], visibility="global",
                                 heading_path=heading, page_number=i, extra={}))
                await db.commit()
                sid = str(src.id)

            hit = Retrieved(chunk_id=str(uuid.uuid4()), content=f"{tag} bước 1", source_id=sid,
                            page_number=1, sheet_name=None, cell_range=None, score=1.0,
                            extra={"heading_path": heading})
            admin = Identity(employee_id=uuid.uuid4(), is_admin=True)
            async with factory() as db:
                out = await retriever.expand_sections(db, admin, [hit], top=6, token_cap=2000)
            # The single hit is expanded to include all 3 sibling chunks of the section.
            assert out[0].content.count(f"{tag} bước") == 3
        finally:
            async with factory() as db:
                from sqlalchemy import delete
                await db.execute(delete(Chunk).where(Chunk.content.like(f"{tag}%")))
                await db.execute(delete(Source).where(Source.filename == f"{tag}.docx"))
                await db.commit()
            await eng.dispose()

    asyncio.run(run())
