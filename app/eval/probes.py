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


async def assert_no_leak(db: AsyncSession, actor: Identity, foreign_dept: uuid.UUID,
                         queries: list[str]) -> list[LeakReport]:
    """Return all leaking probes (empty list = PASS). Use as a CI gate."""
    reports = [await probe_leak(db, actor, foreign_dept, q) for q in queries]
    return [r for r in reports if r.leaked]
