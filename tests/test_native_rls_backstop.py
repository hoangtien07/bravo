"""P0.6 — the native Postgres RLS backstop (migration 0017) actually denies cross-department
rows at the SQL layer once armed, independent of any application WHERE clause.

The migration ships the policy INERT (RLS not enabled). This test arms it inside a transaction
(ENABLE + FORCE ROW LEVEL SECURITY so the table owner is also subject to it), sets the per-identity
GUCs via the shared helper, and asserts a dept-A user sees only dept-A + global chunks — never a
dept-B chunk. The transaction is rolled back, so RLS is never left enabled for other tests.

DB integration (skip w/o Postgres). Requires migration 0017 applied (alembic upgrade head).
"""
from __future__ import annotations

import asyncio
import uuid

import pytest
from sqlalchemy import text

from app.security.native_rls import apply_rls_gucs
from app.security.rls import Identity


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


pytestmark = pytest.mark.skipif(not _db_available(), reason="Postgres not reachable")


def _engine():
    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlalchemy.pool import NullPool

    from app.config import get_settings
    return create_async_engine(get_settings().database_url, poolclass=NullPool)


def test_native_rls_denies_cross_department_when_armed():
    async def run() -> None:
        engine = _engine()
        dept_a, dept_b = uuid.uuid4(), uuid.uuid4()
        src_id = uuid.uuid4()
        c_a, c_b, c_global = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
        try:
            async with engine.connect() as conn:
                trans = await conn.begin()
                # embedding dim is deployment-dependent (1536 cloud / 1024 local) -> build a zero
                # vector of the right size dynamically.
                dim = (await conn.execute(text(
                    "SELECT (regexp_match(format_type(atttypid, atttypmod), '\\((\\d+)\\)'))[1]::int "
                    "FROM pg_attribute WHERE attrelid='chunks'::regclass AND attname='embedding'"
                ))).scalar()
                zero_vec = "[" + ",".join(["0"] * int(dim)) + "]"

                await conn.execute(text(
                    "INSERT INTO sources (id, filename, status, visibility) "
                    "VALUES (:id, 'rls-test.md', 'ready', 'global')"),
                    {"id": src_id})
                ins = text(
                    "INSERT INTO chunks (id, source_id, content, embedding, is_table, extra, "
                    "department_ids, visibility, owner_id) VALUES "
                    "(:id, :src, :content, CAST(:emb AS vector), false, '{}'::jsonb, "
                    ":depts, :vis, :owner)")
                await conn.execute(ins, {"id": c_a, "src": src_id, "content": "dept A doc",
                                         "emb": zero_vec, "depts": [dept_a], "vis": "department",
                                         "owner": None})
                await conn.execute(ins, {"id": c_b, "src": src_id, "content": "dept B doc",
                                         "emb": zero_vec, "depts": [dept_b], "vis": "department",
                                         "owner": None})
                await conn.execute(ins, {"id": c_global, "src": src_id, "content": "global doc",
                                         "emb": zero_vec, "depts": [], "vis": "global",
                                         "owner": None})

                # Arm the backstop for this transaction only.
                await conn.execute(text("ALTER TABLE chunks ENABLE ROW LEVEL SECURITY"))
                await conn.execute(text("ALTER TABLE chunks FORCE ROW LEVEL SECURITY"))

                # The default `bravo` connection is a SUPERUSER, which BYPASSES RLS (exactly the
                # review's finding — the operator cutover must use a non-owner role). Prove the
                # policy by switching to a throwaway non-superuser role for the SELECT.
                await conn.execute(text("CREATE ROLE rls_probe NOSUPERUSER"))
                await conn.execute(text("GRANT SELECT ON chunks TO rls_probe"))

                ident_a = Identity(employee_id=uuid.uuid4(), department_ids=[dept_a],
                                   permissions=frozenset({"doc:read:own_dept"}))
                await apply_rls_gucs(conn, ident_a)
                await conn.execute(text("SET LOCAL ROLE rls_probe"))

                visible = set((await conn.execute(text(
                    "SELECT id FROM chunks WHERE id = ANY(:ids)"),
                    {"ids": [c_a, c_b, c_global]})).scalars().all())

                await conn.execute(text("RESET ROLE"))
                assert c_a in visible, "dept-A user must see the dept-A chunk"
                assert c_global in visible, "global chunk must be visible to everyone"
                assert c_b not in visible, "SQL-layer RLS must hide the dept-B chunk"

                await trans.rollback()   # never leave RLS armed / role / rows persisted
        finally:
            await engine.dispose()

    asyncio.run(run())
