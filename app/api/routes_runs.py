"""Durable agent-run status, replay and cooperative cancellation API."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent import runs
from app.database import get_db
from app.database.models import AgentRun, AgentRunEvent
from app.security.auth import get_current_identity
from app.security.rls import Identity

router = APIRouter()


async def _owned_run(db: AsyncSession, run_id: uuid.UUID, identity: Identity) -> AgentRun:
    stmt = select(AgentRun).where(AgentRun.id == run_id)
    if not identity.is_admin:
        stmt = stmt.where(AgentRun.employee_id == identity.employee_id)
    run = (await db.execute(stmt)).scalar_one_or_none()
    if run is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tác vụ không tồn tại hoặc ngoài phạm vi")
    return run


def _run_out(run: AgentRun) -> dict:
    return {
        "id": str(run.id), "conversation_id": str(run.session_id), "status": run.status,
        "mode": run.mode, "plan": run.plan or {}, "cancel_requested": run.cancel_requested,
        "tokens_used": run.tokens_used, "created_at": run.created_at, "completed_at": run.completed_at,
    }


@router.get("/agent-runs/{run_id}")
async def get_run(run_id: uuid.UUID, identity: Identity = Depends(get_current_identity),
                  db: AsyncSession = Depends(get_db)) -> dict:
    return _run_out(await _owned_run(db, run_id, identity))


@router.get("/agent-runs/{run_id}/events")
async def get_run_events(run_id: uuid.UUID, after_seq: int = Query(0, ge=0),
                         identity: Identity = Depends(get_current_identity),
                         db: AsyncSession = Depends(get_db)) -> dict:
    await _owned_run(db, run_id, identity)
    rows = list((await db.execute(select(AgentRunEvent).where(
        AgentRunEvent.agent_run_id == run_id, AgentRunEvent.seq > after_seq
    ).order_by(AgentRunEvent.seq))).scalars().all())
    return {"events": [{"seq": row.seq, "type": row.event_type, "payload": row.payload,
                         "created_at": row.created_at} for row in rows]}


@router.post("/agent-runs/{run_id}/cancel", status_code=status.HTTP_202_ACCEPTED)
async def cancel_run(run_id: uuid.UUID, identity: Identity = Depends(get_current_identity),
                     db: AsyncSession = Depends(get_db)) -> dict:
    await _owned_run(db, run_id, identity)
    accepted = await runs.request_cancel(db, run_id)
    return {"accepted": accepted, "run_id": str(run_id)}
