"""API router aggregation."""
from __future__ import annotations

from fastapi import APIRouter

from app.api import (
    routes_admin,
    routes_agent,
    routes_agents,
    routes_ask,
    routes_auth,
    routes_conversations,
    routes_drafts,
    routes_graph,
    routes_invoices,
    routes_sources,
)

router = APIRouter()
router.include_router(routes_auth.router, tags=["auth"])
router.include_router(routes_admin.router, tags=["admin"])
router.include_router(routes_sources.router, tags=["knowledge"])
router.include_router(routes_graph.router, tags=["knowledge"])
router.include_router(routes_agents.router, tags=["agents"])
router.include_router(routes_ask.router, tags=["knowledge"])
router.include_router(routes_agent.router, tags=["agent"])
router.include_router(routes_conversations.router, tags=["chat"])
router.include_router(routes_invoices.router, tags=["money-engine"])
router.include_router(routes_drafts.router, tags=["drafts"])
