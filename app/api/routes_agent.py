"""Agentic Q&A endpoint (Phase 2) — exposes the constrained-agentic loop over HTTP.

Unlike `/ask` (single-shot retrieve+cite, ADR Phase-1 MVP), `/agent/ask` drives the full
`AgentSession` (ADR-0010): RLS retrieval -> tool ReAct (metric engine / draft) -> verify-gate
(WP-B, no fabricated numbers) -> router egress-audit (WP-C). Tools are RLS-filtered per the
caller's identity, so a metric/draft tool only exists for a user who holds the permission.

The loop NEVER writes to the ERP: a write tool produces a Draft for human approval (invariant
#2), surfaced via `/api/drafts`. Numbers come only from the engine; any unverified number is
masked before the answer leaves this endpoint (invariant #3).
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.loop import AgentSession
from app.database import get_db
from app.security.auth import require_permission
from app.security.rls import Identity

router = APIRouter()


class AgentAskRequest(BaseModel):
    question: str
    session_id: uuid.UUID | None = None   # pass back to continue a multi-turn session


class AgentAskResponse(BaseModel):
    answer: str
    grounded: bool
    citations: list[str] = []
    clarify: bool = False                 # the agent asked a clarifying question instead
    routed_cloud: bool = False            # True if any LLM call egressed to cloud (audited)
    stopped: str | None = None            # e.g. "budget" if a safety limit halted the turn
    session_id: str


@router.post("/agent/ask", response_model=AgentAskResponse)
async def agent_ask(
    req: AgentAskRequest,
    identity: Identity = Depends(require_permission("doc:read")),
    db: AsyncSession = Depends(get_db),
) -> AgentAskResponse:
    session = AgentSession(db, identity, session_id=req.session_id)
    out = await session.step(req.question)
    return AgentAskResponse(
        answer=out.get("answer", ""),
        grounded=bool(out.get("grounded")),
        citations=list(out.get("citations", []) or []),
        clarify=bool(out.get("clarify", False)),
        routed_cloud=bool(out.get("routed_cloud", False)),
        stopped=out.get("stopped"),
        session_id=out.get("session_id", str(session.session_id)),
    )
