"""Draft (HITL) routes: propose / list pending / approve / reject.

Non-invasive write path — AI proposes, human approves. Approval requires `draft:approve`.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.accounting import journal_export
from app.database import get_db
from app.database.models import AuditLog, Draft
from app.erp import draft_queue
from app.security.auth import require_permission
from app.security.rls import Identity

router = APIRouter()


class DraftIn(BaseModel):
    kind: str
    payload: dict


class DraftOut(BaseModel):
    id: uuid.UUID
    kind: str
    status: str
    payload: dict
    created_by: uuid.UUID | None = None
    created_at: datetime | None = None


class RejectIn(BaseModel):
    reason: str


def _out(d) -> DraftOut:
    return DraftOut(id=d.id, kind=d.kind, status=d.status, payload=d.payload,
                    created_by=getattr(d, "created_by", None),
                    created_at=getattr(d, "created_at", None))


@router.post("/drafts", response_model=DraftOut, status_code=status.HTTP_201_CREATED)
async def propose(body: DraftIn, identity: Identity = Depends(require_permission("draft:create")),
                  db: AsyncSession = Depends(get_db)) -> DraftOut:
    return _out(await draft_queue.create_draft(db, identity, body.kind, body.payload))


@router.get("/drafts", response_model=list[DraftOut])
async def list_drafts(status: str | None = Query(None, description="pending|approved|rejected"),
                      kind: str | None = Query(None),
                      identity: Identity = Depends(require_permission("draft:approve")),
                      db: AsyncSession = Depends(get_db)) -> list[DraftOut]:
    rows = await draft_queue.list_drafts(db, identity, status=status, kind=kind)
    # Audit truy cập đặc quyền (PDPD/NĐ13 & NĐ356: draft chứa PII lương/HR -> xem/liệt kê có vết).
    db.add(AuditLog(actor_id=identity.employee_id, action="draft.list",
                    detail={"status": status or "", "kind": kind or "", "count": len(rows)}))
    await db.commit()
    return [_out(d) for d in rows]


class BatchExportIn(BaseModel):
    draft_ids: list[uuid.UUID]


@router.post("/drafts/export")
async def export_batch(body: BatchExportIn,
                       identity: Identity = Depends(require_permission("draft:approve")),
                       db: AsyncSession = Depends(get_db)) -> Response:
    """Xuất GỘP nhiều bút toán vào 1 CSV (nhập tay theo lô) — RLS-scoped."""
    rows = (await db.execute(select(Draft).where(
        Draft.id.in_(body.draft_ids), draft_queue.draft_scope_filter(identity)))).scalars().all()
    payloads = [d.payload for d in rows if d.kind == "journal_entry"]
    if not payloads:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Không có bút toán hợp lệ để xuất")
    return Response(journal_export.batch_to_csv(payloads), media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": 'attachment; filename="buttoan_lo.csv"'})


@router.get("/drafts/{draft_id}", response_model=DraftOut)
async def get_draft(draft_id: uuid.UUID,
                    identity: Identity = Depends(require_permission("draft:approve")),
                    db: AsyncSession = Depends(get_db)) -> DraftOut:
    # RLS-scoped: chỉ trả draft trong phạm vi phòng của identity (không rò liên-phòng).
    d = (await db.execute(select(Draft).where(
        Draft.id == draft_id, draft_queue.draft_scope_filter(identity)))).scalar_one_or_none()
    if d is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Draft không tồn tại hoặc ngoài phạm vi")
    return _out(d)


@router.get("/drafts/{draft_id}/export")
async def export_draft(draft_id: uuid.UUID, fmt: str = Query("csv", pattern="^(csv|xlsx)$"),
                       identity: Identity = Depends(require_permission("draft:approve")),
                       db: AsyncSession = Depends(get_db)) -> Response:
    """Xuất bút toán nháp ra CSV/XLSX để kế toán nhập tay vào ERP (ADR-0016, non-invasive)."""
    d = (await db.execute(select(Draft).where(
        Draft.id == draft_id, draft_queue.draft_scope_filter(identity)))).scalar_one_or_none()
    if d is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Draft không tồn tại hoặc ngoài phạm vi")
    if d.kind != "journal_entry":
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Chỉ xuất được bút toán (journal_entry)")
    name = f"buttoan_{str(draft_id)[:8]}"
    if fmt == "xlsx":
        try:
            data = journal_export.to_xlsx(d.payload)
        except ImportError:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY,
                                "XLSX cần openpyxl — dùng fmt=csv") from None
        return Response(data, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        headers={"Content-Disposition": f'attachment; filename="{name}.xlsx"'})
    return Response(journal_export.to_csv(d.payload), media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": f'attachment; filename="{name}.csv"'})


@router.post("/drafts/{draft_id}/approve", response_model=DraftOut)
async def approve(draft_id: uuid.UUID,
                  identity: Identity = Depends(require_permission("draft:approve")),
                  db: AsyncSession = Depends(get_db)) -> DraftOut:
    try:
        return _out(await draft_queue.approve_draft(db, identity, draft_id))
    except PermissionError as exc:  # anti-self-approval / maker-checker (WP-E)
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc


@router.post("/drafts/{draft_id}/reject", response_model=DraftOut)
async def reject(draft_id: uuid.UUID, body: RejectIn,
                 identity: Identity = Depends(require_permission("draft:approve")),
                 db: AsyncSession = Depends(get_db)) -> DraftOut:
    try:
        return _out(await draft_queue.reject_draft(db, identity, draft_id, body.reason))
    except ValueError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
