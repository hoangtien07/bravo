"""W2.2/2.3 — AgentRun durable: persist + paused_for_approval + complete-on-approval.

DB integration (skip nếu Postgres không reachable).
"""
from __future__ import annotations

import asyncio
import uuid

import pytest
from sqlalchemy import delete

from app.agent import runs
from app.database.models import AgentRun, Draft
from app.erp import draft_queue
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


def _factory():
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
    from sqlalchemy.pool import NullPool

    from app.config import get_settings

    engine = create_async_engine(get_settings().database_url, poolclass=NullPool)
    return engine, async_sessionmaker(engine, expire_on_commit=False)


def test_run_persist_pause_and_complete_on_approval():
    run_id = uuid.uuid4()

    async def run():
        from sqlalchemy import select

        from app.database.models import Employee
        engine, factory = _factory()
        async with factory() as db:
            # created_by/actor_id là FK -> dùng employee đã seed (maker ≠ approver, maker-checker).
            maker = (await db.execute(select(Employee.id).where(
                Employee.email == "ketoan@bravo.vn"))).scalar_one()
            approver = (await db.execute(select(Employee.id).where(
                Employee.email == "giamdoc@bravo.vn"))).scalar_one()
            try:
                # 1) persist run (running) -> 2) paused_for_approval
                await runs.start_run(db, run_id=run_id, session_id=uuid.uuid4(), employee_id=maker)
                got = await db.get(AgentRun, run_id)
                assert got.status == "running"
                await runs.finish_run(db, run_id, status="paused_for_approval",
                                      checkpoint_state={"created_draft": True})

                # 3) draft của run, người KHÁC duyệt -> complete_on_approval -> run 'done'
                maker_department = uuid.uuid4()
                draft = await draft_queue.create_draft(
                    db, Identity(employee_id=maker, department_ids=[maker_department],
                                 permissions=frozenset({"draft:create:own_dept"})),
                    kind="journal_entry",
                    payload={
                        "invoice": {},
                        "lines": [
                            {"account": "156", "debit": "1"},
                            {"account": "331", "credit": "1"},
                        ],
                        "total_debit": "1", "total_credit": "1",
                    },
                    agent_run_id=run_id,
                )
                approved = await draft_queue.approve_draft(
                    db, Identity(employee_id=approver, department_ids=[],
                                 permissions=frozenset({"draft:approve:all"}), is_admin=True),
                    draft.id)
                assert approved.status == "approved"
                run_after = await db.get(AgentRun, run_id)
                assert run_after.status == "done", "duyệt draft phải hoàn tất AgentRun (W2.3)"
            finally:
                await db.execute(delete(Draft).where(Draft.agent_run_id == run_id))
                await db.execute(delete(AgentRun).where(AgentRun.id == run_id))
                await db.commit()
        await engine.dispose()

    asyncio.run(run())
