"""Version-aware schema snapshots and KEDB evidence stores.

Revision ID: 0015_schema_kedb_evidence
Revises: 0014_candidate_review_note
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID

revision = "0015_schema_kedb_evidence"
down_revision = "0014_candidate_review_note"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if not inspector.has_table("schema_snapshots"):
        op.create_table(
            "schema_snapshots",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("bravo_version", sa.String(80), nullable=False),
            sa.Column("environment", sa.String(120), nullable=False),
            sa.Column("status", sa.String(30), nullable=False, server_default="candidate"),
            sa.Column("source_ref", sa.String(500), nullable=True),
            sa.Column("fingerprint", sa.String(64), nullable=False, unique=True),
            sa.Column("payload", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
            sa.Column("created_by", UUID(as_uuid=True), nullable=False),
            sa.Column("approved_by", UUID(as_uuid=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
        for column in ("bravo_version", "environment", "status", "created_by"):
            op.create_index(f"ix_schema_snapshots_{column}", "schema_snapshots", [column])
    if not inspector.has_table("known_errors"):
        op.create_table(
            "known_errors",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("case_key", sa.String(120), nullable=False),
            sa.Column("title", sa.String(500), nullable=False),
            sa.Column("symptom", sa.Text(), nullable=False),
            sa.Column("probable_cause", sa.Text(), nullable=True),
            sa.Column("resolution", sa.Text(), nullable=True),
            sa.Column("bravo_version", sa.String(80), nullable=True),
            sa.Column("environment", sa.String(120), nullable=True),
            sa.Column("status", sa.String(30), nullable=False, server_default="candidate"),
            sa.Column("supersedes_case_key", sa.String(120), nullable=True),
            sa.Column("source_refs", ARRAY(sa.String()), nullable=False, server_default=sa.text("'{}'")),
            sa.Column("created_by", UUID(as_uuid=True), nullable=False),
            sa.Column("verified_by", UUID(as_uuid=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.UniqueConstraint("case_key", name="uq_known_error_case_key"),
        )
        for column in ("case_key", "bravo_version", "environment", "status", "created_by"):
            op.create_index(f"ix_known_errors_{column}", "known_errors", [column])


def downgrade() -> None:
    for column in ("created_by", "status", "environment", "bravo_version", "case_key"):
        op.drop_index(f"ix_known_errors_{column}", table_name="known_errors")
    op.drop_table("known_errors")
    for column in ("created_by", "status", "environment", "bravo_version"):
        op.drop_index(f"ix_schema_snapshots_{column}", table_name="schema_snapshots")
    op.drop_table("schema_snapshots")
