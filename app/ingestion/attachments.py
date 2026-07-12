"""Chat-attachment extraction (v2 Track 3).

Text attachments (.txt/.md/.docx/.pdf) get their text extracted (reusing the ingestion
parser) and, if within the inject cap, stored on the row for full-text prompt injection.
Oversized text falls back to RAG: a PERSONAL Source is created and ingested so the chat
retrieves it via the normal personal-tier chunk scope. Images carry no extracted text —
the vision model sees the pixels at chat time.
"""
from __future__ import annotations

import uuid
from pathlib import Path

import tiktoken
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database.models import Attachment, Source

_settings = get_settings()
_enc = tiktoken.get_encoding("cl100k_base")

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
TEXT_EXTS = {".txt", ".md", ".markdown", ".docx", ".pdf"}


def classify_kind(filename: str, mime_type: str | None = None) -> str:
    """image | text, from mime first then extension."""
    if (mime_type or "").startswith("image/"):
        return "image"
    return "image" if Path(filename).suffix.lower() in IMAGE_EXTS else "text"


def extract_text(path: str) -> tuple[str, int]:
    """Extract plain text from a document via the ingestion parser; return (text, token_count)."""
    from app.ingestion.parser import parse

    blocks = parse(path)
    parts: list[str] = []
    for b in blocks:
        head = f"{b.heading_path}\n" if getattr(b, "heading_path", None) else ""
        parts.append(f"{head}{b.text}".strip())
    text = "\n\n".join(p for p in parts if p)
    return text, len(_enc.encode(text)) if text else 0


async def extract_attachment(db: AsyncSession, attachment_id: uuid.UUID) -> str:
    """Worker entry: fill an attachment's extracted text (or RAG-fallback for oversized).

    Returns the resulting status ("ready" | "failed"). Idempotent enough to retry.
    """
    att = await db.get(Attachment, attachment_id)
    if att is None:
        return "failed"
    if att.kind == "image":
        att.status = "ready"          # nothing to extract — pixels go to the vision model
        await db.commit()
        return "ready"
    try:
        text, tokens = extract_text(att.storage_path)
    except Exception as exc:  # noqa: BLE001
        att.status = "failed"
        att.error = f"extract: {exc}"[:500]
        await db.commit()
        return "failed"

    if tokens <= _settings.attachment_inject_token_cap:
        att.content = text
        att.token_count = tokens
        att.status = "ready"
        await db.commit()
        return "ready"

    # Oversized -> RAG fallback: personal Source owned by the uploader, ingested normally.
    from app.ingestion.pipeline import ingest_source

    src = Source(filename=att.filename, knowledge_type=None, status="pending",
                 visibility="personal", owner_id=att.owner_id)
    db.add(src)
    await db.flush()
    att.source_id = src.id
    att.content = None
    att.token_count = tokens
    await db.commit()
    try:
        await ingest_source(db, src.id, att.storage_path, trusted_knowledge_type=None)
    except Exception as exc:  # noqa: BLE001
        src.status = "failed"
        att.status = "failed"
        att.error = f"ingest: {exc}"[:500]
        await db.commit()
        return "failed"
    att.status = "ready"
    await db.commit()
    return "ready"
