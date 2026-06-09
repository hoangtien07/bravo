"""Draft queue (HITL) — AI proposals awaiting human approval. Phase 2/3.

Non-invasive (VISION §2): the AI NEVER writes to the ERP ledger. It creates a DRAFT
here; a human reviews and approves on the UI; only on approval does an approved draft
flow onward (to BRAVO ERP's staging — needs ERP write endpoint, see ERP-INTEGRATION-REQUEST §3).

Args are pinned by hash at creation (findings/J anti-drift): approval re-verifies the
hash so what the human approved is exactly what executes. Every action is audited.
"""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.tools import payload_hash
from app.database.models import AuditLog, Draft
from app.security.rls import Identity


async def create_draft(db: AsyncSession, identity: Identity, kind: str, payload: dict) -> Draft:
    """AI/user proposes a draft (e.g. a journal entry). Status=pending; hash pinned."""
    draft = Draft(kind=kind, payload=payload, payload_hash=payload_hash(payload),
                  status="pending", created_by=identity.employee_id)
    db.add(draft)
    db.add(AuditLog(actor_id=identity.employee_id, action="draft.create",
                    detail={"kind": kind, "hash": draft.payload_hash}))
    await db.commit()
    await db.refresh(draft)
    return draft


async def list_pending(db: AsyncSession, identity: Identity) -> list[Draft]:
    """Drafts awaiting review. (Scope by department/role can be added like RLS.)"""
    rows = (await db.execute(
        select(Draft).where(Draft.status == "pending").order_by(Draft.created_at.desc())
    )).scalars().all()
    return list(rows)


async def approve_draft(db: AsyncSession, identity: Identity, draft_id: uuid.UUID) -> Draft:
    """Approve a draft — ONLY if its payload hash is unchanged (anti-drift)."""
    draft = await db.get(Draft, draft_id)
    if draft is None or draft.status != "pending":
        raise ValueError("Draft không tồn tại hoặc không ở trạng thái chờ duyệt")
    if payload_hash(draft.payload) != draft.payload_hash:
        raise ValueError("Payload đã thay đổi sau khi đề xuất — từ chối duyệt (anti-drift)")
    draft.status = "approved"
    db.add(AuditLog(actor_id=identity.employee_id, action="draft.approve",
                    detail={"draft_id": str(draft_id)}))
    # TODO(Phase 3): push approved draft to BRAVO ERP staging (read-only-write endpoint,
    # ERP-INTEGRATION-REQUEST §3). The AI still never posts to the ledger directly.
    await db.commit()
    await db.refresh(draft)
    return draft


async def reject_draft(db: AsyncSession, identity: Identity, draft_id: uuid.UUID, reason: str) -> Draft:
    draft = await db.get(Draft, draft_id)
    if draft is None or draft.status != "pending":
        raise ValueError("Draft không tồn tại hoặc không ở trạng thái chờ duyệt")
    draft.status = "rejected"
    db.add(AuditLog(actor_id=identity.employee_id, action="draft.reject",
                    detail={"draft_id": str(draft_id), "reason": reason}))
    await db.commit()
    await db.refresh(draft)
    return draft
