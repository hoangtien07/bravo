"""Lifecycle metadata for opt-in Consultant task-state retention.

Revision ID: 0016_task_state_retention
Revises: 0015_schema_kedb_evidence
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "0016_task_state_retention"
down_revision = "0015_schema_kedb_evidence"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns("memory_blocks")}
    if "updated_at" not in columns:
        op.add_column(
            "memory_blocks",
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
        op.create_index("ix_memory_blocks_updated_at", "memory_blocks", ["updated_at"])


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns("memory_blocks")}
    if "updated_at" in columns:
        op.drop_index("ix_memory_blocks_updated_at", table_name="memory_blocks")
        op.drop_column("memory_blocks", "updated_at")
