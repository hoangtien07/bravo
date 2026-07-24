"""P0.4 — consultant task-state writes are compare-and-set, and corrupt persisted state is an
explicit recovery event (audit) rather than a silent empty task.

Regression for the lock-free /agent/ask race: two turns on the same conversation loaded the same
revision and the last writer silently clobbered the other. DB integration (skip w/o Postgres).
"""
from __future__ import annotations

import asyncio
import uuid

import pytest

from app.consultant.contracts import TaskState
from app.consultant.service import ConsultantService, ConsultantStateConflict
from app.security.rls import Identity
from tests.db_support import db_available


pytestmark = pytest.mark.skipif(not db_available(), reason="Postgres not reachable")


def _engine_factory():
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
    from sqlalchemy.pool import NullPool

    from app.config import get_settings
    engine = create_async_engine(get_settings().database_url, poolclass=NullPool)
    return engine, async_sessionmaker(engine, expire_on_commit=False)


def _ident():
    return Identity(employee_id=uuid.uuid4(), department_ids=[uuid.uuid4()],
                    permissions=frozenset({"doc:read"}))


def test_stale_write_raises_conflict():
    async def run() -> None:
        from sqlalchemy import delete
        from app.database.models import MemoryBlock

        engine, factory = _engine_factory()
        sid = uuid.uuid4()
        try:
            async with factory() as db:
                svc = ConsultantService(db, _ident(), sid)
                # Seed revision 1.
                await svc.save_state(TaskState(revision=1), expected_revision=0)
                # A concurrent turn advances it to revision 2 (based on revision 1).
                await svc.save_state(TaskState(revision=2), expected_revision=1)
                # A stale writer still holding revision 1 must be rejected.
                with pytest.raises(ConsultantStateConflict):
                    await svc.save_state(TaskState(revision=99), expected_revision=1)
                # The winner's value is intact.
                loaded = await svc.load_state()
                assert loaded.revision == 2
        finally:
            async with factory() as db:
                await db.execute(delete(MemoryBlock).where(MemoryBlock.session_id == sid))
                await db.commit()
            await engine.dispose()

    asyncio.run(run())


def test_corrupt_state_recovers_and_records_event():
    async def run() -> None:
        from sqlalchemy import delete, select
        from app.database.models import AuditLog, MemoryBlock

        engine, factory = _engine_factory()
        sid = uuid.uuid4()
        ident = _ident()
        try:
            async with factory() as db:
                # Write garbage into the task-state block.
                db.add(MemoryBlock(session_id=sid, label=ConsultantService._LABEL,
                                   value="{not valid json"))
                await db.commit()

                svc = ConsultantService(db, ident, sid)
                recovered = await svc.load_state()
                assert recovered.revision == 0 and recovered.workflow_id is None

                events = (await db.execute(select(AuditLog).where(
                    AuditLog.actor_id == ident.employee_id,
                    AuditLog.action == "consultant.state_corrupt_recovered"))).scalars().all()
                assert events, "corrupt state must record an explicit recovery audit event"
        finally:
            async with factory() as db:
                await db.execute(delete(MemoryBlock).where(MemoryBlock.session_id == sid))
                await db.execute(delete(AuditLog).where(AuditLog.actor_id == ident.employee_id))
                await db.commit()
            await engine.dispose()

    asyncio.run(run())
