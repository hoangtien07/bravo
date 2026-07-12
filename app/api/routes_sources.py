"""Source (document) routes: workspace upload + ingest + list/delete (RLS-filtered).

v2 three-tier workspace (ADR-0020): an upload defaults to a PERSONAL source (owner-only) —
any authenticated user may create one. Department/global tiers require the explicit create/
publish capability, authorized in `resolve_source_visibility`. Ingestion runs off the request
path via the arq worker (inline only under settings.ingest_sync for tests). List/detail/delete
enforce RLS in the SQL query.
"""
from __future__ import annotations

import hashlib
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import delete as sa_delete
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.database.models import Chunk, Source, SourceDepartment
from app.ingestion.pipeline import ingest_source
from app.queue import enqueue
from app.security.auth import get_current_identity, require_permission
from app.storage_paths import legacy_flat_path, workspace_path
from app.security.rls import (
    Identity,
    resolve_source_visibility,
    source_scope_filter,
)

router = APIRouter()
_settings = get_settings()
_CORPUS_DIR = Path("file_system")


def _locate_source_file(src: Source) -> Path | None:
    """Locate the original bytes: (1) v2 workspace layout; (2) legacy flat; (3) corpus rglob."""
    candidates = [
        workspace_path(src.id, src.filename, src.owner_id),
        legacy_flat_path(src.id, src.filename),
    ]
    for p in candidates:
        if p.exists():
            return p
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
    visibility: str = "personal"
    owned: bool = False           # True if the requester owns this personal source
    deduped: bool = False         # True when an identical prior upload was reused


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


async def _find_duplicate(db: AsyncSession, *, content_hash: str, visibility: str,
                          owner_id: uuid.UUID | None,
                          dept_ids: list[uuid.UUID]) -> Source | None:
    """Scope-aware dedup: reuse a prior identical upload only within the SAME scope, so two
    departments uploading the same bytes never collapse into one shared (leaky) Source."""
    rows = (await db.execute(
        select(Source).where(
            Source.content_hash == content_hash,
            Source.visibility == visibility,
            Source.owner_id.is_(owner_id) if owner_id is None else Source.owner_id == owner_id,
        )
    )).scalars().all()
    if visibility != "department":
        return rows[0] if rows else None
    want = set(dept_ids)
    for src in rows:
        existing = set((await db.execute(
            select(SourceDepartment.department_id).where(SourceDepartment.source_id == src.id)
        )).scalars().all())
        if existing == want:
            return src
    return None


@router.post("/sources", response_model=SourceOut, status_code=status.HTTP_201_CREATED)
async def upload_source(
    file: UploadFile,
    knowledge_type: str | None = Form(default=None),
    visibility: str = Form(default="personal"),
    department_ids: str | None = Form(default=None),
    shared: bool = Form(default=False),   # deprecated alias for visibility=global
    identity: Identity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
) -> SourceOut:
    if shared and visibility == "personal":
        visibility = "global"           # back-compat: old `shared=true` meant publish-global
    try:
        requested_department_ids = _parse_requested_department_ids(department_ids)
        resolved_vis, authorized_department_ids, owner_id = resolve_source_visibility(
            identity, visibility, requested_department_ids,
        )
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY,
                            "Phạm vi nguồn không hợp lệ hoặc chưa xác định") from exc
    except PermissionError as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN,
                            "Không có quyền tạo nguồn trong phạm vi này") from exc

    payload = await file.read()
    content_hash = hashlib.sha256(payload).hexdigest()

    dup = await _find_duplicate(db, content_hash=content_hash, visibility=resolved_vis,
                                owner_id=owner_id, dept_ids=authorized_department_ids)
    if dup is not None:
        return SourceOut(id=dup.id, filename=dup.filename, status=dup.status,
                         knowledge_type=dup.knowledge_type, visibility=dup.visibility,
                         owned=dup.owner_id == identity.employee_id, deduped=True)

    src = Source(filename=file.filename or "upload", knowledge_type=knowledge_type,
                 status="pending", visibility=resolved_vis, owner_id=owner_id,
                 content_hash=content_hash)
    db.add(src)
    await db.flush()  # get src.id

    for department_id in authorized_department_ids:
        db.add(SourceDepartment(source_id=src.id, department_id=department_id))

    dest = workspace_path(src.id, src.filename, owner_id)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(payload)
    await db.commit()

    # Ingest off the request path (arq worker). Inline only under ingest_sync (tests/dev).
    if _settings.ingest_sync:
        try:
            await ingest_source(db, src.id, str(dest), trusted_knowledge_type=None)
        except Exception as exc:  # noqa: BLE001
            src.status = "failed"
            await db.commit()
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY,
                                f"Ingest failed: {exc}") from exc
        await db.refresh(src)
    else:
        await enqueue("ingest_task", str(src.id), str(dest))

    return SourceOut(id=src.id, filename=src.filename, status=src.status,
                     knowledge_type=src.knowledge_type, visibility=src.visibility,
                     owned=owner_id == identity.employee_id)


@router.get("/sources", response_model=list[SourceOut])
async def list_sources(
    scope: str = "all",   # mine | department | global | all (narrows WITHIN rls scope)
    identity: Identity = Depends(require_permission("doc:read")),
    db: AsyncSession = Depends(get_db),
) -> list[SourceOut]:
    stmt = select(Source).where(source_scope_filter(identity, "read"))
    if scope == "mine":
        stmt = stmt.where(Source.visibility == "personal",
                          Source.owner_id == identity.employee_id)
    elif scope in {"department", "global"}:
        stmt = stmt.where(Source.visibility == scope)
    stmt = stmt.order_by(Source.created_at.desc())
    rows = (await db.execute(stmt)).scalars().all()
    return [SourceOut(id=s.id, filename=s.filename, status=s.status,
                      knowledge_type=s.knowledge_type, visibility=s.visibility,
                      owned=s.owner_id == identity.employee_id) for s in rows]


@router.delete("/sources/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_source(source_id: uuid.UUID,
                        identity: Identity = Depends(require_permission("doc:read")),
                        db: AsyncSession = Depends(get_db)) -> None:
    """Delete a source the requester controls: own personal source, or (for a
    doc:create:all publisher / admin) a department/global source. RLS-scoped lookup first."""
    src = (await db.execute(select(Source).where(
        Source.id == source_id, source_scope_filter(identity, "read")))).scalar_one_or_none()
    if src is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Nguồn không tồn tại hoặc ngoài phạm vi")
    owns_personal = src.visibility == "personal" and src.owner_id == identity.employee_id
    can_manage_shared = identity.is_admin or ("doc:create:all" in identity.permissions)
    if not (owns_personal or can_manage_shared):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Không có quyền xoá nguồn này")

    path = _locate_source_file(src)
    await db.execute(sa_delete(Chunk).where(Chunk.source_id == src.id))
    await db.execute(sa_delete(SourceDepartment).where(SourceDepartment.source_id == src.id))
    await db.execute(sa_delete(Source).where(Source.id == src.id))
    await db.commit()
    if path is not None and path.exists() and _CORPUS_DIR.resolve() not in path.resolve().parents:
        path.unlink(missing_ok=True)   # never delete corpus files


@router.get("/sources/{source_id}/file")
async def source_file(source_id: uuid.UUID,
                      identity: Identity = Depends(require_permission("doc:read")),
                      db: AsyncSession = Depends(get_db)) -> FileResponse:
    """Serve a source's original bytes (RLS-scoped) — inline in a browser tab."""
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
