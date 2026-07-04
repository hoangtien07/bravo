"""Agent demo endpoints (NỘI BỘ, chạy trên MOCK) — quét bất thường -> cờ nháp chờ duyệt.

Engine tất định (app/agent/anomaly.py) tìm bất thường; mỗi cờ tạo một Draft(kind="anomaly_flag")
đi qua maker-checker (non-invasive: chỉ FLAG chờ người xác nhận). Idempotent: bỏ qua cờ đã có
draft pending cùng payload_hash. Số liệu từ engine, KHÔNG do LLM sinh.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent import anomaly
from app.agent.tools import payload_hash
from app.data_layer.mock_source import MockDataSource
from app.database import get_db
from app.erp import draft_queue
from app.security.auth import require_permission
from app.security.rls import Identity

router = APIRouter()


class ScanOut(BaseModel):
    created: int
    total_flags: int


@router.post("/agents/anomaly/scan", response_model=ScanOut)
async def scan_anomaly(identity: Identity = Depends(require_permission("draft:create")),
                       db: AsyncSession = Depends(get_db)) -> ScanOut:
    src = MockDataSource()
    flags = anomaly.detect(src.fetch_block("journal_entries"), src.fetch_block("anomalies"))
    existing = {d.payload_hash for d in
                await draft_queue.list_drafts(db, identity, status="pending", kind="anomaly_flag")}
    created = 0
    for f in flags:
        payload = f.to_payload()
        if payload_hash(payload) in existing:
            continue
        await draft_queue.create_draft(db, identity, kind="anomaly_flag", payload=payload)
        created += 1
    return ScanOut(created=created, total_flags=len(flags))
