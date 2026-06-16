"""WP-E: agent_runs (durable HITL run) + draft scope/idempotency columns.

Revision ID: 0003_agentrun_draft
Revises: 0002_memory_trust
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "0003_agentrun_draft"
down_revision = "0002_memory_trust"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    
    if not insp.has_table("agent_runs"):
        op.create_table(
            "agent_runs",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("session_id", UUID(as_uuid=True), nullable=False),
            sa.Column("employee_id", UUID(as_uuid=True), nullable=False),
            sa.Column("status", sa.String(40), nullable=False, server_default="running"),
            sa.Column("checkpoint_state", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
            sa.Column("idempotency_key", sa.String(64), nullable=True, unique=True),
            sa.Column("lease_owner", sa.String(100), nullable=True),
            sa.Column("lease_expires_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
        op.create_index("ix_agent_runs_session_id", "agent_runs", ["session_id"])
        op.create_index("ix_agent_runs_employee_id", "agent_runs", ["employee_id"])

    if insp.has_table("drafts"):
        draft_cols = [c["name"] for c in insp.get_columns("drafts")]
        if "department_id" not in draft_cols:
            op.add_column("drafts", sa.Column("department_id", UUID(as_uuid=True), nullable=True))
        if "agent_run_id" not in draft_cols:
            op.add_column("drafts", sa.Column("agent_run_id", UUID(as_uuid=True), nullable=True))
            op.create_unique_constraint("uq_draft_run_hash", "drafts", ["agent_run_id", "payload_hash"])


def downgrade() -> None:
    op.drop_constraint("uq_draft_run_hash", "drafts", type_="unique")
    op.drop_column("drafts", "agent_run_id")
    op.drop_column("drafts", "department_id")
    op.drop_index("ix_agent_runs_employee_id", table_name="agent_runs")
    op.drop_index("ix_agent_runs_session_id", table_name="agent_runs")
    op.drop_table("agent_runs")
