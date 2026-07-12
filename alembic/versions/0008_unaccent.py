"""unaccent extension — lexical search bắt được tiếng Việt KHÔNG dấu.

Người dùng VN gõ không dấu rất phổ biến ("cach len bao cao can doi phat sinh");
tsquery so khớp chuỗi thô nên trước đây trượt hết nội dung có dấu -> retrieval
trả nhiễu -> agent abstain/clarify sai. unaccent hoá CẢ HAI phía trong
lexical_search (app/rag/retriever.py) để accent-insensitive; dense + rerank vẫn
phân biệt dấu nên nhiễu đồng-tự-khác-dấu (bán/bàn) được kiểm soát qua RRF.

Revision ID: 0008_unaccent
Revises: 0007_agentrun_tokens
"""
from __future__ import annotations

from alembic import op

revision = "0008_unaccent"
down_revision = "0007_agentrun_tokens"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS unaccent")


def downgrade() -> None:
    op.execute("DROP EXTENSION IF EXISTS unaccent")
