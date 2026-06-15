"""Durable AgentRun lifecycle (W2.2/2.3) — persist + paused-for-approval + resume-on-approve.

Lưu mỗi lượt agent thành một AgentRun trên Postgres lớp-AI (observability + HITL durable).
Khi lượt tạo bút toán/draft chờ duyệt -> status='paused_for_approval' + checkpoint_state.
Khi human DUYỆT draft của run đó -> complete_on_approval đánh dấu run 'done' ("duyệt = thực
thi"). lease_* (chống 2 worker) để dành — MVP chưa chạy nhiều worker.

Mọi hàm BEST-EFFORT khi gọi từ loop (unit-test dùng DB giả) — lỗi DB không được làm vỡ lượt.
"""
from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession


async def start_run(db: AsyncSession, *, run_id: uuid.UUID, session_id: uuid.UUID,
                    employee_id: uuid.UUID, idempotency_key: str | None = None) -> None:
    from app.database.models import AgentRun

    db.add(AgentRun(id=run_id, session_id=session_id, employee_id=employee_id,
                    status="running", idempotency_key=idempotency_key))
    await db.commit()


async def finish_run(db: AsyncSession, run_id: uuid.UUID, *, status: str,
                     checkpoint_state: dict | None = None) -> None:
    from app.database.models import AgentRun

    run = await db.get(AgentRun, run_id)
    if run is None:
        return
    run.status = status
    if checkpoint_state is not None:
        run.checkpoint_state = checkpoint_state
    await db.commit()


async def complete_on_approval(db: AsyncSession, run_id: uuid.UUID) -> None:
    """W2.3: khi draft của run được DUYỆT -> run 'done' (cái duyệt = cái thực thi)."""
    from app.database.models import AgentRun

    run = await db.get(AgentRun, run_id)
    if run is None:
        return
    if run.status in ("paused_for_approval", "running"):
        run.status = "done"
        await db.commit()
