"""v2 Track 2 — RLS personal-tier isolation (the security-critical test for the workspace).

A user's PERSONAL upload must never leak to their department or to anyone else via the old
"empty departments == global" rule. Verified against the real SQL predicates on Postgres.
"""
from __future__ import annotations

import asyncio
import uuid

import pytest

from app.security.rls import (
    Identity,
    chunk_scope_filter,
    resolve_source_visibility,
    source_scope_filter,
)


# --- pure write-scope matrix (no DB) ------------------------------------------------ #
def _ident(*, depts=(), perms=(), admin=False) -> Identity:
    return Identity(employee_id=uuid.uuid4(), department_ids=list(depts),
                    permissions=frozenset(perms), is_admin=admin)


def test_personal_visibility_allowed_for_bare_user():
    u = _ident()  # no create permission at all
    vis, depts, owner = resolve_source_visibility(u, "personal")
    assert vis == "personal" and depts == [] and owner == u.employee_id


def test_personal_cannot_carry_departments():
    with pytest.raises(ValueError):
        resolve_source_visibility(_ident(), "personal", [uuid.uuid4()])


def test_global_requires_publish_capability():
    with pytest.raises(PermissionError):
        resolve_source_visibility(_ident(perms={"doc:create:own_dept"}), "global")
    vis, depts, owner = resolve_source_visibility(_ident(perms={"doc:create:all"}), "global")
    assert vis == "global" and depts == [] and owner is None


def test_department_requires_own_dept_and_stays_in_scope():
    d = uuid.uuid4()
    vis, depts, owner = resolve_source_visibility(
        _ident(depts=[d], perms={"doc:create:own_dept"}), "department", [d])
    assert vis == "department" and depts == [d] and owner is None
    with pytest.raises(PermissionError):
        resolve_source_visibility(_ident(depts=[d], perms={"doc:create:own_dept"}),
                                  "department", [uuid.uuid4()])


# --- DB integration: real predicate on chunks/sources ------------------------------- #
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

_DIM = __import__("app.config", fromlist=["get_settings"]).get_settings().embedding_dim
_VEC = [0.1] * _DIM


def _factory():
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
    from sqlalchemy.pool import NullPool
    from app.config import get_settings
    eng = create_async_engine(get_settings().database_url, poolclass=NullPool)
    return eng, async_sessionmaker(eng, expire_on_commit=False)


async def _seed_source(db, *, visibility, owner_id=None, dept_ids=(), tag):
    from app.database.models import Chunk, Source, SourceDepartment
    src = Source(filename=f"{tag}.txt", knowledge_type="guide", status="ready",
                 visibility=visibility, owner_id=owner_id)
    db.add(src)
    await db.flush()
    for d in dept_ids:
        db.add(SourceDepartment(source_id=src.id, department_id=d))
    db.add(Chunk(source_id=src.id, content=f"{tag} secret body", embedding=_VEC,
                 department_ids=list(dept_ids), visibility=visibility, owner_id=owner_id,
                 extra={}))
    await db.commit()
    return src.id


@pytestmark_db
def test_personal_chunk_not_visible_to_same_department_peer():
    from sqlalchemy import func, select
    from app.database.models import Chunk, Source

    async def run():
        eng, factory = _factory()
        dept = uuid.uuid4()
        alice = Identity(employee_id=uuid.uuid4(), department_ids=[dept],
                         permissions=frozenset({"doc:read:own_dept"}))
        bob = Identity(employee_id=uuid.uuid4(), department_ids=[dept],
                       permissions=frozenset({"doc:read:own_dept"}))
        tag = f"pers-{uuid.uuid4().hex}"
        gtag = f"glob-{uuid.uuid4().hex}"
        try:
            async with factory() as db:
                await _seed_source(db, visibility="personal", owner_id=alice.employee_id, tag=tag)
                await _seed_source(db, visibility="global", tag=gtag)

            async def visible_chunk_tags(ident):
                async with factory() as db:
                    rows = (await db.execute(
                        select(Chunk.content).where(chunk_scope_filter(ident))
                    )).scalars().all()
                    return {r.split()[0] for r in rows}

            alice_sees = await visible_chunk_tags(alice)
            bob_sees = await visible_chunk_tags(bob)
            # Alice sees her personal chunk + global; Bob sees only global.
            assert tag in alice_sees and gtag in alice_sees
            assert tag not in bob_sees, "LEAK: personal chunk visible to department peer"
            assert gtag in bob_sees

            # Source-level list isolation mirrors chunk isolation.
            async def visible_source_files(ident):
                async with factory() as db:
                    rows = (await db.execute(
                        select(Source.filename).where(source_scope_filter(ident))
                    )).scalars().all()
                    return set(rows)

            assert f"{tag}.txt" in await visible_source_files(alice)
            assert f"{tag}.txt" not in await visible_source_files(bob)
        finally:
            # Cleanup seeded rows.
            async with factory() as db:
                await db.execute(sa_del := __import__("sqlalchemy").delete(Chunk).where(
                    Chunk.content.like("pers-%") | Chunk.content.like("glob-%")))
                await db.execute(__import__("sqlalchemy").delete(Source).where(
                    Source.filename.like("pers-%") | Source.filename.like("glob-%")))
                await db.commit()
            await eng.dispose()

    asyncio.run(run())


@pytestmark_db
def test_permissionless_user_still_reads_own_personal_files():
    from sqlalchemy import select
    from app.database.models import Chunk

    async def run():
        eng, factory = _factory()
        # A bare end-user with NO doc:read permission at all.
        user = Identity(employee_id=uuid.uuid4(), department_ids=[], permissions=frozenset())
        tag = f"pers-{uuid.uuid4().hex}"
        try:
            async with factory() as db:
                await _seed_source(db, visibility="personal", owner_id=user.employee_id, tag=tag)
            async with factory() as db:
                rows = (await db.execute(
                    select(Chunk.content).where(chunk_scope_filter(user))
                )).scalars().all()
            assert any(tag in r for r in rows), "bare user cannot read their own personal file"
        finally:
            async with factory() as db:
                await db.execute(__import__("sqlalchemy").delete(Chunk).where(
                    Chunk.content.like("pers-%")))
                from app.database.models import Source
                await db.execute(__import__("sqlalchemy").delete(Source).where(
                    Source.filename.like("pers-%")))
                await db.commit()
            await eng.dispose()

    asyncio.run(run())
