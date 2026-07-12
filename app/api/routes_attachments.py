"""Chat-attachment routes (v2 Track 3): upload / status / delete — strictly owner-scoped.

An attachment is personal by construction (no departments). Upload validates type + size,
stores the bytes, then either extracts inline (images = nothing to extract; small text = fast
path) or enqueues the extraction worker. Chat consumes ready attachments by id (routes_conversations).
"""
from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy import delete as sa_delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.database.models import Attachment
from app.ingestion.attachments import IMAGE_EXTS, TEXT_EXTS, classify_kind, extract_attachment
from app.queue import enqueue
from app.ratelimit import chat_limit, limiter
from app.security.auth import get_current_identity
from app.security.rls import Identity
from app.storage_paths import attachment_path

router = APIRouter()
_settings = get_settings()
_INLINE_TEXT_MAX = 2 * 1024 * 1024   # small text extracts inline (fast path)


class AttachmentOut(BaseModel):
    id: uuid.UUID
    filename: str
    mime_type: str
    size_bytes: int
    kind: str
    status: str
    token_count: int = 0
    error: str | None = None


def _out(a: Attachment) -> AttachmentOut:
    return AttachmentOut(id=a.id, filename=a.filename, mime_type=a.mime_type,
                         size_bytes=a.size_bytes, kind=a.kind, status=a.status,
                         token_count=a.token_count, error=a.error)


@router.post("/attachments", response_model=AttachmentOut, status_code=status.HTTP_201_CREATED)
@limiter.limit(chat_limit)   # F2: image upload triggers inline vision extraction -> throttle abuse/cost
async def upload_attachment(
    request: Request,
    file: UploadFile,
    identity: Identity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
) -> AttachmentOut:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in (IMAGE_EXTS | TEXT_EXTS):
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                            f"Định dạng không hỗ trợ: {suffix or '(không rõ)'}")
    payload = await file.read()
    if len(payload) > _settings.attachment_max_bytes:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                            "Tệp vượt quá kích thước cho phép")

    kind = classify_kind(file.filename or "upload", file.content_type)
    att = Attachment(
        owner_id=identity.employee_id, filename=file.filename or "upload",
        mime_type=file.content_type or "application/octet-stream", size_bytes=len(payload),
        storage_path="", kind=kind, status="pending",
    )
    db.add(att)
    await db.flush()
    dest = attachment_path(att.id, identity.employee_id, att.filename)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(payload)
    att.storage_path = str(dest)
    await db.commit()

    inline = (
        _settings.ingest_sync
        or kind == "image"
        or (suffix in {".txt", ".md", ".markdown"} and len(payload) <= _INLINE_TEXT_MAX)
    )
    if inline:
        await extract_attachment(db, att.id)
        await db.refresh(att)
    else:
        await enqueue("attachment_extract_task", str(att.id))
    return _out(att)


@router.get("/attachments/{attachment_id}", response_model=AttachmentOut)
async def get_attachment(attachment_id: uuid.UUID,
                         identity: Identity = Depends(get_current_identity),
                         db: AsyncSession = Depends(get_db)) -> AttachmentOut:
    att = await _load_owned(db, attachment_id, identity)
    return _out(att)


@router.delete("/attachments/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_attachment(attachment_id: uuid.UUID,
                            identity: Identity = Depends(get_current_identity),
                            db: AsyncSession = Depends(get_db)) -> None:
    att = await _load_owned(db, attachment_id, identity)
    path = Path(att.storage_path) if att.storage_path else None
    await db.execute(sa_delete(Attachment).where(Attachment.id == att.id))
    await db.commit()
    if path is not None and path.exists():
        path.unlink(missing_ok=True)


async def _load_owned(db: AsyncSession, attachment_id: uuid.UUID,
                      identity: Identity) -> Attachment:
    """Owner-scoped fetch in SQL (admin bypass). Foreign ids 404 — no existence leak."""
    stmt = select(Attachment).where(Attachment.id == attachment_id)
    if not identity.is_admin:
        stmt = stmt.where(Attachment.owner_id == identity.employee_id)
    att = (await db.execute(stmt)).scalar_one_or_none()
    if att is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tệp đính kèm không tồn tại")
    return att
