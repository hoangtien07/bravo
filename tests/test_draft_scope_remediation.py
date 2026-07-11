"""Focused regressions for draft ownership and journal integrity gates."""
from __future__ import annotations

import uuid
from pathlib import Path

import pytest

from app.accounting.journal import build_journal_entry
from app.database.models import Draft
from app.erp.draft_queue import create_draft, resolve_draft_department, validate_draft_payload
from app.ingestion.invoice_parser import parse_invoice_xml
from app.security.rls import Identity


_FIX = Path(__file__).parent / "fixtures" / "invoices"
_DEPT_A = uuid.uuid4()
_DEPT_B = uuid.uuid4()


def _identity(*, departments: list[uuid.UUID], permissions: set[str] | None = None) -> Identity:
    return Identity(employee_id=uuid.uuid4(), department_ids=departments,
                    permissions=frozenset(permissions or {"draft:create:own_dept"}))


def _journal_payload() -> dict:
    return build_journal_entry(
        parse_invoice_xml((_FIX / "inv_single_10pct_goods.xml").read_bytes())
    ).model_dump(mode="json")


class _FakeDB:
    def __init__(self):
        self.added = []

    def add(self, item):
        self.added.append(item)

    async def commit(self):
        pass

    async def refresh(self, item):
        if isinstance(item, Draft) and item.id is None:
            item.id = uuid.uuid4()


def test_requested_foreign_draft_department_is_not_authoritative():
    identity = _identity(departments=[_DEPT_A])
    assert resolve_draft_department(identity, {"department_id": str(_DEPT_B)}) is None


def test_requested_own_draft_department_is_allowed():
    identity = _identity(departments=[_DEPT_A])
    assert resolve_draft_department(identity, {"department_id": str(_DEPT_A)}) == _DEPT_A


@pytest.mark.asyncio
@pytest.mark.parametrize("departments, requested", [([], None), ([_DEPT_A, _DEPT_B], None), ([_DEPT_A], _DEPT_B)])
async def test_ambiguous_or_foreign_owner_never_persists_a_draft(departments, requested):
    db = _FakeDB()
    identity = _identity(departments=departments)
    with pytest.raises(ValueError, match="department owner"):
        await create_draft(db, identity, "journal_entry", _journal_payload(), department_id=requested)
    assert not db.added


@pytest.mark.asyncio
async def test_owned_journal_draft_is_persisted_with_authoritative_department():
    db = _FakeDB()
    identity = _identity(departments=[_DEPT_A])
    draft = await create_draft(db, identity, "journal_entry", _journal_payload())
    assert draft.department_id == _DEPT_A
    assert draft.kind == "journal_entry"


def test_journal_payload_is_revalidated_and_unknown_accounts_are_rejected():
    payload = _journal_payload()
    payload["lines"][0]["account"] = "NOT-A-COA"
    with pytest.raises(ValueError, match="Journal payload"):
        validate_draft_payload("journal_entry", payload)
