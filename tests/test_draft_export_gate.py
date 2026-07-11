"""Backend contract tests: only approved, valid journals are exportable."""
from __future__ import annotations

import uuid
from pathlib import Path

import pytest
from fastapi import HTTPException

from app.accounting.journal import build_journal_entry
from app.api import routes_drafts
from app.database.models import Draft
from app.ingestion.invoice_parser import parse_invoice_xml
from app.security.rls import Identity


_FIX = Path(__file__).parent / "fixtures" / "invoices"


def _payload() -> dict:
    return build_journal_entry(
        parse_invoice_xml((_FIX / "inv_single_10pct_goods.xml").read_bytes())
    ).model_dump(mode="json")


def _identity() -> Identity:
    return Identity(employee_id=uuid.uuid4(), permissions=frozenset({"draft:approve:all"}))


class _Result:
    def __init__(self, rows):
        self._rows = rows

    def scalar_one_or_none(self):
        return self._rows[0] if self._rows else None

    def scalars(self):
        return self

    def all(self):
        return self._rows


class _FakeDB:
    def __init__(self, rows):
        self.rows = rows

    async def execute(self, _statement):
        return _Result(self.rows)


def _draft(*, status: str, payload: dict | None = None) -> Draft:
    return Draft(id=uuid.uuid4(), kind="journal_entry", status=status, payload=payload or _payload())


@pytest.mark.asyncio
@pytest.mark.parametrize("status", ["pending", "rejected"])
async def test_unapproved_individual_journal_export_is_denied(status):
    draft = _draft(status=status)
    with pytest.raises(HTTPException) as exc:
        await routes_drafts.export_draft(draft.id, "csv", _identity(), _FakeDB([draft]))
    assert exc.value.status_code == 409


@pytest.mark.asyncio
async def test_approved_individual_journal_export_succeeds():
    draft = _draft(status="approved")
    response = await routes_drafts.export_draft(draft.id, "csv", _identity(), _FakeDB([draft]))
    assert response.status_code == 200
    assert response.body.startswith(b"\xef\xbb\xbf")


@pytest.mark.asyncio
async def test_mixed_batch_export_is_denied_without_partial_output():
    approved = _draft(status="approved")
    pending = _draft(status="pending")
    with pytest.raises(HTTPException) as exc:
        await routes_drafts.export_batch(
            routes_drafts.BatchExportIn(draft_ids=[approved.id, pending.id]),
            _identity(),
            _FakeDB([approved, pending]),
        )
    assert exc.value.status_code == 409


@pytest.mark.asyncio
async def test_export_revalidates_journal_payload():
    payload = _payload()
    payload["lines"][0]["account"] = "NOT-A-COA"
    draft = _draft(status="approved", payload=payload)
    with pytest.raises(HTTPException) as exc:
        await routes_drafts.export_draft(draft.id, "csv", _identity(), _FakeDB([draft]))
    assert exc.value.status_code == 422
