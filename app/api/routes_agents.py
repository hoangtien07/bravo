"""Agent demo endpoints (NỘI BỘ, chạy trên MOCK) — quét bất thường -> cờ nháp chờ duyệt.

Engine tất định (app/agent/anomaly.py) tìm bất thường; mỗi cờ tạo một Draft(kind="anomaly_flag")
đi qua maker-checker (non-invasive: chỉ FLAG chờ người xác nhận). Idempotent: bỏ qua cờ đã có
draft pending cùng payload_hash. Số liệu từ engine, KHÔNG do LLM sinh.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent import anomaly, tax
from app.agent.tools import payload_hash
from app.data_layer.mock_source import MockDataSource
from app.database import get_db
from app.erp import draft_queue
from app.security.auth import require_permission
from app.security.rls import Identity

router = APIRouter()


class ScanOut(BaseModel):
    created: int
    total_flags: int


def _scan_department(identity: Identity):
    """Scope cờ nháp theo phòng người chạy scan (RLS, invariant #1) — fail-closed nếu không rõ.

    Cờ anomaly/tax do agent tạo KHÔNG được để NULL=global (rò chéo phòng ban). Admin có thể
    tạo global chủ ý; người thường phải thuộc đúng một phòng ban."""
    dept_id = draft_queue.resolve_draft_department(identity)
    if dept_id is None and not identity.is_admin:
        raise HTTPException(
            status_code=400,
            detail="Không xác định được phòng ban cho kiến nghị (fail-closed): tài khoản không "
                   "thuộc đúng một phòng ban. Không tạo nháp global chéo phòng.")
    return dept_id


@router.post("/agents/anomaly/scan", response_model=ScanOut)
async def scan_anomaly(identity: Identity = Depends(require_permission("draft:create")),
                       db: AsyncSession = Depends(get_db)) -> ScanOut:
    dept_id = _scan_department(identity)
    src = MockDataSource()
    flags = anomaly.detect(src.fetch_block("journal_entries"), src.fetch_block("anomalies"))
    existing = {d.payload_hash for d in
                await draft_queue.list_drafts(db, identity, status="pending", kind="anomaly_flag")}
    created = 0
    for f in flags:
        payload = f.to_payload()
        if payload_hash(payload) in existing:
            continue
        await draft_queue.create_draft(db, identity, kind="anomaly_flag", payload=payload,
                                       department_id=dept_id)
        created += 1
    return ScanOut(created=created, total_flags=len(flags))


@router.post("/agents/tax/reconcile", response_model=ScanOut)
async def reconcile_tax(identity: Identity = Depends(require_permission("draft:create")),
                        db: AsyncSession = Depends(get_db)) -> ScanOut:
    """Đối chiếu hoá đơn ↔ tờ khai (Lớp 2) -> draft kiến nghị `tax_adjustment` chờ duyệt."""
    dept_id = _scan_department(identity)
    src = MockDataSource()
    flags = tax.reconcile(src.fetch_block("invoices"), src.fetch_block("tax_returns"))
    existing = {d.payload_hash for d in
                await draft_queue.list_drafts(db, identity, status="pending", kind="tax_adjustment")}
    created = 0
    for f in flags:
        payload = f.to_payload()
        if payload_hash(payload) in existing:
            continue
        await draft_queue.create_draft(db, identity, kind="tax_adjustment", payload=payload,
                                       department_id=dept_id)
        created += 1
    return ScanOut(created=created, total_flags=len(flags))
