"""PostgreSQL regressions for draft object-scope approval and rejection."""
from __future__ import annotations

import asyncio
import uuid

import pytest

from app.erp import draft_queue
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


def _journal_payload() -> dict:
    return {
        "invoice": {},
        "lines": [
            {"account": "156", "debit": "1"},
            {"account": "331", "credit": "1"},
        ],
        "total_debit": "1",
        "total_credit": "1",
    }


def test_approve_and_reject_do_not_bypass_department_scope():
    async def run() -> None:
        from sqlalchemy import delete, select
        from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
        from sqlalchemy.pool import NullPool

        from app.config import get_settings
        from app.database.models import Draft, Employee

        engine = create_async_engine(get_settings().database_url, poolclass=NullPool)
        factory = async_sessionmaker(engine, expire_on_commit=False)
        created_ids: list[uuid.UUID] = []
        try:
            async with factory() as db:
                maker, reviewer = (await db.execute(select(Employee.id).where(
                    Employee.email.in_(["ketoan@bravo.vn", "admin@bravo.vn"])
                ))).scalars().all()
                dept_a, dept_b = uuid.uuid4(), uuid.uuid4()
                maker_identity = Identity(
                    employee_id=maker, department_ids=[dept_a],
                    permissions=frozenset({"draft:create:own_dept"}),
                )
                own_reviewer = Identity(
                    employee_id=reviewer, department_ids=[dept_a],
                    permissions=frozenset({"draft:approve:own_dept"}),
                )
                foreign_reviewer = Identity(
                    employee_id=reviewer, department_ids=[dept_b],
                    permissions=frozenset({"draft:approve:own_dept"}),
                )

                pending = await draft_queue.create_draft(
                    db, maker_identity, "journal_entry", _journal_payload(), department_id=dept_a,
                )
                created_ids.append(pending.id)
                with pytest.raises(ValueError):
                    await draft_queue.approve_draft(db, foreign_reviewer, pending.id)
                await db.rollback()

                approved = await draft_queue.approve_draft(db, own_reviewer, pending.id)
                assert approved.status == "approved"

                pending_reject = await draft_queue.create_draft(
                    db, maker_identity, "journal_entry", _journal_payload(), department_id=dept_a,
                )
                created_ids.append(pending_reject.id)
                with pytest.raises(ValueError):
                    await draft_queue.reject_draft(db, foreign_reviewer, pending_reject.id, "no")
                await db.rollback()

                rejected = await draft_queue.reject_draft(db, own_reviewer, pending_reject.id, "no")
                assert rejected.status == "rejected"
        finally:
            async with factory() as db:
                if created_ids:
                    await db.execute(delete(Draft).where(Draft.id.in_(created_ids)))
                    await db.commit()
            await engine.dispose()

    asyncio.run(run())
