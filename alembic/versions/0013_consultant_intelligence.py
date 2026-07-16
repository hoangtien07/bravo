"""Consultant state gaps and governed candidate queue.

Revision ID: 0013_consultant_intelligence
Revises: 0012_frontier_run_control_plane
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "0013_consultant_intelligence"
down_revision = "0012_frontier_run_control_plane"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if not sa.inspect(op.get_bind()).has_table("consultant_gap_events"):
        op.create_table(
            "consultant_gap_events",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("session_id", UUID(as_uuid=True), nullable=False),
            sa.Column("employee_id", UUID(as_uuid=True), nullable=False),
            sa.Column("goal_type", sa.String(100), nullable=False),
            sa.Column("workflow_id", sa.String(100), nullable=True),
            sa.Column("node_id", sa.String(100), nullable=True),
            sa.Column("reason", sa.String(60), nullable=False),
            sa.Column("risk", sa.String(8), nullable=False, server_default="U1"),
            sa.Column("signature", sa.String(64), nullable=False),
            sa.Column("status", sa.String(40), nullable=False, server_default="open"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.UniqueConstraint("session_id", "signature", "status",
                                name="uq_consultant_gap_session_signature_status"),
        )
        for column in ("session_id", "employee_id", "goal_type", "workflow_id", "reason", "signature", "status"):
            op.create_index(f"ix_consultant_gap_events_{column}", "consultant_gap_events", [column])
    if not sa.inspect(op.get_bind()).has_table("knowledge_candidates"):
        op.create_table(
            "knowledge_candidates",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("artifact_type", sa.String(60), nullable=False),
            sa.Column("status", sa.String(40), nullable=False, server_default="review_required"),
            sa.Column("content", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
            sa.Column("gap_count", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("reviewer_id", UUID(as_uuid=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
        op.create_index("ix_knowledge_candidates_status", "knowledge_candidates", ["status"])


def downgrade() -> None:
    op.drop_index("ix_knowledge_candidates_status", table_name="knowledge_candidates")
    op.drop_table("knowledge_candidates")
    for column in ("status", "signature", "reason", "workflow_id", "goal_type", "employee_id", "session_id"):
        op.drop_index(f"ix_consultant_gap_events_{column}", table_name="consultant_gap_events")
    op.drop_table("consultant_gap_events")
