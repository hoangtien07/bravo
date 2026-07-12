"""D — tool read-only preview_journal_entry: lộ money-engine AP cho chat.

- Registry contract: read-only + required_permission (không phải write, không tạo nháp).
- DB: trả list[MetricResult] đúng số của bút toán; RLS chặn draft khác phòng.
"""
from __future__ import annotations

import asyncio
import uuid
from decimal import Decimal

import pytest

from app.agent.loop import _preview_journal_entry
from app.agent.tools import REGISTRY
from app.data_layer.semantic import MetricResult
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


def _journal_payload() -> dict:
    return {
        "invoice": {},
        "lines": [
            {"account": "156", "debit": "1", "memo": "hàng hoá"},
            {"account": "331", "credit": "1", "source_ref": "HD#1 dòng 1"},
        ],
        "total_debit": "1",
        "total_credit": "1",
    }


# --- contract (no DB) --------------------------------------------------------- #
def test_preview_tool_is_readonly_gated():
    t = REGISTRY["preview_journal_entry"]
    assert t.read_only is True                 # READ -> không tạo nháp
    assert t.requires_approval is False
    assert t.required_permission == "draft:create"
    assert t.payload_builder is None
    assert ":" in t.required_permission        # thỏa audit least-privilege (tool_inventory)


# --- DB integration ----------------------------------------------------------- #
pytestmark = pytest.mark.skipif(not _db_available(), reason="Postgres not reachable")


def test_preview_returns_engine_numbers_and_rls_blocks_cross_dept():
    async def run() -> None:
        from sqlalchemy import delete, select
        from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
        from sqlalchemy.pool import NullPool

        from app.config import get_settings
        from app.database.models import Draft, Employee
        from app.erp import draft_queue

        engine = create_async_engine(get_settings().database_url, poolclass=NullPool)
        factory = async_sessionmaker(engine, expire_on_commit=False)
        created: list[uuid.UUID] = []
        try:
            async with factory() as db:
                maker = (await db.execute(select(Employee.id).where(
                    Employee.email == "ketoan@bravo.vn"))).scalars().first()
                dept_a, dept_b = uuid.uuid4(), uuid.uuid4()
                maker_id = Identity(employee_id=maker, department_ids=[dept_a],
                                    permissions=frozenset({"draft:create:own_dept"}))
                foreign = Identity(employee_id=maker, department_ids=[dept_b],
                                   permissions=frozenset({"draft:create:own_dept"}))

                draft = await draft_queue.create_draft(
                    db, maker_id, "journal_entry", _journal_payload(), department_id=dept_a)
                did = draft.id
                created.append(did)

                # maker (đúng phòng) -> trả số engine dưới dạng MetricResult
                out = await _preview_journal_entry(str(did), identity=maker_id, db=db)
                assert out and all(isinstance(x, MetricResult) for x in out)
                by = {x.metric_id: x.value for x in out}
                assert by["butoan.156.debit"] == Decimal("1")
                assert by["butoan.331.credit"] == Decimal("1")
                assert by["butoan.total_debit"] == Decimal("1")
                assert by["butoan.total_credit"] == Decimal("1")
                # provenance mang source_ref/memo để LLM trích dẫn
                assert any("HD#1" in x.provenance for x in out)

                # RLS: người phòng khác KHÔNG xem được -> raise (ẩn tồn tại)
                with pytest.raises(ValueError):
                    await _preview_journal_entry(str(did), identity=foreign, db=db)
        finally:
            async with factory() as db:
                if created:
                    await db.execute(delete(Draft).where(Draft.id.in_(created)))
                    await db.commit()
            await engine.dispose()

    asyncio.run(run())
