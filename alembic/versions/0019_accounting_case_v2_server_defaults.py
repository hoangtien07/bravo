"""Align durable AccountingCase V2 server defaults with the ORM model.

Revision ID: 0019_case_v2_defaults
Revises: 0018_accounting_case_v2_shell
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0019_case_v2_defaults"
down_revision = "0018_accounting_case_v2_shell"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for column, default in (
        ("department_ids", "'{}'::uuid[]"),
        ("scope", "'{}'::jsonb"),
        ("revision", "0"),
        ("evidence", "'[]'::jsonb"),
        ("results", "'[]'::jsonb"),
        ("findings", "'[]'::jsonb"),
        ("review_dispositions", "'{}'::jsonb"),
    ):
        op.alter_column("accounting_cases_v2", column, server_default=sa.text(default))
    op.alter_column("accounting_case_commands_v2", "outcome", server_default=sa.text("'{}'::jsonb"))


def downgrade() -> None:
    for column in (
        "department_ids",
        "scope",
        "revision",
        "evidence",
        "results",
        "findings",
        "review_dispositions",
    ):
        op.alter_column("accounting_cases_v2", column, server_default=None)
    op.alter_column("accounting_case_commands_v2", "outcome", server_default=None)
