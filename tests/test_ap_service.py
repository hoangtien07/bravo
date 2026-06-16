"""W3.4 — AP service: hoá đơn XML -> bút toán nháp (qua draft_queue). DB giả lập."""
from __future__ import annotations

import uuid
from pathlib import Path

import pytest

from app.accounting.ap_service import create_invoice_draft
from app.database.models import Draft
from app.security.rls import Identity

_FIX = Path(__file__).parent / "fixtures" / "invoices"


class _FakeDB:
    def __init__(self):
        self.added = []

    def add(self, obj):
        self.added.append(obj)

    async def commit(self):
        pass

    async def refresh(self, obj):
        if isinstance(obj, Draft) and obj.id is None:
            obj.id = uuid.uuid4()


def _identity(perms=("draft:create",)):
    return Identity(employee_id=uuid.uuid4(), department_ids=[uuid.uuid4()],
                    permissions=frozenset(perms), is_admin=False)


@pytest.mark.asyncio
async def test_invoice_to_journal_draft():
    db = _identity_db = _FakeDB()
    idn = _identity()
    draft, je = await create_invoice_draft(
        db, idn, (_FIX / "inv_single_10pct_goods.xml").read_bytes())

    # bút toán cân + đúng kind + scope theo phòng
    assert je.total_debit == je.total_credit
    drafts = [o for o in db.added if isinstance(o, Draft)]
    assert len(drafts) == 1
    d = drafts[0]
    assert d.kind == "journal_entry"
    assert d.department_id == idn.department_ids[0]      # RLS scope theo đơn vị
    assert d.payload["total_debit"] == "1100000" or float(d.payload["total_debit"]) == 1100000
    # payload JSON-safe (Decimal đã serialize) -> hash được, lưu JSONB được
    assert isinstance(d.payload["lines"], list) and len(d.payload["lines"]) == 3


@pytest.mark.asyncio
async def test_audit_logged_on_draft_create():
    from app.database.models import AuditLog

    db = _FakeDB()
    await create_invoice_draft(db, _identity(), (_FIX / "inv_multi_rate.xml").read_bytes())
    audits = [o for o in db.added if isinstance(o, AuditLog)]
    assert any(a.action == "draft.create" for a in audits)
