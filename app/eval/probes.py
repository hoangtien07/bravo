"""Cross-tenant ACL leak probes — the most important regression test for BRAVO.

A user scoped to department A must NEVER retrieve a chunk that belongs ONLY to
department B (no overlap, not global). This is the failure class that hit Slack AI and
Sage Copilot (findings/C). Run after every change touching retrieval/RLS.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.rag import retriever
from app.security.rls import Identity


@dataclass
class LeakReport:
    query: str
    actor_dept: uuid.UUID
    leaked_chunk_ids: list[str]

    @property
    def leaked(self) -> bool:
        return bool(self.leaked_chunk_ids)


async def probe_leak(db: AsyncSession, actor: Identity, foreign_dept: uuid.UUID,
                     query: str) -> LeakReport:
    """Retrieve as `actor`; flag any returned chunk scoped ONLY to `foreign_dept`
    (i.e. department_ids == [foreign_dept] and actor has no access)."""
    # Disable rerank for determinism; we only care about WHICH chunks come back.
    results = await retriever.retrieve(db, actor, query, top_n=50, use_rerank=False)

    from sqlalchemy import select

    from app.database.models import Chunk

    ids = [uuid.UUID(r.chunk_id) for r in results]
    if not ids:
        return LeakReport(query, _first_dept(actor), [])
    rows = (await db.execute(select(Chunk).where(Chunk.id.in_(ids)))).scalars().all()

    leaked = [
        str(c.id)
        for c in rows
        if c.department_ids
        and foreign_dept in c.department_ids
        and not (set(c.department_ids) & set(actor.department_ids))
        and "doc:read:all" not in actor.permissions
        and not actor.is_admin
    ]
    return LeakReport(query, _first_dept(actor), leaked)


def _first_dept(identity: Identity) -> uuid.UUID:
    return identity.department_ids[0] if identity.department_ids else uuid.UUID(int=0)


# --- Draft leak probe (Phase 0.3): draft phòng B không được lọt sang approver phòng A ---
@dataclass
class DraftLeakReport:
    actor_dept: uuid.UUID
    leaked_draft_ids: list[str]

    @property
    def leaked(self) -> bool:
        return bool(self.leaked_draft_ids)


def draft_leaked(draft, actor: Identity, foreign_dept: uuid.UUID) -> bool:
    """PURE predicate (test được không cần DB): `draft` thuộc RIÊNG `foreign_dept` mà `actor`
    KHÔNG có quyền thấy. Draft global (department_id=None) là dùng-chung chủ ý -> KHÔNG tính rò.
    Đây chính là lớp bất thường mà lỗ 'draft agent = global' từng gây ra (OWASP ASI03)."""
    dep = getattr(draft, "department_id", None)
    return bool(
        dep is not None
        and dep == foreign_dept
        and dep not in actor.department_ids
        and actor.scope_level("draft", "approve") != "all"
        and not actor.is_admin
    )


async def probe_draft_leak(db: AsyncSession, actor: Identity,
                           foreign_dept: uuid.UUID) -> DraftLeakReport:
    """List drafts như `actor` (RLS-in-query) rồi soi có draft nào thuộc RIÊNG `foreign_dept`."""
    from app.erp import draft_queue
    drafts = await draft_queue.list_drafts(db, actor)
    leaked = [str(d.id) for d in drafts if draft_leaked(d, actor, foreign_dept)]
    return DraftLeakReport(_first_dept(actor), leaked)


async def assert_no_draft_leak(db: AsyncSession, actor: Identity,
                               foreign_dept: uuid.UUID) -> DraftLeakReport | None:
    """Return report nếu rò (None = PASS). CI gate cho maker-checker RLS."""
    r = await probe_draft_leak(db, actor, foreign_dept)
    return r if r.leaked else None


async def assert_no_leak(db: AsyncSession, actor: Identity, foreign_dept: uuid.UUID,
                         queries: list[str]) -> list[LeakReport]:
    """Return all leaking probes (empty list = PASS). Use as a CI gate."""
    reports = [await probe_leak(db, actor, foreign_dept, q) for q in queries]
    return [r for r in reports if r.leaked]
