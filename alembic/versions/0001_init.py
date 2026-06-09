"""Initial schema: pgvector extension, core tables, retrieval indexes.

Revision ID: 0001_init
Create Date: 2026-06-09
"""
from __future__ import annotations

from alembic import op

import app.database.models  # noqa: F401 — register tables
from app.database import Base

revision = "0001_init"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # pgvector must exist before the Vector columns are created.
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    bind = op.get_bind()
    Base.metadata.create_all(bind)

    # Hybrid retrieval indexes (findings/J):
    #  - FTS GIN for lexical/BM25 branch ('simple' = whitespace, catches codes/numbers)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_chunks_fts ON chunks "
        "USING gin (to_tsvector('simple', content))"
    )
    #  - HNSW for approximate vector search (cosine)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_chunks_embedding ON chunks "
        "USING hnsw (embedding vector_cosine_ops)"
    )
    #  - GIN on department_ids for the RLS-on-vector overlap (&&) predicate
    op.execute("CREATE INDEX IF NOT EXISTS ix_chunks_dept ON chunks USING gin (department_ids)")
    # Archival memory indexes (agent memory — same RLS-on-vector pattern)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_archival_embedding ON archival_passages "
        "USING hnsw (embedding vector_cosine_ops)"
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_archival_dept ON archival_passages USING gin (department_ids)")


def downgrade() -> None:
    Base.metadata.drop_all(op.get_bind())
