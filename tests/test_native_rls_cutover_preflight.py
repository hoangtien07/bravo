from __future__ import annotations

from scripts.verify_native_rls_cutover import cutover_failures


def _ready_role():
    return {"rolsuper": False, "rolbypassrls": False}


def _ready_table():
    return {"is_owner": False, "relrowsecurity": True, "relforcerowsecurity": True}


def test_cutover_preflight_accepts_only_a_non_owner_enforced_runtime(monkeypatch):
    monkeypatch.setenv("NATIVE_RLS_ENABLED", "true")
    assert cutover_failures(_ready_role(), _ready_table(), has_policy=True) == []


def test_cutover_preflight_rejects_owner_and_inert_policy(monkeypatch):
    monkeypatch.delenv("NATIVE_RLS_ENABLED", raising=False)
    table = {"is_owner": True, "relrowsecurity": False, "relforcerowsecurity": False}

    failures = cutover_failures(
        {"rolsuper": True, "rolbypassrls": True}, table, has_policy=False)

    assert "runtime role is SUPERUSER" in failures
    assert "runtime role has BYPASSRLS" in failures
    assert "runtime role owns protected table chunks" in failures
    assert "chunks does not have ROW LEVEL SECURITY enabled" in failures
    assert "chunks does not have FORCE ROW LEVEL SECURITY enabled" in failures
    assert "chunks_rls_backstop SELECT policy is missing" in failures
    assert "NATIVE_RLS_ENABLED is not enabled for the runtime" in failures
