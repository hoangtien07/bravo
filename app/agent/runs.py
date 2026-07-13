"""Durable AgentRun lifecycle (W2.2/2.3) — persist + paused-for-approval + resume-on-approve.

Lưu mỗi lượt agent thành một AgentRun trên Postgres lớp-AI (observability + HITL durable).
Khi lượt tạo bút toán/draft chờ duyệt -> status='paused_for_approval' + checkpoint_state.
Khi human DUYỆT draft của run đó -> complete_on_approval đánh dấu run 'done' ("duyệt = thực
thi"). lease_* (chống 2 worker) để dành — MVP chưa chạy nhiều worker.

Mọi hàm BEST-EFFORT khi gọi từ loop (unit-test dùng DB giả) — lỗi DB không được làm vỡ lượt.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession


async def start_run(db: AsyncSession, *, run_id: uuid.UUID, session_id: uuid.UUID,
                    employee_id: uuid.UUID, idempotency_key: str | None = None,
                    mode: str = "auto", plan: dict | None = None) -> None:
    from app.database.models import AgentRun

    db.add(AgentRun(id=run_id, session_id=session_id, employee_id=employee_id,
                    status="running", idempotency_key=idempotency_key, mode=mode,
                    plan=plan or {}))
    await db.commit()


async def finish_run(db: AsyncSession, run_id: uuid.UUID, *, status: str,
                     checkpoint_state: dict | None = None, tokens_used: int | None = None) -> None:
    from app.database.models import AgentRun

    run = await db.get(AgentRun, run_id)
    if run is None:
        return
    run.status = status
    if checkpoint_state is not None:
        run.checkpoint_state = checkpoint_state
    if tokens_used is not None:
        run.tokens_used = int(tokens_used)
    if status in {"done", "completed", "failed", "cancelled"}:
        run.completed_at = datetime.now(timezone.utc)
    await db.commit()


async def update_plan(db: AsyncSession, run_id: uuid.UUID, plan: dict) -> None:
    """Persist a client-safe research plan for reconnect/status views."""
    from app.database.models import AgentRun

    run = await db.get(AgentRun, run_id)
    if run is None:
        return
    run.plan = plan
    await db.commit()


def _client_safe_event(event: dict) -> tuple[str, dict] | None:
    """Persist only client-safe progress data; tool arguments and answer token deltas stay out."""
    kind = str(event.get("type") or "")
    if kind in {"answer", "ping", "id", "attachments"}:
        return None
    if kind == "tool_call":
        return kind, {"tool": event.get("tool")}
    if kind == "tool_result":
        return kind, {"tool": event.get("tool"), "isError": bool(event.get("isError")),
                      "summary": str(event.get("summary") or "")[:500]}
    allowed = {"source", "status", "step", "draft", "done", "error", "plan", "plan_update", "artifact"}
    if kind not in allowed:
        return None
    return kind, {k: v for k, v in event.items() if k != "type"}


async def record_event(db: AsyncSession, run_id: uuid.UUID, event: dict) -> None:
    """Append an event for reconnect/status views without storing sensitive tool args."""
    safe = _client_safe_event(event)
    if safe is None:
        return
    from app.database.models import AgentRun, AgentRunEvent

    event_type, payload = safe
    # Event writers include the streaming worker and the cancellation endpoint. Locking the
    # parent row makes max(seq)+1 safe across sessions without exposing a global sequence.
    await db.execute(select(AgentRun.id).where(AgentRun.id == run_id).with_for_update())
    next_seq = (await db.execute(
        select(func.coalesce(func.max(AgentRunEvent.seq), 0) + 1)
        .where(AgentRunEvent.agent_run_id == run_id))).scalar_one()
    db.add(AgentRunEvent(agent_run_id=run_id, seq=int(next_seq), event_type=event_type,
                         payload=payload))
    await db.commit()


async def request_cancel(db: AsyncSession, run_id: uuid.UUID) -> bool:
    """Mark cancellation cooperatively; workers/loops observe it at their next safe boundary."""
    from app.database.models import AgentRun

    run = await db.get(AgentRun, run_id)
    if run is None or run.status in {"done", "completed", "failed", "cancelled"}:
        return False
    run.cancel_requested = True
    await db.commit()
    await record_event(db, run_id, {"type": "status", "text": "Đã yêu cầu dừng tác vụ."})
    return True


async def is_cancel_requested(db: AsyncSession, run_id: uuid.UUID) -> bool:
    from app.database.models import AgentRun

    run = await db.get(AgentRun, run_id)
    return bool(run and run.cancel_requested)


async def complete_on_approval(db: AsyncSession, run_id: uuid.UUID) -> None:
    """W2.3: khi draft của run được DUYỆT -> run 'done' (cái duyệt = cái thực thi)."""
    from app.database.models import AgentRun

    run = await db.get(AgentRun, run_id)
    if run is None:
        return
    if run.status in ("paused_for_approval", "running"):
        run.status = "done"
        await db.commit()
