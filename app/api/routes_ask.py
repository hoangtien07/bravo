"""Knowledge Q&A endpoint (Phase 1 MVP).

Flow: RLS-scoped retrieval -> if no grounded context, REFUSE (no hallucination) ->
else LLM interprets ONLY the retrieved context and answers WITH citations.
The LLM never invents numbers (ADR-0004); it summarizes grounded chunks + cites.

The retrieve+answer+cite core is shared with the C0 evaluation arm in
app/rag/grounded_answer.py (single source of truth for the "bare model + evidence" path).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.rag.grounded_answer import answer_grounded
from app.security.auth import require_permission
from app.security.rls import Identity

router = APIRouter()


class AskRequest(BaseModel):
    question: str


class Citation(BaseModel):
    source_id: str
    page_number: int | None = None
    sheet_name: str | None = None
    cell_range: str | None = None


class Integrity(BaseModel):
    ok: bool = True
    ungrounded_numbers: list[int] = []


class AskResponse(BaseModel):
    answer: str
    citations: list[Citation]
    grounded: bool
    integrity: Integrity = Integrity()


@router.post("/ask", response_model=AskResponse)
async def ask(
    req: AskRequest,
    identity: Identity = Depends(require_permission("doc:read")),
    db: AsyncSession = Depends(get_db),
) -> AskResponse:
    result = await answer_grounded(db, identity, req.question, top_n=12)
    return AskResponse(
        answer=result["answer"], grounded=result["grounded"],
        citations=[Citation(**c) for c in result["citations"]],
        integrity=Integrity(**result.get("integrity", {})))
