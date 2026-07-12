"""v2 Track 2: three-tier visibility + owner on sources/chunks (personal workspace).

Adds an EXPLICIT visibility column so a personal upload (empty departments) is no longer
inferred as global. Backfills legacy rows from the old convention:
  - has source_departments  -> 'department'
  - none                     -> 'global'
Legacy owner_id stays NULL (corpus/file_system sources are department/global, not personal).

Idempotent: 0001_init runs Base.metadata.create_all against the LIVE models, so a fresh DB
already has these columns — every add is guarded (matches 0005 convention).

Revision ID: 0009_visibility
Revises: 0008_unaccent
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = "0009_visibility"
down_revision = "0008_unaccent"
branch_labels = None
depends_on = None


def _cols(insp, table: str) -> set[str]:
    return {c["name"] for c in insp.get_columns(table)}


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)

    scols = _cols(insp, "sources")
    if "visibility" not in scols:
        op.add_column("sources", sa.Column(
            "visibility", sa.String(20), nullable=False, server_default="personal"))
    if "owner_id" not in scols:
        op.add_column("sources", sa.Column("owner_id", UUID(as_uuid=True), nullable=True))
    if "content_hash" not in scols:
        op.add_column("sources", sa.Column("content_hash", sa.String(64), nullable=True))

    ccols = _cols(insp, "chunks")
    if "visibility" not in ccols:
        op.add_column("chunks", sa.Column(
            "visibility", sa.String(20), nullable=False, server_default="personal"))
    if "owner_id" not in ccols:
        op.add_column("chunks", sa.Column("owner_id", UUID(as_uuid=True), nullable=True))

    # Backfill legacy rows from the old empty-departments=global convention.
    op.execute("""
        UPDATE sources SET visibility = CASE
            WHEN EXISTS (SELECT 1 FROM source_departments sd WHERE sd.source_id = sources.id)
            THEN 'department' ELSE 'global' END
        WHERE owner_id IS NULL
    """)
    op.execute("""
        UPDATE chunks SET visibility = CASE
            WHEN cardinality(department_ids) = 0 THEN 'global' ELSE 'department' END
        WHERE owner_id IS NULL
    """)

    # Drop the transient server_default (app supplies visibility explicitly going forward).
    op.alter_column("sources", "visibility", server_default=None)
    op.alter_column("chunks", "visibility", server_default=None)

    # Constraints + indexes (guarded for the fresh-DB path).
    existing_sources_idx = {i["name"] for i in insp.get_indexes("sources")}
    existing_chunks_idx = {i["name"] for i in insp.get_indexes("chunks")}
    check_names = {c["name"] for c in insp.get_check_constraints("sources")}

    if "ck_sources_visibility" not in check_names:
        op.create_check_constraint(
            "ck_sources_visibility", "sources",
            "visibility IN ('personal','department','global')")
    if "ck_chunks_visibility" not in {c["name"] for c in insp.get_check_constraints("chunks")}:
        op.create_check_constraint(
            "ck_chunks_visibility", "chunks",
            "visibility IN ('personal','department','global')")

    # Personal lookups = equality on owner_id; partial index keeps it cheap.
    if "ix_chunks_owner_personal" not in existing_chunks_idx:
        op.create_index("ix_chunks_owner_personal", "chunks", ["owner_id"],
                        postgresql_where=sa.text("visibility = 'personal'"))
    if "ix_chunks_visibility" not in existing_chunks_idx:
        op.create_index("ix_chunks_visibility", "chunks", ["visibility"])
    if "ix_sources_owner_id" not in existing_sources_idx:
        op.create_index("ix_sources_owner_id", "sources", ["owner_id"])
    if "ix_sources_content_hash" not in existing_sources_idx:
        op.create_index("ix_sources_content_hash", "sources", ["content_hash"])
    if "ix_sources_visibility" not in existing_sources_idx:
        op.create_index("ix_sources_visibility", "sources", ["visibility"])


def downgrade() -> None:
    op.drop_index("ix_sources_visibility", table_name="sources")
    op.drop_index("ix_sources_content_hash", table_name="sources")
    op.drop_index("ix_sources_owner_id", table_name="sources")
    op.drop_index("ix_chunks_visibility", table_name="chunks")
    op.drop_index("ix_chunks_owner_personal", table_name="chunks")
    op.drop_constraint("ck_chunks_visibility", "chunks", type_="check")
    op.drop_constraint("ck_sources_visibility", "sources", type_="check")
    op.drop_column("chunks", "owner_id")
    op.drop_column("chunks", "visibility")
    op.drop_column("sources", "content_hash")
    op.drop_column("sources", "owner_id")
    op.drop_column("sources", "visibility")
