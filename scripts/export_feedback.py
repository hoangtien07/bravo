"""Q10 corpus-ops: export disliked assistant answers as golden-set candidates.

The chat UI records like/dislike on assistant messages (ConversationMessage.feedback), but
nothing consumed it (council 2026-07-12 #4). This script pulls disliked turns + the user
question that preceded them into a YAML the team triages: a bad answer is either a corpus
gap (acquire data), a retrieval miss (tune), or a synthesis issue (prompt). Feeds the golden
set + the weekly ritual in docs/CORPUS-OPS.md.

Usage: python -m scripts.export_feedback > feedback_candidates.yaml
"""
from __future__ import annotations

import asyncio
import sys

from sqlalchemy import select

from app.database import async_session_factory
from app.database.models import ConversationMessage


async def collect() -> list[dict]:
    async with async_session_factory() as db:
        disliked = list((await db.execute(
            select(ConversationMessage)
            .where(ConversationMessage.feedback == "dislike",
                   ConversationMessage.role == "assistant")
            .order_by(ConversationMessage.created_at.desc())
        )).scalars().all())
        out: list[dict] = []
        for m in disliked:
            # The user question is the most recent user turn before this answer in the session.
            q = (await db.execute(
                select(ConversationMessage.content)
                .where(ConversationMessage.session_id == m.session_id,
                       ConversationMessage.role == "user",
                       ConversationMessage.created_at < m.created_at)
                .order_by(ConversationMessage.created_at.desc()).limit(1)
            )).scalar_one_or_none()
            out.append({"question": q or "", "bad_answer": (m.content or "")[:500],
                        "session_id": str(m.session_id),
                        # P1: user's free-text report + category (may contain personal data).
                        "report_comment": m.feedback_comment or "",
                        "report_category": m.feedback_category or "",
                        "label": ""})   # corpus-miss | retrieval-miss | synthesis-poor | wrong-task-type
        return out


def _yaml_dump(records: list[dict]) -> str:
    # F-9: real YAML serializer (no hand-rolled escaping that a backslash could break out of).
    header = ("# ⚠ CÓ THỂ CHỨA DỮ LIỆU CÁ NHÂN — xử lý theo PDPL; chỉ dùng nội bộ IT, đặt retention.\n"
              "# Disliked answers -> golden-set / corpus-gap triage (Q10).\n")
    try:
        import yaml
        body = yaml.safe_dump({"candidates": records}, allow_unicode=True, sort_keys=False)
    except Exception:
        # Fallback (no PyYAML): JSON is valid YAML and round-trips safely.
        import json
        body = json.dumps({"candidates": records}, ensure_ascii=False, indent=2)
    return header + body


def main() -> int:
    records = asyncio.run(collect())
    sys.stdout.write(_yaml_dump(records))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
