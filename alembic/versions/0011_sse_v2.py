"""P1 SSE v2: attachment.message_id (turn binding) + conversation_messages.seq
(absolute ordering for truncate/edit) + feedback_comment/feedback_category (report-to-IT).

Idempotent: 0001 create_all builds the current models on a fresh DB, so every add is guarded
by a column-existence check.

Revision ID: 0011_sse_v2
Revises: 0010_attachments
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = "0011_sse_v2"
down_revision = "0010_attachments"
branch_labels = None
depends_on = None

_SEQ = "conv_msg_seq"


def _has_col(insp, table: str, col: str) -> bool:
    return any(c["name"] == col for c in insp.get_columns(table))


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)

    # 1) attachments.message_id — bind an attachment to the user turn it was sent with.
    if insp.has_table("attachments") and not _has_col(insp, "attachments", "message_id"):
        op.add_column("attachments", sa.Column("message_id", UUID(as_uuid=True), nullable=True))
        op.create_foreign_key(
            "fk_attachments_message", "attachments", "conversation_messages",
            ["message_id"], ["id"], ondelete="SET NULL")
        op.create_index("ix_attachments_message_id", "attachments", ["message_id"])

    if not insp.has_table("conversation_messages"):
        return

    # 2) feedback comment + category (report-to-IT).
    if not _has_col(insp, "conversation_messages", "feedback_comment"):
        op.add_column("conversation_messages", sa.Column("feedback_comment", sa.Text, nullable=True))
    if not _has_col(insp, "conversation_messages", "feedback_category"):
        op.add_column("conversation_messages",
                      sa.Column("feedback_category", sa.String(32), nullable=True))

    # 3) seq — monotonic per-table ordering, backfilled in created_at order (P3 truncate needs a
    #    tie-free order; created_at alone can collide within a transaction-second).
    if not _has_col(insp, "conversation_messages", "seq"):
        op.execute(f"CREATE SEQUENCE IF NOT EXISTS {_SEQ}")
        op.add_column("conversation_messages", sa.Column("seq", sa.BigInteger, nullable=True))
        op.execute("""
            WITH ordered AS (
                SELECT id, ROW_NUMBER() OVER (ORDER BY created_at, id) AS rn
                FROM conversation_messages
            )
            UPDATE conversation_messages m SET seq = o.rn FROM ordered o WHERE m.id = o.id
        """)
        op.execute(
            f"SELECT setval('{_SEQ}', COALESCE((SELECT MAX(seq) FROM conversation_messages), 0) + 1, false)")
        op.execute(f"ALTER TABLE conversation_messages ALTER COLUMN seq SET DEFAULT nextval('{_SEQ}')")
        op.alter_column("conversation_messages", "seq", nullable=False)
        op.create_index("ix_conv_msg_session_seq", "conversation_messages", ["session_id", "seq"])


def downgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    if insp.has_table("conversation_messages"):
        if _has_col(insp, "conversation_messages", "seq"):
            try:
                op.drop_index("ix_conv_msg_session_seq", table_name="conversation_messages")
            except Exception:
                pass
            op.drop_column("conversation_messages", "seq")
            op.execute(f"DROP SEQUENCE IF EXISTS {_SEQ}")
        for col in ("feedback_category", "feedback_comment"):
            if _has_col(insp, "conversation_messages", col):
                op.drop_column("conversation_messages", col)
    if insp.has_table("attachments") and _has_col(insp, "attachments", "message_id"):
        try:
            op.drop_index("ix_attachments_message_id", table_name="attachments")
        except Exception:
            pass
        try:
            op.drop_constraint("fk_attachments_message", "attachments", type_="foreignkey")
        except Exception:
            pass
        op.drop_column("attachments", "message_id")
