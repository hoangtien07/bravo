"""AgentRun.tokens_used — token usage thật per lượt (W1.2, nền cost-tracking W2.4).

Revision ID: 0007_agentrun_tokens
Revises: 0006_tool_audit
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0007_agentrun_tokens"
down_revision = "0006_tool_audit"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    cols = {c["name"] for c in insp.get_columns("agent_runs")}
    if "tokens_used" not in cols:
        op.add_column("agent_runs",
                      sa.Column("tokens_used", sa.Integer(), nullable=False, server_default="0"))


def downgrade() -> None:
    op.drop_column("agent_runs", "tokens_used")
