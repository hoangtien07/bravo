"""Memory provenance / trust hardening (WP-G).

Add `trust_level` ("trusted" | "untrusted", default "trusted") + `source` (nullable)
to conversation_messages and archival_passages. Content derived from documents/ERP
is marked "untrusted" so the prompt builder can frame it as DATA, not instructions
(prompt/context-poisoning defense — Invariant #1/#3).

Revision ID: 0002_memory_trust
Create Date: 2026-06-10
"""
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0002_memory_trust"
down_revision = "0001_init"
branch_labels = None
depends_on = None

_TABLES = ("conversation_messages", "archival_passages")


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    for table in _TABLES:
        columns = [c["name"] for c in insp.get_columns(table)]
        if "trust_level" not in columns:
            op.add_column(
                table,
                sa.Column(
                    "trust_level",
                    sa.String(length=20),
                    nullable=False,
                    server_default="trusted",
                ),
            )
            op.add_column(
                table,
                sa.Column("source", sa.String(length=500), nullable=True),
            )
            # Deterministic constraint: only the two known trust levels are storable.
            op.create_check_constraint(
                f"ck_{table}_trust_level",
                table,
                "trust_level IN ('trusted', 'untrusted')",
            )


def downgrade() -> None:
    for table in _TABLES:
        op.drop_constraint(f"ck_{table}_trust_level", table, type_="check")
        op.drop_column(table, "source")
        op.drop_column(table, "trust_level")
