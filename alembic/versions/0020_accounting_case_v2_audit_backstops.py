"""Scope command/audit V2 records and make their history append-only.

Revision ID: 0020_case_v2_audit
Revises: 0019_case_v2_defaults
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0020_case_v2_audit"
down_revision = "0019_case_v2_defaults"
branch_labels = None
depends_on = None


_SCOPE = """
current_setting('bravo.accounting_case_level', true) = 'all'
OR (
    current_setting('bravo.accounting_case_level', true) = 'own_dept'
    AND department_ids && (
        SELECT COALESCE(array_agg(x::uuid), ARRAY[]::uuid[])
        FROM unnest(string_to_array(nullif(current_setting('bravo.dept_ids', true), ''), ',')) AS x
    )
)
"""


def _policy(table: str) -> None:
    op.execute(f"DROP POLICY IF EXISTS {table}_rls_backstop ON {table}")
    op.execute(f"CREATE POLICY {table}_rls_backstop ON {table} FOR ALL USING ({_SCOPE}) WITH CHECK ({_SCOPE})")


def _has_column(table: str, column: str) -> bool:
    """Account for the legacy 0001 metadata bootstrap on a fresh database.

    Migration 0001 creates the *current* ORM metadata, which can already contain columns
    introduced by a later revision.  Later migrations therefore must not assume their schema
    change is absent on a new local database.
    """
    return column in {item["name"] for item in sa.inspect(op.get_bind()).get_columns(table)}


def upgrade() -> None:
    op.alter_column("accounting_cases_v2", "review_dispositions", server_default=sa.text("'[]'::jsonb"))
    if not _has_column("accounting_case_commands_v2", "department_ids"):
        op.add_column("accounting_case_commands_v2", sa.Column(
            "department_ids", postgresql.ARRAY(postgresql.UUID(as_uuid=True)), nullable=False,
            server_default=sa.text("'{}'::uuid[]"),
        ))
    op.execute("""
        UPDATE accounting_case_commands_v2 command
        SET department_ids = cases.department_ids
        FROM accounting_cases_v2 cases
        WHERE command.outcome_case_id = cases.case_id
    """)
    inspector = sa.inspect(op.get_bind())
    if not inspector.has_table("accounting_case_audit_v2"):
        op.create_table(
            "accounting_case_audit_v2",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("case_id", sa.String(length=160), nullable=False),
            sa.Column("department_ids", postgresql.ARRAY(postgresql.UUID(as_uuid=True)), nullable=False,
                      server_default=sa.text("'{}'::uuid[]")),
            sa.Column("actor_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("action", sa.String(length=80), nullable=False),
            sa.Column("detail", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        )
        op.create_index("ix_accounting_case_audit_v2_case_id", "accounting_case_audit_v2", ["case_id"])
    _policy("accounting_case_commands_v2")
    _policy("accounting_case_audit_v2")
    op.execute("""
        CREATE OR REPLACE FUNCTION bravo_reject_v2_audit_mutation() RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'AccountingCase V2 audit history is append-only';
        END;
        $$ LANGUAGE plpgsql
    """)
    op.execute("DROP TRIGGER IF EXISTS accounting_case_commands_v2_immutable ON accounting_case_commands_v2")
    op.execute("DROP TRIGGER IF EXISTS accounting_case_audit_v2_immutable ON accounting_case_audit_v2")
    op.execute("""
        CREATE TRIGGER accounting_case_commands_v2_immutable
          BEFORE UPDATE OR DELETE ON accounting_case_commands_v2
          FOR EACH ROW EXECUTE FUNCTION bravo_reject_v2_audit_mutation()
    """)
    op.execute("""
        CREATE TRIGGER accounting_case_audit_v2_immutable
          BEFORE UPDATE OR DELETE ON accounting_case_audit_v2
          FOR EACH ROW EXECUTE FUNCTION bravo_reject_v2_audit_mutation()
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS accounting_case_audit_v2_immutable ON accounting_case_audit_v2")
    op.execute("DROP TRIGGER IF EXISTS accounting_case_commands_v2_immutable ON accounting_case_commands_v2")
    op.execute("DROP FUNCTION IF EXISTS bravo_reject_v2_audit_mutation()")
    op.execute("DROP POLICY IF EXISTS accounting_case_audit_v2_rls_backstop ON accounting_case_audit_v2")
    op.execute("DROP POLICY IF EXISTS accounting_case_commands_v2_rls_backstop ON accounting_case_commands_v2")
    op.drop_index("ix_accounting_case_audit_v2_case_id", table_name="accounting_case_audit_v2")
    op.drop_table("accounting_case_audit_v2")
    op.drop_column("accounting_case_commands_v2", "department_ids")
    op.alter_column("accounting_cases_v2", "review_dispositions", server_default=sa.text("'{}'::jsonb"))
