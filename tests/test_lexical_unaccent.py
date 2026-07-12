"""Lexical search accent-insensitive (migration 0008 unaccent).

Regression: người dùng VN gõ KHÔNG dấu ("cach len bao cao can doi phat sinh") —
tsquery so khớp thô trượt hết nội dung có dấu -> retrieval nhiễu -> agent
abstain/clarify sai trong khi corpus CÓ nội dung. unaccent hoá 2 phía sửa điều đó;
câu có dấu phải giữ nguyên hành vi.
"""
from __future__ import annotations

import asyncio
import uuid

import pytest

from app.security.rls import Identity


def _db_available() -> bool:
    import asyncpg

    async def check() -> bool:
        try:
            conn = await asyncpg.connect("postgresql://bravo:bravo@localhost:5432/bravo")
            await conn.close()
            return True
        except Exception:
            return False

    return asyncio.run(check())


pytestmark = pytest.mark.skipif(not _db_available(), reason="Postgres not reachable")

_MARK = "UNACCENTREGRESSION"


def test_lexical_matches_unaccented_query_against_accented_content():
    async def run() -> None:
        from sqlalchemy import delete
        from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
        from sqlalchemy.pool import NullPool

        from app.config import get_settings
        from app.database.models import Chunk, Source
        from app.rag.retriever import lexical_search

        engine = create_async_engine(get_settings().database_url, poolclass=NullPool)
        factory = async_sessionmaker(engine, expire_on_commit=False)
        # perm phải có SCOPE (doc:read:all) — perm thô "doc:read" bị chunk_scope_filter deny.
        ident = Identity(employee_id=uuid.uuid4(), department_ids=[],
                         permissions=frozenset({"doc:read:all"}))
        src_id = None
        try:
            async with factory() as db:
                src = Source(filename=f"{_MARK}.md", knowledge_type="test", status="ready")
                db.add(src)
                await db.flush()
                src_id = src.id
                # embedding zeros: lexical không đụng vector; chunk GLOBAL (dept rỗng).
                db.add(Chunk(
                    source_id=src.id,
                    content=f"Hướng dẫn lên bảng cân đối phát sinh {_MARK}",
                    embedding=[0.0] * 1536, department_ids=[], extra={},
                ))
                await db.commit()

                # KHÔNG dấu -> vẫn phải khớp nội dung CÓ dấu
                hits = await lexical_search(db, ident, f"bang can doi phat sinh {_MARK}", k=10)
                assert any(_MARK in h.content for h in hits), "unaccented query must match"
                # CÓ dấu -> hành vi cũ giữ nguyên
                hits2 = await lexical_search(db, ident, f"bảng cân đối phát sinh {_MARK}", k=10)
                assert any(_MARK in h.content for h in hits2), "accented query must still match"
        finally:
            async with factory() as db:
                if src_id is not None:
                    await db.execute(delete(Chunk).where(Chunk.source_id == src_id))
                    await db.execute(delete(Source).where(Source.id == src_id))
                    await db.commit()
            await engine.dispose()

    asyncio.run(run())
