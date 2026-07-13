"""Read-only artifact workspace API."""
from __future__ import annotations

import re
import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent import artifacts
from app.database import get_db
from app.security.auth import get_current_identity
from app.security.rls import Identity

router = APIRouter()


def _out(item) -> dict:
    return {"id": str(item.id), "agent_run_id": str(item.agent_run_id) if item.agent_run_id else None,
            "kind": item.kind, "title": item.title, "mime_type": item.mime_type,
            "provenance": item.provenance or {}, "status": item.status, "created_at": item.created_at}


@router.get("/artifacts")
async def list_artifacts(identity: Identity = Depends(get_current_identity),
                         db: AsyncSession = Depends(get_db)) -> list[dict]:
    return [_out(item) for item in await artifacts.list_artifacts(db, identity)]


@router.get("/artifacts/{artifact_id}")
async def get_artifact(artifact_id: uuid.UUID, identity: Identity = Depends(get_current_identity),
                       db: AsyncSession = Depends(get_db)) -> dict:
    item = await artifacts.get_artifact(db, artifact_id, identity)
    if item is None:
        raise HTTPException(status_code=404, detail="Artifact không tồn tại hoặc ngoài phạm vi")
    return {**_out(item), "content": item.content}


@router.get("/artifacts/{artifact_id}/download")
async def download_artifact(artifact_id: uuid.UUID, identity: Identity = Depends(get_current_identity),
                            db: AsyncSession = Depends(get_db)) -> Response:
    item = await artifacts.get_artifact(db, artifact_id, identity)
    if item is None or item.content is None:
        raise HTTPException(status_code=404, detail="Artifact không có nội dung tải xuống")
    filename = re.sub(r"[^A-Za-z0-9._ -]", "_", item.title).strip(". ") or "artifact.md"
    return Response(item.content, media_type=item.mime_type,
                    headers={"Content-Disposition": f'attachment; filename="{filename}"'})
