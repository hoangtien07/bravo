"""Lean agent memory — core / recall / archival (MemGPT pattern, findings/J).

Rewritten from letta PATTERNS on BRAVO's OWN pgvector so RLS applies to archival memory
(letta keeps a separate store — harder to scope). NOT full Letta. Context-window
management (evict ~70% + summarize) is a follow-up TODO.
"""
from __future__ import annotations

import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.dialects.postgresql import array
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import ArchivalPassage, ConversationMessage, MemoryBlock
from app.rag.embedding import embed_one
from app.security.rls import Identity, frame_by_trust


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
    async def recall_add(self, role: str, content: str, *, trust_level: str = "trusted",
                         source: str | None = None) -> None:
        """Append a turn to recall memory.

        `trust_level`: "trusted" for the agent's own user/assistant turns; pass
        "untrusted" when persisting tool/document/ERP-derived text (it gets DATA-framed
        on recall so embedded directives can't change behaviour — WP-G).
        """
        self.db.add(ConversationMessage(
            session_id=self.session_id, role=role, content=content,
            trust_level=trust_level, source=source,
        ))
        await self.db.commit()

    async def recall_recent(self, limit: int = 20) -> list[ConversationMessage]:
        """Recent turns for THIS session only (RLS: session-scoped, no cross-session leak)."""
        rows = (await self.db.execute(
            select(ConversationMessage).where(ConversationMessage.session_id == self.session_id)
            .order_by(ConversationMessage.created_at.desc()).limit(limit)
        )).scalars().all()
        return list(reversed(rows))

    async def recall_recent_for_prompt(self, limit: int = 20) -> list[dict[str, str]]:
        """Recall turns prepared for the prompt: untrusted turns are DATA-framed.

        Returns role/content dicts ready for the message list. Untrusted content (e.g.
        persisted tool/document output) is wrapped so it cannot act as an instruction
        (memory-poisoning defense — deterministic, not LLM-judged; CONTRACTS §5).
        """
        rows = await self.recall_recent(limit)
        return [
            {"role": m.role,
             "content": frame_by_trust(m.content, m.trust_level, m.source)}
            for m in rows
        ]

    # --- archival memory (long-term, vector-searchable, RLS-scoped) ---
    async def archival_insert(self, content: str, tags: list[str] | None = None,
                              department_ids: list[uuid.UUID] | None = None,
                              *, trust_level: str = "untrusted",
                              source: str | None = None) -> None:
        """Insert an archival passage.

        Defaults to `trust_level="untrusted"`: archival content is document/ERP-derived
        and must be framed as DATA when recalled (WP-G). Pass "trusted" only for content
        the agent itself authored and vetted.
        """
        self.db.add(ArchivalPassage(
            owner_id=self.identity.employee_id, content=content, embedding=embed_one(content),
            tags=tags or [], department_ids=department_ids or [],
            trust_level=trust_level, source=source,
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

    async def archival_search_for_prompt(self, query: str, top_k: int = 5) -> list[str]:
        """RLS-scoped archival recall, each hit framed by its trust level for the prompt.

        Two hard controls stack here (Invariant #1 + WP-G): rows are filtered IN SQL by
        `_archival_scope` (no cross-dept leak), and untrusted hits are DATA-framed so
        injected instructions inside a passage are inert.
        """
        hits = await self.archival_search(query, top_k)
        return [frame_by_trust(p.content, p.trust_level, p.source) for p in hits]

    def _archival_scope(self):
        """RLS for archival (W2.1 — chống rò bộ nhớ riêng xuyên người dùng).

        Non-admin chỉ thấy: passage CỦA MÌNH (`owner_id == me`) HOẶC passage được CHIA SẺ
        tường minh tới phòng mình (`department_ids` overlap). Passage dept-RỖNG = bộ nhớ
        CÁ NHÂN của owner, KHÔNG còn coi là "global cho mọi người" (đó là lỗ rò cũ: cùng
        phòng đọc bộ nhớ riêng của nhau). Admin / doc:read:all = thấy tất cả.
        """
        if self.identity.is_admin or "doc:read:all" in self.identity.permissions:
            from sqlalchemy import true
            return true()
        mine = ArchivalPassage.owner_id == self.identity.employee_id
        if not self.identity.department_ids:
            return mine
        overlap = ArchivalPassage.department_ids.op("&&")(
            array(self.identity.department_ids, type_=ArchivalPassage.department_ids.type.item_type)
        )
        return or_(mine, overlap)
