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
                        "session_id": str(m.session_id)})
        return out


def _yaml_dump(records: list[dict]) -> str:
    # Minimal YAML writer (no external dep) — keeps the air-gap posture.
    lines = ["# Disliked answers -> golden-set / corpus-gap triage (Q10)", "candidates:"]
    for r in records:
        q = r["question"].replace('"', "'")
        a = r["bad_answer"].replace('"', "'").replace("\n", " ")
        lines.append(f'  - question: "{q}"')
        lines.append(f'    bad_answer: "{a}"')
        lines.append(f'    session_id: "{r["session_id"]}"')
        lines.append('    label: ""   # corpus-miss | retrieval-miss | synthesis-poor | wrong-task-type')
    return "\n".join(lines) + "\n"


def main() -> int:
    records = asyncio.run(collect())
    sys.stdout.write(_yaml_dump(records))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
