"""P-chat: bảng conversations (hội thoại có chủ + tiêu đề + chia sẻ) + cột feedback.

Revision ID: 0005_conversations
Revises: 0004_db_roles
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = "0005_conversations"
down_revision = "0004_db_roles"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "conversations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),   # == session_id
        sa.Column("employee_id", UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(200), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("last_message_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("shared_token", sa.String(64), nullable=True),
    )
    op.create_index("ix_conversations_employee_id", "conversations", ["employee_id"])
    op.create_index("ix_conversations_last_message_at", "conversations", ["last_message_at"])
    op.create_index("uq_conversations_shared_token", "conversations", ["shared_token"], unique=True)

    op.add_column("conversation_messages",
                  sa.Column("feedback", sa.String(10), nullable=True))
    op.create_index("ix_conv_messages_session_created", "conversation_messages",
                    ["session_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_conv_messages_session_created", table_name="conversation_messages")
    op.drop_column("conversation_messages", "feedback")
    op.drop_index("uq_conversations_shared_token", table_name="conversations")
    op.drop_index("ix_conversations_last_message_at", table_name="conversations")
    op.drop_index("ix_conversations_employee_id", table_name="conversations")
    op.drop_table("conversations")
