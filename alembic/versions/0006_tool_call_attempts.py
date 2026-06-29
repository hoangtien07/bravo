"""Tool-call audit journal (Tầng 3b): bảng tool_call_attempts.

Revision ID: 0006_tool_audit
Revises: 0005_conversations
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = "0006_tool_audit"
down_revision = "0005_conversations"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    if not insp.has_table("tool_call_attempts"):
        op.create_table(
            "tool_call_attempts",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("agent_run_id", UUID(as_uuid=True), nullable=True),
            sa.Column("actor_id", UUID(as_uuid=True), nullable=True),
            sa.Column("tool", sa.String(100), nullable=False),
            sa.Column("args_hash", sa.String(64), nullable=False),
            sa.Column("status", sa.String(20), nullable=False),  # drafted|executed|failed
            sa.Column("summary", sa.String(500), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
        op.create_index("ix_tool_call_attempts_agent_run_id", "tool_call_attempts", ["agent_run_id"])


def downgrade() -> None:
    op.drop_table("tool_call_attempts")
