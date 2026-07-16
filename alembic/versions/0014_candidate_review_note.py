"""Add explicit reviewer note to governed knowledge candidates.

Revision ID: 0014_candidate_review_note
Revises: 0013_consultant_intelligence
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0014_candidate_review_note"
down_revision = "0013_consultant_intelligence"
branch_labels = None
depends_on = None


def upgrade() -> None:
    cols = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("knowledge_candidates")}
    if "review_note" not in cols:
        op.add_column("knowledge_candidates", sa.Column("review_note", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("knowledge_candidates", "review_note")
