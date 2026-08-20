"""Capability discovery for disabled-by-default frontier interaction surfaces."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.config import get_settings
from app.security.auth import require_admin
from app.security.rls import Identity

router = APIRouter()


@router.get("/frontier/capabilities")
async def frontier_capabilities(identity: Identity = Depends(require_admin)) -> dict:
    settings = get_settings()
    return {
        "realtime": {
            "enabled": settings.realtime_enabled,
            "model": settings.realtime_model if settings.realtime_enabled else None,
            "transport": "not_configured" if not settings.realtime_enabled else "deployment_broker_required",
        },
        "computer_use": {
            "enabled": False,
            "mode": "removed_by_plan20",
            "requires_approval_for_side_effects": False,
        },
    }
