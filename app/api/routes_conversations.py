"""Chat / conversation API (P-chat): SSE streaming + CRUD + share + feedback.

RLS THEO NGƯỜI DÙNG: mọi endpoint hội thoại scope theo `identity.employee_id` (non-owner ->
404, không lộ tồn tại). Chia sẻ read-only qua shared_token (tra trực tiếp, không auth).
Streaming dùng POST + fetch ReadableStream (KHÔNG EventSource — vì bearer auth cần header).
"""
from __future__ import annotations

import json
import secrets
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent import conversations as conv_svc
from app.agent.loop import AgentSession
from app.database import get_db
from app.database.models import Conversation, ConversationMessage, MemoryBlock
from app.security.auth import get_current_identity, require_permission
from app.security.rls import Identity, conversation_scope_filter

router = APIRouter()

_DISPLAY_ROLES = ("user", "assistant")


class ChatIn(BaseModel):
    question: str


class RenameIn(BaseModel):
    title: str


class FeedbackIn(BaseModel):
    value: str | None  # like|dislike|null


def _msg_dict(m: ConversationMessage) -> dict:
    return {"id": str(m.id), "role": m.role, "content": m.content,
            "created_at": m.created_at, "feedback": m.feedback}


async def _owned(db: AsyncSession, conv_id: uuid.UUID, identity: Identity) -> Conversation:
    conv = (await db.execute(select(Conversation).where(
        Conversation.id == conv_id, conversation_scope_filter(identity)))).scalar_one_or_none()
    if conv is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Hội thoại không tồn tại hoặc ngoài phạm vi")
    return conv


async def _messages(db: AsyncSession, conv_id: uuid.UUID) -> list[ConversationMessage]:
    return list((await db.execute(
        select(ConversationMessage).where(
            ConversationMessage.session_id == conv_id,
            ConversationMessage.role.in_(_DISPLAY_ROLES))
        .order_by(ConversationMessage.created_at))).scalars().all())


# --------------------------------------------------------------------------------------
# Streaming chat turn (SSE).
# --------------------------------------------------------------------------------------
@router.post("/chat/{conversation_id}/messages")
async def chat_stream(conversation_id: uuid.UUID, body: ChatIn,
                      identity: Identity = Depends(require_permission("doc:read")),
                      db: AsyncSession = Depends(get_db)):
    # Ownership: không được post vào session của người khác (chống forgery session_id).
    try:
        await conv_svc.ensure_conversation(db, conversation_id, identity.employee_id,
                                           first_question=body.question)
    except PermissionError as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(exc)) from exc

    session = AgentSession(db, identity, session_id=conversation_id)

    async def gen():
        try:
            async for event in session.step_stream(body.question):
                yield f"data: {json.dumps(event, ensure_ascii=False, default=str)}\n\n"
        except Exception as exc:  # noqa: BLE001 — báo lỗi qua stream, không 500 giữa chừng
            yield f"data: {json.dumps({'type': 'error', 'message': str(exc)})}\n\n"
        finally:
            try:
                await conv_svc.touch(db, conversation_id)
            except Exception:  # noqa: BLE001
                pass

    return StreamingResponse(gen(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


# --------------------------------------------------------------------------------------
# Conversation CRUD (owner-scoped).
# --------------------------------------------------------------------------------------
@router.get("/conversations")
async def list_conversations(identity: Identity = Depends(get_current_identity),
                             db: AsyncSession = Depends(get_db)) -> list[dict]:
    rows = (await db.execute(
        select(Conversation).where(conversation_scope_filter(identity))
        .order_by(Conversation.last_message_at.desc().nullslast(),
                  Conversation.created_at.desc()).limit(30))).scalars().all()
    return [{"id": str(c.id), "title": c.title, "last_message_at": c.last_message_at,
             "created_at": c.created_at} for c in rows]


@router.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: uuid.UUID,
                           identity: Identity = Depends(get_current_identity),
                           db: AsyncSession = Depends(get_db)) -> dict:
    conv = await _owned(db, conversation_id, identity)
    return {"id": str(conv.id), "title": conv.title,
            "messages": [_msg_dict(m) for m in await _messages(db, conversation_id)]}


@router.post("/conversations/{conversation_id}/rename")
async def rename_conversation(conversation_id: uuid.UUID, body: RenameIn,
                              identity: Identity = Depends(get_current_identity),
                              db: AsyncSession = Depends(get_db)) -> dict:
    conv = await _owned(db, conversation_id, identity)
    conv.title = (body.title or "").strip()[:200] or conv.title
    await db.commit()
    return {"id": str(conv.id), "title": conv.title}


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(conversation_id: uuid.UUID,
                              identity: Identity = Depends(get_current_identity),
                              db: AsyncSession = Depends(get_db)) -> Response:
    conv = await _owned(db, conversation_id, identity)
    await db.execute(delete(ConversationMessage).where(
        ConversationMessage.session_id == conversation_id))
    await db.execute(delete(MemoryBlock).where(MemoryBlock.session_id == conversation_id))
    await db.delete(conv)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/conversations/{conversation_id}/share")
async def share_conversation(conversation_id: uuid.UUID,
                             identity: Identity = Depends(get_current_identity),
                             db: AsyncSession = Depends(get_db)) -> dict:
    conv = await _owned(db, conversation_id, identity)
    if not conv.shared_token:
        conv.shared_token = secrets.token_urlsafe(32)
        await db.commit()
    return {"shared_token": conv.shared_token, "url": f"/shared/{conv.shared_token}"}


@router.get("/shared/{token}")
async def shared_conversation(token: str, db: AsyncSession = Depends(get_db)) -> dict:
    # Bypass RLS có kiểm soát: tra theo shared_token (256-bit), read-only, KHÔNG lộ employee_id.
    conv = (await db.execute(select(Conversation).where(
        Conversation.shared_token == token))).scalar_one_or_none()
    if conv is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Liên kết chia sẻ không hợp lệ")
    return {"title": conv.title,
            "messages": [_msg_dict(m) for m in await _messages(db, conv.id)]}


@router.post("/conversations/{conversation_id}/messages/{message_id}/feedback")
async def set_feedback(conversation_id: uuid.UUID, message_id: uuid.UUID, body: FeedbackIn,
                       identity: Identity = Depends(get_current_identity),
                       db: AsyncSession = Depends(get_db)) -> dict:
    await _owned(db, conversation_id, identity)  # owns parent conversation
    msg = (await db.execute(select(ConversationMessage).where(
        ConversationMessage.id == message_id,
        ConversationMessage.session_id == conversation_id))).scalar_one_or_none()
    if msg is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tin nhắn không tồn tại")
    msg.feedback = body.value if body.value in ("like", "dislike") else None
    await db.commit()
    return {"ok": True, "feedback": msg.feedback}
