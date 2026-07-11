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


def resolve_draft_department(identity: Identity, payload: dict | None = None) -> uuid.UUID | None:
    """Suy department cho draft do AGENT/dịch vụ tạo — scope maker-checker theo RLS (invariant #1).

    Thứ tự: `department_id` tường minh trong payload -> phòng DUY NHẤT của identity -> None.
    Trả None khi KHÔNG suy ra được (identity 0 hoặc >1 phòng, không có dept trong payload);
    caller PHẢI fail-closed (từ chối tạo draft) thay vì để rơi về NULL=global — nếu không,
    nháp của phòng B lọt sang approver phòng A (lỗ rò chéo phòng ban, OWASP ASI03).
    """
    if payload:
        raw = payload.get("department_id")
        if raw:
            try:
                requested = raw if isinstance(raw, uuid.UUID) else uuid.UUID(str(raw))
                level = identity.scope_level("draft", "create")
                if level == "all" or requested in identity.department_ids:
                    return requested
            except (ValueError, AttributeError, TypeError):
                return None
            return None
    if len(identity.department_ids) == 1:
        return identity.department_ids[0]
    return None


def canonical_draft_kind(kind: str) -> str:
    """Map the agent tool name for a journal proposal to the persisted draft kind."""
    return "journal_entry" if kind == "create_journal_entry" else kind


def validate_draft_payload(kind: str, payload: dict) -> dict:
    """Validate a financial draft at every persistence/export transition."""
    if canonical_draft_kind(kind) != "journal_entry":
        return payload
    from app.accounting.journal import JournalEntryPayload

    try:
        return JournalEntryPayload.model_validate(payload).model_dump(mode="json")
    except Exception as exc:
        raise ValueError("Journal payload is invalid") from exc


def _required_draft_department(
    identity: Identity,
    payload: dict,
    department_id: uuid.UUID | None,
) -> uuid.UUID:
    """Resolve the authoritative owner; NULL must never create a shared draft."""
    if department_id is not None:
        resolved = resolve_draft_department(identity, {"department_id": str(department_id)})
    else:
        resolved = resolve_draft_department(identity, payload)
    if resolved is None:
        raise ValueError("A permitted department owner is required for draft creation")
    return resolved


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
    kind = canonical_draft_kind(kind)
    department_id = _required_draft_department(identity, payload, department_id)
    payload = validate_draft_payload(kind, payload)
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
    draft = (await db.execute(select(Draft).where(
        Draft.id == draft_id, draft_scope_filter(identity)
    ))).scalar_one_or_none()
    if draft is None or draft.status != "pending":
        raise ValueError("Draft không tồn tại hoặc không ở trạng thái chờ duyệt")
    ok, reason = maker_checker_ok(identity.employee_id, draft.created_by,
                                  allow_self_approval=get_settings().allow_self_approval)
    if not ok:
        raise PermissionError(reason)
    if payload_hash(draft.payload) != draft.payload_hash:
        raise ValueError("Payload đã thay đổi sau khi đề xuất — từ chối duyệt (anti-drift)")
    validate_draft_payload(draft.kind, draft.payload)
    draft.status = "approved"
    db.add(AuditLog(actor_id=identity.employee_id, action="draft.approve",
                    detail={"draft_id": str(draft_id)}))
    # Đầu ra của draft đã duyệt = XUẤT FILE để kế toán nhập tay (journal_export), KHÔNG ghi
    # thẳng ERP. Đây là quyết định chốt của ADR-0016 (Accepted 2026-07-05): con người là cổng
    # ghi cuối (non-invasive hơn) + bỏ phụ thuộc ERP API. Nối ERP staging là nâng cấp tùy chọn
    # Phase sau, KHÔNG gating — không giữ TODO ở đây để tránh hiểu nhầm còn việc phải làm.
    await db.commit()
    # W2.3 "duyệt = thực thi": nếu draft thuộc một AgentRun chờ duyệt -> đánh dấu run done.
    if draft.agent_run_id is not None:
        from app.agent import runs
        await runs.complete_on_approval(db, draft.agent_run_id)
    await db.refresh(draft)
    return draft


async def reject_draft(db: AsyncSession, identity: Identity, draft_id: uuid.UUID, reason: str) -> Draft:
    draft = (await db.execute(select(Draft).where(
        Draft.id == draft_id, draft_scope_filter(identity)
    ))).scalar_one_or_none()
    if draft is None or draft.status != "pending":
        raise ValueError("Draft không tồn tại hoặc không ở trạng thái chờ duyệt")
    draft.status = "rejected"
    db.add(AuditLog(actor_id=identity.employee_id, action="draft.reject",
                    detail={"draft_id": str(draft_id), "reason": reason}))
    await db.commit()
    await db.refresh(draft)
    return draft
