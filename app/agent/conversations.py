"""Vòng đời hội thoại (P-chat) — upsert + ownership + cập nhật last_message_at.

`Conversation.id == session_id` (1:1). Ownership là HARD check: một người dùng KHÔNG
được post vào session của người khác (chống forgery session_id). Title tự sinh từ câu hỏi
đầu (deterministic, không gọi LLM).
"""
from __future__ import annotations

import uuid

from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Conversation


def make_title(question: str) -> str:
    title = " ".join((question or "").strip().split()[:8])[:48]
    return title or "Hội thoại mới"


async def ensure_conversation(db: AsyncSession, session_id: uuid.UUID, employee_id: uuid.UUID,
                              *, first_question: str | None = None) -> Conversation:
    """Upsert conversation row. Đã tồn tại mà chủ KHÁC -> PermissionError (hard)."""
    # Scope the lookup in SQL; never fetch a foreign conversation and filter it in memory.
    conv = (await db.execute(select(Conversation).where(
        Conversation.id == session_id,
        Conversation.employee_id == employee_id,
    ))).scalar_one_or_none()
    if conv is not None:
        return conv

    conv = Conversation(id=session_id, employee_id=employee_id,
                        title=make_title(first_question or ""))
    db.add(conv)
    try:
        await db.commit()
    except IntegrityError:
        # The id either belongs to another owner or a concurrent request created it. Re-query
        # only within the caller's scope; a foreign row remains indistinguishable from absent.
        await db.rollback()
        conv = (await db.execute(select(Conversation).where(
            Conversation.id == session_id,
            Conversation.employee_id == employee_id,
        ))).scalar_one_or_none()
        if conv is None:
            raise PermissionError("Hội thoại không tồn tại hoặc ngoài phạm vi")
        return conv
    await db.refresh(conv)
    return conv


async def touch(db: AsyncSession, session_id: uuid.UUID) -> None:
    """Cập nhật last_message_at (cho sidebar sắp xếp theo gần nhất)."""
    await db.execute(update(Conversation).where(Conversation.id == session_id)
                     .values(last_message_at=func.now()))
    await db.commit()
