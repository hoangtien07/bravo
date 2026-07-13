"""Capability discovery for disabled-by-default frontier interaction surfaces."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.config import get_settings
from app.security.auth import get_current_identity
from app.security.rls import Identity

router = APIRouter()


@router.get("/frontier/capabilities")
async def frontier_capabilities(identity: Identity = Depends(get_current_identity)) -> dict:
    settings = get_settings()
    return {
        "realtime": {
            "enabled": settings.realtime_enabled,
            "model": settings.realtime_model if settings.realtime_enabled else None,
            "transport": "not_configured" if not settings.realtime_enabled else "deployment_broker_required",
        },
        "computer_use": {
            "enabled": settings.computer_use_enabled and (identity.is_admin or "computer:use" in identity.permissions),
            "mode": "proposal_only",
            "requires_approval_for_side_effects": True,
        },
    }
