"""API router aggregation."""
from __future__ import annotations

from fastapi import APIRouter

from app.api import (
    routes_admin,
    routes_accounting_cases_v2,
    routes_agent,
    routes_artifacts,
    routes_ask,
    routes_attachments,
    routes_auth,
    routes_conversations,
    routes_consultant,
    routes_frontier,
    routes_oidc,
    routes_runs,
    routes_sources,
)
from app.config import get_settings

router = APIRouter()
router.include_router(routes_auth.router, tags=["auth"])
router.include_router(routes_oidc.router, tags=["auth"])
router.include_router(routes_admin.router, tags=["admin"])
router.include_router(routes_sources.router, tags=["knowledge"])
router.include_router(routes_ask.router, tags=["knowledge"])
router.include_router(routes_agent.router, tags=["agent"])
router.include_router(routes_conversations.router, tags=["chat"])
router.include_router(routes_consultant.router, tags=["consultant"])
router.include_router(routes_frontier.router, tags=["frontier"])
router.include_router(routes_runs.router, tags=["agent-runs"])
router.include_router(routes_artifacts.router, tags=["artifacts"])
router.include_router(routes_attachments.router, tags=["chat"])
router.include_router(routes_accounting_cases_v2.router, tags=["accounting-cases-v2"])

# Kept only for a controlled, local rollback while historical records are retained.  The default
# standalone product has no connector, draft/journal, generic anomaly/tax, or graph API family.
if get_settings().plan20_legacy_erp_surfaces_enabled:
    from app.api import routes_agents, routes_connectors, routes_drafts, routes_graph, routes_invoices

    router.include_router(routes_graph.router, tags=["legacy-knowledge"])
    router.include_router(routes_agents.router, tags=["legacy-agents"])
    router.include_router(routes_connectors.router, tags=["legacy-connectors"])
    router.include_router(routes_invoices.router, tags=["legacy-money-engine"])
    router.include_router(routes_drafts.router, tags=["legacy-drafts"])
