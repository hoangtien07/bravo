"""Source (document) routes: upload + ingest + list (RLS-filtered).

Upload scopes a source to departments (empty = global). Ingestion runs the pipeline
(parse -> chunk -> embed -> store with scope). List enforces RLS in the query.
"""
from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.database.models import Source, SourceDepartment
from app.ingestion.pipeline import ingest_source
from app.security.auth import require_permission
from app.security.rls import Identity, source_scope_filter

router = APIRouter()
_DATA_DIR = Path("data/uploads")


class SourceOut(BaseModel):
    id: uuid.UUID
    filename: str
    status: str
    knowledge_type: str | None = None


@router.post("/sources", response_model=SourceOut, status_code=status.HTTP_201_CREATED)
async def upload_source(
    file: UploadFile,
    knowledge_type: str | None = Form(default=None),
    department_ids: str = Form(default=""),  # comma-separated UUIDs; empty = global
    identity: Identity = Depends(require_permission("doc:create")),
    db: AsyncSession = Depends(get_db),
) -> SourceOut:
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    src = Source(filename=file.filename or "upload", knowledge_type=knowledge_type, status="pending")
    db.add(src)
    await db.flush()  # get src.id

    for raw in filter(None, (d.strip() for d in department_ids.split(","))):
        db.add(SourceDepartment(source_id=src.id, department_id=uuid.UUID(raw)))

    dest = _DATA_DIR / f"{src.id}_{src.filename}"
    dest.write_bytes(await file.read())
    await db.commit()

    # MVP: ingest synchronously. For scale, enqueue ingest_task to the arq worker.
    try:
        await ingest_source(db, src.id, str(dest))
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
