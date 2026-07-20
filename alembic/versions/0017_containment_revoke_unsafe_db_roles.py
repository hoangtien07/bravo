"""Containment: revoke unsafe placeholder runtime-role grants.

The original ``app_safe`` views are unscoped ``SELECT *`` views and the application does not
set a request identity in PostgreSQL. Granting them to ``bravo_agent`` is therefore not a native
RLS backstop. Fail closed until a later reviewed migration introduces real policies, separate
login roles and two-user/two-department negative probes.

Revision ID: 0017_revoke_unsafe_roles
Revises: 0016_task_state_retention
"""
from __future__ import annotations

from alembic import op

revision = "0017_revoke_unsafe_roles"
down_revision = "0016_task_state_retention"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("REVOKE ALL ON app_safe.v_chunks_scoped FROM bravo_agent")
    op.execute("REVOKE ALL ON app_safe.v_archival_scoped FROM bravo_agent")
    op.execute("REVOKE USAGE ON SCHEMA app_safe FROM bravo_agent")
    op.execute("REVOKE INSERT ON drafts, audit_log FROM bravo_writer")
    op.execute(
        "COMMENT ON ROLE bravo_agent IS "
        "'CONTAINED: no runtime grants until native scoped policies are verified'"
    )
    op.execute(
        "COMMENT ON ROLE bravo_writer IS "
        "'CONTAINED: no runtime grants until draft/audit writer isolation is verified'"
    )


def downgrade() -> None:
    op.execute("GRANT USAGE ON SCHEMA app_safe TO bravo_agent")
    op.execute(
        "GRANT SELECT ON app_safe.v_chunks_scoped, app_safe.v_archival_scoped TO bravo_agent"
    )
    op.execute("GRANT INSERT ON drafts, audit_log TO bravo_writer")
    op.execute("COMMENT ON ROLE bravo_agent IS NULL")
    op.execute("COMMENT ON ROLE bravo_writer IS NULL")
