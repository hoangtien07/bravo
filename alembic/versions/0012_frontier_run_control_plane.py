"""Frontier durable run control plane: events, approvals, plans and cancellation.

Revision ID: 0012_frontier_run_control_plane
Revises: 0011_sse_v2
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "0012_frontier_run_control_plane"
down_revision = "0011_sse_v2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    cols = {c["name"] for c in insp.get_columns("agent_runs")}
    if "mode" not in cols:
        op.add_column("agent_runs", sa.Column("mode", sa.String(30), nullable=False,
                                               server_default="auto"))
    if "plan" not in cols:
        op.add_column("agent_runs", sa.Column("plan", JSONB, nullable=False,
                                               server_default=sa.text("'{}'::jsonb")))
    if "cancel_requested" not in cols:
        op.add_column("agent_runs", sa.Column("cancel_requested", sa.Boolean(), nullable=False,
                                               server_default=sa.false()))
    if "completed_at" not in cols:
        op.add_column("agent_runs", sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True))

    if not insp.has_table("agent_run_events"):
        op.create_table(
            "agent_run_events",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("agent_run_id", UUID(as_uuid=True),
                      sa.ForeignKey("agent_runs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("seq", sa.Integer(), nullable=False),
            sa.Column("event_type", sa.String(80), nullable=False),
            sa.Column("payload", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.UniqueConstraint("agent_run_id", "seq", name="uq_agent_run_event_seq"),
        )
        op.create_index("ix_agent_run_events_agent_run_id", "agent_run_events", ["agent_run_id"])

    if not insp.has_table("agent_approvals"):
        op.create_table(
            "agent_approvals",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("agent_run_id", UUID(as_uuid=True),
                      sa.ForeignKey("agent_runs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("requested_by", UUID(as_uuid=True), nullable=False),
            sa.Column("tool_name", sa.String(120), nullable=False),
            sa.Column("args_hash", sa.String(64), nullable=False),
            sa.Column("preview", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
            sa.Column("status", sa.String(30), nullable=False, server_default="pending"),
            sa.Column("resolved_by", UUID(as_uuid=True), nullable=True),
            sa.Column("resolution_note", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        )
        op.create_index("ix_agent_approvals_agent_run_id", "agent_approvals", ["agent_run_id"])
        op.create_index("ix_agent_approvals_requested_by", "agent_approvals", ["requested_by"])

    if not insp.has_table("artifacts"):
        op.create_table(
            "artifacts",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("agent_run_id", UUID(as_uuid=True),
                      sa.ForeignKey("agent_runs.id", ondelete="SET NULL"), nullable=True),
            sa.Column("owner_id", UUID(as_uuid=True), sa.ForeignKey("employees.id"), nullable=False),
            sa.Column("kind", sa.String(60), nullable=False),
            sa.Column("title", sa.String(300), nullable=False),
            sa.Column("mime_type", sa.String(120), nullable=False, server_default="text/markdown"),
            sa.Column("content", sa.Text(), nullable=True),
            sa.Column("storage_path", sa.String(1000), nullable=True),
            sa.Column("provenance", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
            sa.Column("status", sa.String(30), nullable=False, server_default="ready"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
        op.create_index("ix_artifacts_agent_run_id", "artifacts", ["agent_run_id"])
        op.create_index("ix_artifacts_owner_id", "artifacts", ["owner_id"])


def downgrade() -> None:
    op.drop_index("ix_artifacts_owner_id", table_name="artifacts")
    op.drop_index("ix_artifacts_agent_run_id", table_name="artifacts")
    op.drop_table("artifacts")
    op.drop_index("ix_agent_approvals_requested_by", table_name="agent_approvals")
    op.drop_index("ix_agent_approvals_agent_run_id", table_name="agent_approvals")
    op.drop_table("agent_approvals")
    op.drop_index("ix_agent_run_events_agent_run_id", table_name="agent_run_events")
    op.drop_table("agent_run_events")
    op.drop_column("agent_runs", "completed_at")
    op.drop_column("agent_runs", "cancel_requested")
    op.drop_column("agent_runs", "plan")
    op.drop_column("agent_runs", "mode")
