"""P0.6: native Postgres RLS backstop policies (defense-in-depth for invariant #1).

Layer #1 is the app-composed WHERE clause (rls.py). This adds an INDEPENDENT layer #2: native
row-level-security policies on the chunk/source read surface, filtering by per-request GUCs
(bravo.employee_id / bravo.dept_ids / bravo.doc_read_level) that mirror chunk_scope_filter.

READY-TO-ARM, NOT ARMED: this migration creates the policies but deliberately does NOT
`ENABLE ROW LEVEL SECURITY`, so it is inert and cannot break the running app (which currently
connects as the table owner). Arming is an operator cutover — connect the runtime as a dedicated
non-owner LOGIN role, set native_rls_enabled=true, then ENABLE/FORCE RLS — see
docs/SECURITY-DB-BACKSTOP.md. The policy is written so the owner is also filtered once FORCE is on.

Revision ID: 0017_native_rls_backstop
Revises: 0016_task_state_retention
"""
from __future__ import annotations

from alembic import op

revision = "0017_native_rls_backstop"
down_revision = "0016_task_state_retention"
branch_labels = None
depends_on = None

# Mirrors chunk_scope_filter / source_scope_filter (rls.py): admin/all -> everything; own_dept ->
# own personal OR global OR department-overlap; no permission -> own personal only. dept_ids GUC is
# a comma-separated list; an empty GUC yields an empty array (no department match).
_POLICY = """
CREATE POLICY {name} ON {table} FOR SELECT USING (
    current_setting('bravo.doc_read_level', true) = 'all'
    OR (
        visibility = 'personal'
        AND owner_id = nullif(current_setting('bravo.employee_id', true), '')::uuid
    )
    OR (
        current_setting('bravo.doc_read_level', true) = 'own_dept'
        AND (
            visibility = 'global'
            OR (
                visibility = 'department'
                AND department_ids && (
                    SELECT COALESCE(array_agg(x::uuid), ARRAY[]::uuid[])
                    FROM unnest(string_to_array(
                        nullif(current_setting('bravo.dept_ids', true), ''), ',')) AS x
                )
            )
        )
    )
);
"""

# Scoped to `chunks` — the RLS-on-vector read surface (chunk_scope_filter) and the crown-jewel
# cross-department leak path. `chunks` carries the inline `department_ids` array this policy needs.
# `sources` (join table source_departments) and conversation/memory tables use different shapes;
# extend the backstop to them as follow-up (docs/SECURITY-DB-BACKSTOP.md) — layer #1 still covers
# them today.
_TABLES = {"chunks": "chunks_rls_backstop"}


def upgrade() -> None:
    for table, name in _TABLES.items():
        op.execute(f"DROP POLICY IF EXISTS {name} ON {table};")
        op.execute(_POLICY.format(name=name, table=table))


def downgrade() -> None:
    for table, name in _TABLES.items():
        op.execute(f"DROP POLICY IF EXISTS {name} ON {table};")
