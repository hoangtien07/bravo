"""C0 — the 'bare model + evidence' evaluation arm (plan QĐ-4, stop-rule).

C0 is the same cloud model + the same RLS-scoped retrieved evidence + a simple prompt, with NO
agent loop, workflow cards, prerequisite planner or critic. It is the floor every V2 architecture
must beat: if C0 already wins/ties against BravoGen, the leverage is evidence + moat features
(numbers-with-sources, RLS, maker-checker), not reasoning architecture — so do NOT build the
expensive V2 core (plan P3.0 checkpoint).

C0Arm satisfies the eval StepLoop protocol (`async step(user_message) -> dict`, app/eval/passk.py)
so it slots into the same pass^k / A-B-C harness as the legacy and consultant paths. It shares the
platform services (retrieval, router egress) via app/rag/grounded_answer but owns a trivial reason
step — that is the whole point of the baseline.
"""
from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.rag.grounded_answer import answer_grounded
from app.security.rls import Identity


class C0Arm:
    """Minimal retrieve->answer->cite arm, StepLoop-compatible for the eval harness."""

    def __init__(self, db: AsyncSession, identity: Identity,
                 session_id: uuid.UUID | None = None, *, top_n: int = 12):
        self.db = db
        self.identity = identity
        self.session_id = session_id or uuid.uuid4()
        self.top_n = top_n

    async def step(self, user_message: str) -> dict[str, Any]:
        result = await answer_grounded(self.db, self.identity, user_message, top_n=self.top_n)
        # citations as compact strings for parity with the other arms' StepLoop output.
        citations = []
        for c in result["citations"]:
            parts = [c["source_id"]]
            if c.get("page_number"):
                parts.append(f"trang {c['page_number']}")
            if c.get("sheet_name"):
                parts.append(f"sheet {c['sheet_name']}")
            if c.get("cell_range"):
                parts.append(f"ô {c['cell_range']}")
            citations.append(", ".join(parts))
        return {"answer": result["answer"], "grounded": result["grounded"],
                "citations": citations, "routed_cloud": result["routed_cloud"],
                "session_id": str(self.session_id)}
