"""Draft queue (HITL) — AI proposals awaiting human approval. Phase 2/3 (WP-E hardening).

Non-invasive (VISION §2): the AI NEVER writes to the ERP ledger. It creates a DRAFT here;
a human reviews and approves on the UI; only on approval does an approved draft flow onward
(to BRAVO ERP staging — needs ERP write endpoint, ERP-INTEGRATION-REQUEST §3).

WP-E hardening (council Critical, SOX/ISA maker-checker):
  - approve uses pg_advisory_xact_lock -> serialize concurrent approvals (no double-posting).
  - ANTI-SELF-APPROVAL: creator cannot approve own draft (unless allow_self_approval config).
  - list_pending applies RLS by department (no leaking other depts' drafts).
  - create_draft is IDEMPOTENT per (agent_run_id, payload_hash) -> resume won't duplicate.
Args pinned by hash at creation (findings/J anti-drift); re-verified on approval. All audited.
"""
from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import or_, select, text, true
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.tools import payload_hash
from app.config import get_settings
from app.database.models import AuditLog, Draft
from app.security.rls import Identity

if TYPE_CHECKING:
    from sqlalchemy import ColumnElement


# --- pure helpers (testable WITHOUT a database) ---
def maker_checker_ok(approver_id: uuid.UUID, created_by: uuid.UUID, *,
                     allow_self_approval: bool) -> tuple[bool, str | None]:
    """Maker-checker (SOX/ISA): người tạo KHÔNG được tự duyệt draft của mình."""
    if not allow_self_approval and approver_id == created_by:
        return False, "Không được tự duyệt draft của chính mình (maker-checker SOX/ISA)."
    return True, None


def draft_scope_filter(identity: Identity, action: str = "approve") -> "ColumnElement[bool]":
    """SQL predicate giới hạn Draft theo quyền (RLS-in-query). NULL department = global."""
    level = identity.scope_level("draft", action)
    if level == "all":
        return true()
    if level is None:
        return Draft.id.is_(None)  # deny
    is_global = Draft.department_id.is_(None)
    if not identity.department_ids:
        return is_global
    return or_(is_global, Draft.department_id.in_(identity.department_ids))


# --- service (database) ---
async def create_draft(db: AsyncSession, identity: Identity, kind: str, payload: dict, *,
                       agent_run_id: uuid.UUID | None = None,
                       department_id: uuid.UUID | None = None) -> Draft:
    """Propose a draft (status=pending, hash pinned). IDEMPOTENT per (agent_run_id, payload_hash)."""
    h = payload_hash(payload)
    if agent_run_id is not None:  # resume-safe: trả draft đã có thay vì tạo trùng
        existing = (await db.execute(select(Draft).where(
            Draft.agent_run_id == agent_run_id, Draft.payload_hash == h))).scalar_one_or_none()
        if existing is not None:
            return existing

    draft = Draft(kind=kind, payload=payload, payload_hash=h, status="pending",
                  created_by=identity.employee_id, agent_run_id=agent_run_id,
                  department_id=department_id)
    db.add(draft)
    db.add(AuditLog(actor_id=identity.employee_id, action="draft.create",
                    detail={"kind": kind, "hash": h, "agent_run_id": str(agent_run_id or "")}))
    try:
        await db.commit()
    except IntegrityError:  # race trên uq_draft_run_hash -> trả bản đã có
        await db.rollback()
        return (await db.execute(select(Draft).where(
            Draft.agent_run_id == agent_run_id, Draft.payload_hash == h))).scalar_one()
    await db.refresh(draft)
    return draft


async def list_pending(db: AsyncSession, identity: Identity) -> list[Draft]:
    """Drafts awaiting review — RLS-scoped IN the query (no cross-department leak)."""
    return await list_drafts(db, identity, status="pending")


async def list_drafts(db: AsyncSession, identity: Identity, *, status: str | None = None,
                      kind: str | None = None) -> list[Draft]:
    """Drafts RLS-scoped, lọc tuỳ chọn theo status (pending/approved/rejected) + kind."""
    conds = [draft_scope_filter(identity)]
    if status:
        conds.append(Draft.status == status)
    if kind:
        conds.append(Draft.kind == kind)
    rows = (await db.execute(
        select(Draft).where(*conds).order_by(Draft.created_at.desc())
    )).scalars().all()
    return list(rows)


async def approve_draft(db: AsyncSession, identity: Identity, draft_id: uuid.UUID) -> Draft:
    """Approve — advisory-lock serialized; anti-self-approval; hash unchanged (anti-drift)."""
    # Serialize concurrent approvals of the SAME draft (chống double-posting).
    await db.execute(text("SELECT pg_advisory_xact_lock(hashtext(:k))"), {"k": str(draft_id)})
    draft = await db.get(Draft, draft_id)
    if draft is None or draft.status != "pending":
        raise ValueError("Draft không tồn tại hoặc không ở trạng thái chờ duyệt")
    ok, reason = maker_checker_ok(identity.employee_id, draft.created_by,
                                  allow_self_approval=get_settings().allow_self_approval)
    if not ok:
        raise PermissionError(reason)
    if payload_hash(draft.payload) != draft.payload_hash:
        raise ValueError("Payload đã thay đổi sau khi đề xuất — từ chối duyệt (anti-drift)")
    draft.status = "approved"
    db.add(AuditLog(actor_id=identity.employee_id, action="draft.approve",
                    detail={"draft_id": str(draft_id)}))
    # TODO(Phase 3): push approved draft to BRAVO ERP staging (ERP-INTEGRATION-REQUEST §3).
    await db.commit()
    # W2.3 "duyệt = thực thi": nếu draft thuộc một AgentRun chờ duyệt -> đánh dấu run done.
    if draft.agent_run_id is not None:
        from app.agent import runs
        await runs.complete_on_approval(db, draft.agent_run_id)
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
