"""AP service: hoá đơn XML -> bút toán nháp chờ duyệt (close-the-loop).

Đường DETERMINISTIC (không cần LLM): parse XML -> dựng bút toán cân Nợ=Có -> create_draft
(invariant #2: ghi = nháp). Tái dùng draft_queue (maker-checker, RLS, idempotent, audit).
Dùng được bởi cả endpoint /api/invoices/draft lẫn (sau) agent tool.
"""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.accounting.journal import JournalEntryPayload, build_journal_entry
from app.database.models import Draft
from app.erp import draft_queue
from app.ingestion.invoice_parser import parse_invoice_xml
from app.security.rls import Identity


async def create_invoice_draft(
    db: AsyncSession, identity: Identity, xml_bytes: bytes | str, *,
    raw_xml_path: str | None = None,
) -> tuple[Draft, JournalEntryPayload]:
    """Parse hoá đơn -> bút toán nháp. Scope draft theo phòng của người tạo (RLS)."""
    inv = parse_invoice_xml(xml_bytes, raw_xml_path=raw_xml_path)
    je = build_journal_entry(inv)
    dept_id = identity.department_ids[0] if identity.department_ids else None
    draft = await draft_queue.create_draft(
        db, identity, kind="journal_entry", payload=je.model_dump(mode="json"),
        department_id=dept_id,
    )
    return draft, je
