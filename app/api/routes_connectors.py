"""Caller-visible connector catalog; no adapter is invoked from this endpoint."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.connectors.registry import available_connectors
from app.security.auth import get_current_identity
from app.security.rls import Identity

router = APIRouter()


@router.get("/connectors")
async def list_connectors(identity: Identity = Depends(get_current_identity)) -> list[dict]:
    return [
        {
            "id": item.id,
            "title": item.title,
            "kind": item.kind,
            "operations": list(item.operations),
            "data_classification": item.data_classification,
            "requires_approval": item.requires_approval,
        }
        for item in available_connectors(identity)
    ]
