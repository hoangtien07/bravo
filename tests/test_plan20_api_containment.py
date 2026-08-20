"""Plan 20: forbidden ERP/draft surfaces are absent from the default product router."""
from __future__ import annotations

from app.agent.loop import _register_builtin_tools
from app.agent.tools import REGISTRY
from app.config import get_settings
from app.main import app


FORBIDDEN_PATHS = {
    "/api/connectors",
    "/api/drafts",
    "/api/drafts/export",
    "/api/invoices/draft",
    "/api/agents/anomaly/scan",
    "/api/agents/tax/reconcile",
    "/api/graph",
}


def test_default_router_has_no_legacy_erp_or_generic_tool_paths():
    paths = set(app.openapi()["paths"])
    assert FORBIDDEN_PATHS.isdisjoint(paths)


def test_default_tool_inventory_has_no_journal_or_draft_tool():
    _register_builtin_tools()
    assert {"create_journal_entry", "list_drafts", "preview_journal_entry"}.isdisjoint(REGISTRY)


def test_plan20_legacy_surface_switch_defaults_to_disabled():
    assert get_settings().plan20_legacy_erp_surfaces_enabled is False
