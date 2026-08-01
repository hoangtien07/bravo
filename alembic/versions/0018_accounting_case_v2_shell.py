"""WP-04 durable shell persistence for synthetic AccountingCase V2.

Revision ID: 0018_accounting_case_v2_shell
Revises: 0017_native_rls_backstop
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0018_accounting_case_v2_shell"
down_revision = "0017_native_rls_backstop"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "accounting_cases_v2",
        sa.Column("case_id", sa.String(length=160), primary_key=True),
        sa.Column("case_type", sa.String(length=80), nullable=False),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("employees.id"), nullable=False),
        sa.Column("department_ids", postgresql.ARRAY(postgresql.UUID(as_uuid=True)), nullable=False,
                  server_default=sa.text("'{}'::uuid[]")),
        sa.Column("scope", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("state", sa.String(length=32), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("evidence", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("results", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("findings", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("review_dispositions", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("draft_action", postgresql.JSONB(), nullable=True),
        sa.Column("approval", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_accounting_cases_v2_case_type", "accounting_cases_v2", ["case_type"])
    op.create_index("ix_accounting_cases_v2_owner_id", "accounting_cases_v2", ["owner_id"])
    op.create_index("ix_accounting_cases_v2_state", "accounting_cases_v2", ["state"])
    op.create_table(
        "accounting_case_commands_v2",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("subject", sa.String(length=200), nullable=False),
        sa.Column("operation", sa.String(length=80), nullable=False),
        sa.Column("idempotency_key", sa.String(length=128), nullable=False),
        sa.Column("request_hash", sa.String(length=64), nullable=False),
        sa.Column("outcome_case_id", sa.String(length=160), nullable=False),
        sa.Column("outcome", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("subject", "idempotency_key", name="uq_accounting_case_command_subject_key"),
    )
    op.create_index("ix_accounting_case_commands_v2_subject", "accounting_case_commands_v2", ["subject"])
    op.create_index("ix_accounting_case_commands_v2_outcome_case_id", "accounting_case_commands_v2", ["outcome_case_id"])
    # Ready-to-arm native backstop.  As with 0017, RLS is not enabled here: only an operator
    # cutover using a non-owner runtime role may arm it after runtime probes pass.
    op.execute("""
        CREATE POLICY accounting_cases_v2_rls_backstop ON accounting_cases_v2 FOR ALL
        USING (
            current_setting('bravo.accounting_case_level', true) = 'all'
            OR (
                current_setting('bravo.accounting_case_level', true) = 'own_dept'
                AND department_ids && (
                    SELECT COALESCE(array_agg(x::uuid), ARRAY[]::uuid[])
                    FROM unnest(string_to_array(nullif(current_setting('bravo.dept_ids', true), ''), ',')) AS x
                )
            )
        )
        WITH CHECK (
            current_setting('bravo.accounting_case_level', true) = 'all'
            OR (
                current_setting('bravo.accounting_case_level', true) = 'own_dept'
                AND department_ids && (
                    SELECT COALESCE(array_agg(x::uuid), ARRAY[]::uuid[])
                    FROM unnest(string_to_array(nullif(current_setting('bravo.dept_ids', true), ''), ',')) AS x
                )
            )
        );
    """)


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS accounting_cases_v2_rls_backstop ON accounting_cases_v2")
    op.drop_index("ix_accounting_case_commands_v2_outcome_case_id", table_name="accounting_case_commands_v2")
    op.drop_index("ix_accounting_case_commands_v2_subject", table_name="accounting_case_commands_v2")
    op.drop_table("accounting_case_commands_v2")
    op.drop_index("ix_accounting_cases_v2_state", table_name="accounting_cases_v2")
    op.drop_index("ix_accounting_cases_v2_owner_id", table_name="accounting_cases_v2")
    op.drop_index("ix_accounting_cases_v2_case_type", table_name="accounting_cases_v2")
    op.drop_table("accounting_cases_v2")
