"""Chat / conversation API (P-chat): SSE streaming + CRUD + share + feedback.

RLS THEO NGƯỜI DÙNG: mọi endpoint hội thoại scope theo `identity.employee_id` (non-owner ->
404, không lộ tồn tại). Chia sẻ read-only qua shared_token (tra trực tiếp, không auth).
Streaming dùng POST + fetch ReadableStream (KHÔNG EventSource — vì bearer auth cần header).
"""
from __future__ import annotations

import asyncio
import json
import logging
import secrets
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import delete, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent import conversations as conv_svc
from app.agent.loop import AgentSession
from app.config import get_settings
from app.database import get_db
from app.database.models import AuditLog, Conversation, ConversationMessage, MemoryBlock
from app.ratelimit import chat_limit, limiter
from app.security.auth import get_current_identity, require_permission
from app.security.rls import Identity, conversation_scope_filter

router = APIRouter()
_log = logging.getLogger(__name__)

_DISPLAY_ROLES = ("user", "assistant")

# P1: per-conversation lock — two concurrent turns on the SAME conversation would interleave
# history/summary writes (audit S5). In-process only; multi-worker prod needs pg_advisory_xact_lock
# (documented in ADR-0024). F-12: prune unlocked entries so the map can't grow unbounded.
_conv_locks: dict[str, asyncio.Lock] = {}


def _conv_lock(session_id: uuid.UUID) -> asyncio.Lock:
    if len(_conv_locks) > 4096:
        for k in [k for k, v in _conv_locks.items() if not v.locked()]:
            _conv_locks.pop(k, None)
    key = str(session_id)
    lk = _conv_locks.get(key)
    if lk is None:
        lk = _conv_locks[key] = asyncio.Lock()
    return lk


class ChatIn(BaseModel):
    question: str
    attachment_ids: list[uuid.UUID] = []
    source_ids: list[uuid.UUID] = []   # P4-lite: GHIM tài liệu workspace vào ngữ cảnh lượt này


async def _load_attachment_payloads(
    db: AsyncSession, identity: Identity, conversation_id: uuid.UUID,
    attachment_ids: list[uuid.UUID],
) -> list[dict]:
    """Load this turn's attachments (owner-scoped, ready) + prior attachments of the conversation,
    and shape them for the agent loop. Foreign/unknown ids are silently dropped (RLS-in-SQL: no
    existence leak). Prior TEXT attachments are re-injected so the assistant keeps the document;
    images are re-sent for RECENT turns but capped at `attach_image_max` total (P1 / F-2 data
    minimization — each re-send is a fresh cloud egress of the same image).
    """
    import base64
    from pathlib import Path

    from app.database.models import Attachment

    settings = get_settings()
    payloads: list[dict] = []
    current: list[Attachment] = []
    if attachment_ids:
        current = list((await db.execute(
            select(Attachment).where(
                Attachment.id.in_(attachment_ids),
                Attachment.owner_id == identity.employee_id,
                Attachment.status == "ready",
            )
        )).scalars().all())
        # Bind to the conversation so prior turns can re-inject the attachment.
        for a in current:
            if a.conversation_id is None:
                a.conversation_id = conversation_id
        await db.commit()

    current_ids = [a.id for a in current]
    prior_text = list((await db.execute(
        select(Attachment).where(
            Attachment.conversation_id == conversation_id,
            Attachment.owner_id == identity.employee_id,
            Attachment.status == "ready",
            Attachment.kind == "text",
            Attachment.content.isnot(None),
            Attachment.id.notin_(current_ids) if current_ids else True,
        )
    )).scalars().all())

    # Recent prior images, filling whatever room remains under the per-prompt image cap.
    room = max(0, settings.attach_image_max - sum(1 for a in current if a.kind == "image"))
    prior_images: list[Attachment] = []
    if room:
        prior_images = list((await db.execute(
            select(Attachment).where(
                Attachment.conversation_id == conversation_id,
                Attachment.owner_id == identity.employee_id,
                Attachment.status == "ready",
                Attachment.kind == "image",
                Attachment.id.notin_(current_ids) if current_ids else True,
            ).order_by(Attachment.created_at.desc()).limit(room)
        )).scalars().all())

    def _img_payload(a: Attachment) -> dict | None:
        try:
            data = Path(a.storage_path).read_bytes()
        except OSError:
            return None
        b64 = base64.b64encode(data).decode()
        return {"kind": "image", "filename": a.filename,
                "data_url": f"data:{a.mime_type};base64,{b64}"}

    for a in current + prior_text:
        if a.kind == "text" and a.content:
            payloads.append({"kind": "text", "filename": a.filename, "content": a.content})
        elif a.kind == "image" and a in current:
            if (p := _img_payload(a)):
                payloads.append(p)
    for a in prior_images:
        if (p := _img_payload(a)):
            payloads.append(p)
    return payloads


class RenameIn(BaseModel):
    title: str


_FEEDBACK_CATEGORIES = {"wrong_number", "wrong_source", "unhelpful", "bug", "other"}


class FeedbackIn(BaseModel):
    value: str | None = None       # like|dislike|null
    comment: str | None = None     # P1: free-text "report to IT" (may contain personal data)
    category: str | None = None    # P1: one of _FEEDBACK_CATEGORIES


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
@limiter.limit(chat_limit)
async def chat_stream(request: Request, conversation_id: uuid.UUID, body: ChatIn,
                      identity: Identity = Depends(require_permission("doc:read")),
                      db: AsyncSession = Depends(get_db)):
    # Ownership: không được post vào session của người khác (chống forgery session_id).
    try:
        await conv_svc.ensure_conversation(db, conversation_id, identity.employee_id,
                                           first_question=body.question)
    except PermissionError as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(exc)) from exc

    attachments = await _load_attachment_payloads(
        db, identity, conversation_id, body.attachment_ids)

    session = AgentSession(db, identity, session_id=conversation_id)
    session.pinned_source_ids = body.source_ids   # P4-lite: pin workspace docs into this turn

    lock = _conv_lock(conversation_id)

    async def gen():
        import time as _time
        from app.observability import record_first_token, record_turn
        # P1: reject a second concurrent turn on the same conversation (no interleaved writes).
        if lock.locked():
            yield ("data: " + json.dumps(
                {"type": "error", "code": "busy",
                 "message": "Hội thoại đang xử lý một yêu cầu khác, vui lòng đợi."},
                ensure_ascii=False) + "\n\n")
            return
        async with lock:
            # ADR-0024: cross-worker guard (chỉ khi bật cờ) — chống hai tiến trình cùng hội thoại.
            adv = get_settings().use_pg_advisory_lock
            if adv:
                got = (await db.execute(
                    text("SELECT pg_try_advisory_lock(hashtext(:s))"),
                    {"s": str(conversation_id)})).scalar()
                if not got:
                    yield ("data: " + json.dumps(
                        {"type": "error", "code": "busy",
                         "message": "Hội thoại đang xử lý một yêu cầu khác, vui lòng đợi."},
                        ensure_ascii=False) + "\n\n")
                    return
            started = _time.monotonic()
            first_token_seen = False
            try:
                async for event in session.step_stream(body.question, attachments):
                    if not first_token_seen and event.get("type") == "answer":
                        first_token_seen = True
                        record_first_token(_time.monotonic() - started)   # Q7 gate: p95 < 3s
                    yield f"data: {json.dumps(event, ensure_ascii=False, default=str)}\n\n"
            except Exception:  # noqa: BLE001 — báo lỗi qua stream, không 500 giữa chừng
                # Sanitize: KHÔNG leak chi tiết nội bộ (SQL/key-adjacent/stacktrace) ra client (F-7).
                _log.exception("chat_stream failed for conversation %s", conversation_id)
                yield (
                    "data: "
                    + json.dumps(
                        {"type": "error",
                         "message": "Đã xảy ra lỗi khi xử lý yêu cầu. Vui lòng thử lại."},
                        ensure_ascii=False,
                    )
                    + "\n\n"
                )
            finally:
                record_turn(_time.monotonic() - started)   # F5: turn-latency histogram
                if adv:
                    try:
                        await db.execute(text("SELECT pg_advisory_unlock(hashtext(:s))"),
                                         {"s": str(conversation_id)})
                    except Exception:  # noqa: BLE001
                        pass
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
    # F-6 (PDPL erasure): also remove conversation-bound attachments + their files on disk.
    from pathlib import Path

    from app.database.models import Attachment
    atts = list((await db.execute(select(Attachment).where(
        Attachment.conversation_id == conversation_id))).scalars().all())
    for a in atts:
        if a.storage_path:
            try:
                Path(a.storage_path).unlink(missing_ok=True)
            except OSError:
                _log.warning("could not delete attachment file %s", a.storage_path)
    await db.execute(delete(Attachment).where(Attachment.conversation_id == conversation_id))
    await db.execute(delete(ConversationMessage).where(
        ConversationMessage.session_id == conversation_id))
    await db.execute(delete(MemoryBlock).where(MemoryBlock.session_id == conversation_id))
    await db.delete(conv)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


class TruncateIn(BaseModel):
    from_message_id: uuid.UUID
    inclusive: bool = True   # True: xoá cả tin mốc (regenerate assistant / edit user)


@router.post("/conversations/{conversation_id}/truncate")
async def truncate_conversation(conversation_id: uuid.UUID, body: TruncateIn,
                                identity: Identity = Depends(get_current_identity),
                                db: AsyncSession = Depends(get_db)) -> dict:
    """ADR-0026: cắt hội thoại từ một tin nhắn trở đi (nền cho regenerate/edit tuyến tính).

    Cắt theo `seq` (thứ tự tuyệt đối, không đụng độ như created_at). Ghi AuditLog (actor, session,
    message_ids, content sha256) — sửa/hỏi lại KHÔNG được xoá sạch dấu vết tuân thủ (F-3). Xoá
    summary MemoryBlocks (reset watermark, khớp B1 S3) + clear conversation_id của attachment thuộc
    tin bị cắt (không thì re-inject mãi). Chạy dưới khoá per-conversation (không đua với lượt đang chạy).
    """
    import hashlib

    from app.database.models import Attachment
    await _owned(db, conversation_id, identity)
    lock = _conv_lock(conversation_id)
    if lock.locked():
        raise HTTPException(status.HTTP_409_CONFLICT, "Hội thoại đang xử lý một yêu cầu khác.")
    async with lock:
        target = (await db.execute(select(ConversationMessage).where(
            ConversationMessage.id == body.from_message_id,
            ConversationMessage.session_id == conversation_id))).scalar_one_or_none()
        if target is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Tin nhắn không tồn tại")
        cond = (ConversationMessage.seq >= target.seq if body.inclusive
                else ConversationMessage.seq > target.seq)
        doomed = list((await db.execute(select(ConversationMessage).where(
            ConversationMessage.session_id == conversation_id, cond)
            .order_by(ConversationMessage.seq))).scalars().all())
        if not doomed:
            return {"deleted": 0}
        doomed_ids = [m.id for m in doomed]
        db.add(AuditLog(actor_id=identity.employee_id, action="conversation.truncate", detail={
            "session_id": str(conversation_id), "count": len(doomed_ids),
            "message_ids": [str(i) for i in doomed_ids],
            "content_sha256": [hashlib.sha256((m.content or "").encode()).hexdigest() for m in doomed],
        }))
        # Attachments bound to a doomed turn: unbind from the conversation so they stop re-injecting.
        await db.execute(update(Attachment)
                         .where(Attachment.message_id.in_(doomed_ids))
                         .values(conversation_id=None))
        # Rolling-summary is now wrong (covered deleted turns) -> reset watermark.
        await db.execute(delete(MemoryBlock).where(
            MemoryBlock.session_id == conversation_id,
            MemoryBlock.label.in_(("summary", "summary_upto", "summary_n"))))
        await db.execute(delete(ConversationMessage).where(
            ConversationMessage.id.in_(doomed_ids)))
        await db.commit()
    return {"deleted": len(doomed_ids)}


@router.post("/conversations/{conversation_id}/share")
async def share_conversation(conversation_id: uuid.UUID,
                             identity: Identity = Depends(get_current_identity),
                             db: AsyncSession = Depends(get_db)) -> dict:
    conv = await _owned(db, conversation_id, identity)
    if not conv.shared_token:
        conv.shared_token = secrets.token_urlsafe(32)
        await db.commit()
    return {"shared_token": conv.shared_token, "url": f"/shared/{conv.shared_token}"}


@router.delete("/conversations/{conversation_id}/share", status_code=status.HTTP_204_NO_CONTENT)
async def unshare_conversation(conversation_id: uuid.UUID,
                               identity: Identity = Depends(get_current_identity),
                               db: AsyncSession = Depends(get_db)) -> Response:
    """P1 share governance: revoke the public link (rotate to None). Any held token stops working."""
    conv = await _owned(db, conversation_id, identity)
    conv.shared_token = None
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/shared/{token}")
@limiter.limit(chat_limit)   # P1: throttle the unauthenticated share endpoint
async def shared_conversation(request: Request, token: str,
                              db: AsyncSession = Depends(get_db)) -> dict:
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
    if body.comment is not None:                        # P1 report-to-IT (F-9: cap length)
        msg.feedback_comment = (body.comment.strip()[:2000]) or None
    if body.category is not None:
        cat = body.category.strip().lower()
        msg.feedback_category = cat if cat in _FEEDBACK_CATEGORIES else "other"
    await db.commit()
    return {"ok": True, "feedback": msg.feedback,
            "comment": msg.feedback_comment, "category": msg.feedback_category}
