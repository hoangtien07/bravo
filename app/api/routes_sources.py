"""Source (document) routes: upload + ingest + list (RLS-filtered).

Upload scope is authorized before persistence.  The legacy empty-mapping shared
representation is accepted only for an explicit shared-publication request by a
``doc:create:all`` principal.  Ingestion runs the pipeline (parse -> chunk -> embed
-> store with the authorized scope). List enforces RLS in the query.
"""
from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.database.models import Source, SourceDepartment
from app.ingestion.pipeline import ingest_source
from app.security.auth import require_permission
from app.security.rls import Identity, resolve_source_write_scope, source_scope_filter

router = APIRouter()
_DATA_DIR = Path("data/uploads")
_CORPUS_DIR = Path("file_system")


def _locate_source_file(src: Source) -> Path | None:
    """Tìm file gốc: (1) file upload data/uploads/{id}_{tên}; (2) corpus file_system/**/{tên}."""
    up = _DATA_DIR / f"{src.id}_{src.filename}"
    if up.exists():
        return up
    if src.filename and _CORPUS_DIR.exists():
        for p in _CORPUS_DIR.rglob(src.filename):
            if p.is_file():
                return p
    return None


class SourceOut(BaseModel):
    id: uuid.UUID
    filename: str
    status: str
    knowledge_type: str | None = None


def _parse_requested_department_ids(raw: str | None) -> list[uuid.UUID]:
    """Parse caller-provided department IDs as a request, never as authority."""
    if not raw:
        return []
    out: list[uuid.UUID] = []
    for value in filter(None, (part.strip() for part in raw.split(","))):
        try:
            department_id = uuid.UUID(value)
        except ValueError as exc:
            raise ValueError("invalid department scope") from exc
        if department_id not in out:
            out.append(department_id)
    return out


@router.post("/sources", response_model=SourceOut, status_code=status.HTTP_201_CREATED)
async def upload_source(
    file: UploadFile,
    knowledge_type: str | None = Form(default=None),
    department_ids: str | None = Form(default=None),
    shared: bool = Form(default=False),
    identity: Identity = Depends(require_permission("doc:create")),
    db: AsyncSession = Depends(get_db),
) -> SourceOut:
    try:
        requested_department_ids = _parse_requested_department_ids(department_ids)
        authorized_department_ids = resolve_source_write_scope(
            identity, requested_department_ids, shared=shared,
        )
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY,
                            "Phạm vi nguồn không hợp lệ hoặc chưa xác định") from exc
    except PermissionError as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN,
                            "Không có quyền tạo nguồn trong phạm vi này") from exc

    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    src = Source(filename=file.filename or "upload", knowledge_type=knowledge_type, status="pending")
    db.add(src)
    await db.flush()  # get src.id

    for department_id in authorized_department_ids:
        db.add(SourceDepartment(source_id=src.id, department_id=department_id))

    dest = _DATA_DIR / f"{src.id}_{src.filename}"
    dest.write_bytes(await file.read())
    await db.commit()

    # MVP: ingest synchronously. For scale, enqueue ingest_task to the arq worker.
    try:
        # Caller `knowledge_type` is display metadata, not a trusted egress label.
        await ingest_source(db, src.id, str(dest), trusted_knowledge_type=None)
    except Exception as exc:  # noqa: BLE001
        src.status = "failed"
        await db.commit()
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, f"Ingest failed: {exc}") from exc

    await db.refresh(src)
    return SourceOut(id=src.id, filename=src.filename, status=src.status,
                     knowledge_type=src.knowledge_type)


@router.get("/sources", response_model=list[SourceOut])
async def list_sources(
    identity: Identity = Depends(require_permission("doc:read")),
    db: AsyncSession = Depends(get_db),
) -> list[SourceOut]:
    stmt = select(Source).where(source_scope_filter(identity, "read")).order_by(Source.created_at.desc())
    rows = (await db.execute(stmt)).scalars().all()
    return [SourceOut(id=s.id, filename=s.filename, status=s.status,
                      knowledge_type=s.knowledge_type) for s in rows]


@router.get("/sources/{source_id}/file")
async def source_file(source_id: uuid.UUID,
                      identity: Identity = Depends(require_permission("doc:read")),
                      db: AsyncSession = Depends(get_db)) -> FileResponse:
    """Phục vụ FILE gốc của một nguồn (RLS-scoped) — mở inline trong tab trình duyệt.

    RLS ở tầng SQL: chỉ trả nguồn người dùng được phép đọc (source_scope_filter). Dùng cho
    'bấm node bản đồ tri thức -> mở tài liệu gốc'.
    """
    src = (await db.execute(select(Source).where(
        Source.id == source_id, source_scope_filter(identity, "read")))).scalar_one_or_none()
    if src is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Nguồn không tồn tại hoặc ngoài phạm vi")
    path = _locate_source_file(src)
    if path is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Không tìm thấy file gốc: {src.filename}")
    media = "application/pdf" if str(path).lower().endswith(".pdf") else "application/octet-stream"
    return FileResponse(str(path), media_type=media, filename=src.filename,
                        content_disposition_type="inline")
