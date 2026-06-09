"""Lean agent loop — assembles memory + knowledge + router + draft (Phase 2).

Ties the pieces together (rewritten from letta patterns, not full Letta):
  core/recall memory  ->  context
  RLS-scoped retrieval ->  grounded knowledge
  Model Router (local default, fail-closed)  ->  answer
  write actions        ->  drafts (requires_approval, never auto-executed)

The full LLM tool-calling protocol (model decides which tool) is the integration point
with the local model's function-calling API — `call_tool` is ready for it.
"""
from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.memory import MemoryStore
from app.agent.tools import REGISTRY
from app.erp import draft_queue
from app.llm import router as llm
from app.rag import retriever
from app.security.rls import Identity

_SYSTEM = (
    "Bạn là BRAVO AI Copilot. Trả lời CHỈ dựa trên NGỮ CẢNH (tri thức + bộ nhớ) được cung cấp; "
    "không bịa, đặc biệt KHÔNG bịa số liệu. Thiếu căn cứ thì nói không biết. Trả lời tiếng Việt, có trích dẫn."
)


class AgentSession:
    def __init__(self, db: AsyncSession, identity: Identity, session_id: uuid.UUID | None = None):
        self.db = db
        self.identity = identity
        self.session_id = session_id or uuid.uuid4()
        self.memory = MemoryStore(db, self.session_id, identity)

    async def _context(self, question: str) -> str:
        parts: list[str] = []
        persona = await self.memory.core_get("nguoi_dung")
        if persona:
            parts.append(f"[Bộ nhớ người dùng]\n{persona}")
        chunks = await retriever.retrieve(self.db, self.identity, question, top_n=6)
        if chunks:
            parts.append("[Tri thức]\n" + "\n\n".join(
                f"{c.content}\n{c.citation()}" for c in chunks))
        return "\n\n".join(parts), chunks

    async def step(self, user_message: str) -> dict:
        """One conversational turn: retrieve + answer (grounded) + persist to recall."""
        await self.memory.recall_add("user", user_message)
        context, chunks = await self._context(user_message)
        if not chunks:
            answer = "Tôi không tìm thấy thông tin này trong tài liệu bạn được phép truy cập."
            await self.memory.recall_add("assistant", answer)
            return {"answer": answer, "grounded": False, "citations": []}

        history = await self.memory.recall_recent(limit=10)
        messages = [{"role": "system", "content": _SYSTEM}]
        messages += [{"role": m.role, "content": m.content} for m in history if m.role in ("user", "assistant")]
        messages.append({"role": "user", "content": f"NGỮ CẢNH:\n{context}\n\nCÂU HỎI: {user_message}"})

        # sensitive=None -> Model Router fails closed to local LLM (data stays on-prem).
        answer, _decision = await llm.chat(messages, sensitive=None, temperature=0.1)
        await self.memory.recall_add("assistant", answer)
        return {
            "answer": answer,
            "grounded": True,
            "citations": [c.citation() for c in chunks],
            "session_id": str(self.session_id),
        }

    async def call_tool(self, name: str, payload: dict) -> dict:
        """Execute a registered tool. Write tools (requires_approval) -> draft, not executed."""
        tool = REGISTRY.get(name)
        if tool is None:
            return {"error": f"Tool không tồn tại: {name}"}
        if tool.requires_approval:
            draft = await draft_queue.create_draft(self.db, self.identity, kind=name, payload=payload)
            return {"status": "pending_approval", "draft_id": str(draft.id),
                    "message": "Đã tạo bản nháp chờ người duyệt (không tự thực thi)."}
        return {"status": "ok", "result": await _maybe_await(tool.fn(**payload))}


async def _maybe_await(value):
    import inspect
    return await value if inspect.isawaitable(value) else value
