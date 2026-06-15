"""API router aggregation."""
from __future__ import annotations

from fastapi import APIRouter

from app.api import (
    routes_agent,
    routes_ask,
    routes_auth,
    routes_drafts,
    routes_invoices,
    routes_sources,
)

router = APIRouter()
router.include_router(routes_auth.router, tags=["auth"])
router.include_router(routes_sources.router, tags=["knowledge"])
router.include_router(routes_ask.router, tags=["knowledge"])
router.include_router(routes_agent.router, tags=["agent"])
router.include_router(routes_invoices.router, tags=["money-engine"])
router.include_router(routes_drafts.router, tags=["drafts"])
