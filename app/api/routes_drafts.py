"""Draft (HITL) routes: propose / list pending / approve / reject.

Non-invasive write path — AI proposes, human approves. Approval requires `draft:approve`.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.database.models import Draft
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
async def pending(identity: Identity = Depends(require_permission("draft:approve")),
                  db: AsyncSession = Depends(get_db)) -> list[DraftOut]:
    return [_out(d) for d in await draft_queue.list_pending(db, identity)]


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
