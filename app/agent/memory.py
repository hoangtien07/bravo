"""Lean agent memory — core / recall / archival (MemGPT pattern, findings/J).

Rewritten from letta PATTERNS on BRAVO's OWN pgvector so RLS applies to archival memory
(letta keeps a separate store — harder to scope). NOT full Letta. Context-window
management (evict ~70% + summarize) is a follow-up TODO.
"""
from __future__ import annotations

import uuid

from sqlalchemy import or_, select
from sqlalchemy.dialects.postgresql import array
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import ArchivalPassage, ConversationMessage, MemoryBlock
from app.rag.embedding import embed_one
from app.security.rls import Identity


class MemoryStore:
    """Per-session memory operations. All archival reads are RLS-scoped."""

    def __init__(self, db: AsyncSession, session_id: uuid.UUID, identity: Identity):
        self.db = db
        self.session_id = session_id
        self.identity = identity

    # --- core memory (in-context, agent-editable) ---
    async def core_get(self, label: str) -> str:
        b = await self._block(label)
        return b.value if b else ""

    async def core_append(self, label: str, content: str) -> None:
        b = await self._block(label)
        if b is None:
            b = MemoryBlock(session_id=self.session_id, label=label, value=content)
            self.db.add(b)
        else:
            b.value = (b.value + "\n" + content)[: b.char_limit]
        await self.db.commit()

    async def core_replace(self, label: str, content: str) -> None:
        b = await self._block(label)
        if b is None:
            self.db.add(MemoryBlock(session_id=self.session_id, label=label, value=content))
        else:
            b.value = content[: b.char_limit]
        await self.db.commit()

    async def _block(self, label: str) -> MemoryBlock | None:
        return (await self.db.execute(
            select(MemoryBlock).where(MemoryBlock.session_id == self.session_id,
                                      MemoryBlock.label == label)
        )).scalar_one_or_none()

    # --- recall memory (conversation history) ---
    async def recall_add(self, role: str, content: str) -> None:
        self.db.add(ConversationMessage(session_id=self.session_id, role=role, content=content))
        await self.db.commit()

    async def recall_recent(self, limit: int = 20) -> list[ConversationMessage]:
        rows = (await self.db.execute(
            select(ConversationMessage).where(ConversationMessage.session_id == self.session_id)
            .order_by(ConversationMessage.created_at.desc()).limit(limit)
        )).scalars().all()
        return list(reversed(rows))

    # --- archival memory (long-term, vector-searchable, RLS-scoped) ---
    async def archival_insert(self, content: str, tags: list[str] | None = None,
                              department_ids: list[uuid.UUID] | None = None) -> None:
        self.db.add(ArchivalPassage(
            owner_id=self.identity.employee_id, content=content, embedding=embed_one(content),
            tags=tags or [], department_ids=department_ids or [],
        ))
        await self.db.commit()

    async def archival_search(self, query: str, top_k: int = 5) -> list[ArchivalPassage]:
        qvec = embed_one(query)
        stmt = (
            select(ArchivalPassage)
            .where(self._archival_scope())
            .order_by(ArchivalPassage.embedding.cosine_distance(qvec))
            .limit(top_k)
        )
        return list((await self.db.execute(stmt)).scalars().all())

    def _archival_scope(self):
        """RLS for archival: global (empty depts) OR overlap with identity depts. Admin = all."""
        if self.identity.is_admin or "doc:read:all" in self.identity.permissions:
            from sqlalchemy import true
            return true()
        is_global = ArchivalPassage.department_ids == []  # noqa: E711
        if not self.identity.department_ids:
            return is_global
        overlap = ArchivalPassage.department_ids.op("&&")(
            array(self.identity.department_ids, type_=ArchivalPassage.department_ids.type.item_type)
        )
        return or_(is_global, overlap)
