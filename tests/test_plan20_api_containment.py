"""Plan 20: forbidden ERP/draft surfaces are absent from the default product router."""
from __future__ import annotations

import pytest

from app.agent.loop import _register_builtin_tools
from app.agent.tools import REGISTRY
from app.api import routes_frontier
from app.config import Settings, get_settings
from app.main import app
from app.security.auth import require_admin


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


def test_forbidden_paths_are_not_callable_through_the_api_prefix():
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        for path in FORBIDDEN_PATHS:
            assert client.get(path).status_code == 404
            assert client.post(path).status_code == 404


def test_frontier_capability_discovery_is_internal_admin_only():
    frontier = next(route for route in routes_frontier.router.routes if route.path == "/frontier/capabilities")
    assert frontier.dependant.dependencies[0].call is require_admin


def test_default_tool_inventory_has_no_journal_or_draft_tool():
    _register_builtin_tools()
    assert {"create_journal_entry", "list_drafts", "preview_journal_entry"}.isdisjoint(REGISTRY)


def test_plan20_legacy_surface_switch_defaults_to_disabled():
    assert get_settings().plan20_legacy_erp_surfaces_enabled is False


def test_plan20_boot_guards_reject_legacy_erp_in_nonlocal_and_computer_use_everywhere():
    with pytest.raises(ValueError, match="PLAN20_LEGACY_ERP_SURFACES_ENABLED"):
        Settings(env="staging", plan20_legacy_erp_surfaces_enabled=True).validate_boot()
    with pytest.raises(ValueError, match="computer_use_enabled"):
        Settings(env="local", computer_use_enabled=True).validate_boot()
