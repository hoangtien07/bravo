"""P0.6 — native Postgres RLS backstop (defense-in-depth for invariant #1).

The application-composed WHERE clauses in ``rls.py`` are layer #1. This module is the plumbing
for an INDEPENDENT layer #2: native Postgres row-level-security policies (migration 0017) that
filter rows using per-request session GUCs, so a forgotten ``.where()`` in future code cannot
leak cross-department data.

It is OFF by default (``settings.native_rls_enabled``). Arming it requires an operator cutover
(a dedicated non-owner LOGIN role + ``ENABLE/FORCE ROW LEVEL SECURITY``) documented in
``docs/SECURITY-DB-BACKSTOP.md`` — the table owner bypasses RLS, so setting GUCs alone is inert
until the runtime connects as a non-owner role or the tables are FORCE-enabled.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import text

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.security.rls import Identity

# GUC names the 0017 policies read. Kept here as the single source of truth.
GUC_EMPLOYEE = "bravo.employee_id"
GUC_DEPTS = "bravo.dept_ids"
GUC_DOC_LEVEL = "bravo.doc_read_level"


async def apply_rls_gucs(session: "AsyncSession", identity: "Identity") -> None:
    """Set the per-identity, transaction-local GUCs the native RLS policies filter on.

    Uses ``set_config(name, value, is_local => true)`` so the settings are scoped to the current
    transaction and never leak across pooled connections. A no-op when the backstop is disabled
    (the caller gates on ``settings.native_rls_enabled``)."""
    dept_csv = ",".join(str(d) for d in identity.department_ids)
    level = identity.scope_level("doc", "read") or "none"
    await session.execute(
        text("SELECT set_config(:k, :v, true)"),
        {"k": GUC_EMPLOYEE, "v": str(identity.employee_id)})
    await session.execute(
        text("SELECT set_config(:k, :v, true)"), {"k": GUC_DEPTS, "v": dept_csv})
    await session.execute(
        text("SELECT set_config(:k, :v, true)"), {"k": GUC_DOC_LEVEL, "v": level})
