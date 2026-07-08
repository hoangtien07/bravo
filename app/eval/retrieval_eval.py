"""Đánh giá truy hồi (recall@k) trên corpus tiếng Việt — phát hiện regression chất lượng RAG.

Mỗi mục: câu hỏi nghiệp vụ + CHƯƠNG/nguồn KỲ VỌNG (substring trong knowledge_type/filename).
recall@k = tỉ lệ câu mà nguồn kỳ vọng xuất hiện trong top-k chunk truy hồi. Dùng để bắt
regression khi đổi model/prompt/chunking/rerank (đúng mối lo "chat không đáp ứng").

Chạy: DATABASE_URL=... PYTHONPATH=. python -m app.eval.retrieval_eval   (cần Postgres + corpus).
"""
from __future__ import annotations

import asyncio
import uuid

from app.database import async_session_factory
from app.rag import retriever
from app.security.rls import Identity

# (câu hỏi, chương/nguồn kỳ vọng) — bám corpus BRAVO 10 đã ingest.
GOLD: list[tuple[str, str]] = [
    ("Quy trình nhập hóa đơn mua hàng trong BRAVO 10", "Purchases"),
    ("Cách khai báo chứng từ kế toán", "Accounting"),
    ("Quản lý nhân sự HRM gồm những chức năng gì", "HRM"),
    ("Bán lẻ tại cửa hàng làm thế nào", "SalesRetail"),
    ("Quản lý hàng tồn kho", "Inventory"),
    ("Kiểm soát chất lượng QC", "QC"),
    ("Quản lý sản xuất", "ProductionManagement"),
    ("Quản lý quan hệ khách hàng CRM", "CRM"),
    ("Quản lý công việc và nhiệm vụ", "Task"),
    ("Báo cáo BI và dashboard", "BI"),
    ("Đơn đặt hàng bán hàng", "Sale"),
    ("Quản lý máy móc thiết bị", "MachineManagement"),
]


async def _labels(db, chunks) -> dict[str, str]:
    from sqlalchemy import select

    from app.database.models import Source
    ids = {getattr(c, "source_id", None) for c in chunks}
    ids.discard(None)
    if not ids:
        return {}
    rows = (await db.execute(
        select(Source).where(Source.id.in_([uuid.UUID(x) for x in ids])))).scalars().all()
    return {str(s.id): f"{s.knowledge_type or ''} {s.filename or ''}" for s in rows}


async def main(k: int = 6, identity: Identity | None = None) -> float:
    # Mặc định admin (không bị RLS lọc). Truyền Identity phòng ban -> eval PER-DOMAIN dưới RLS
    # (recall@k trong phạm vi phòng). Kết hợp probes.assert_no_leak để chặn rò chéo phòng (Phase 2).
    ident = identity or Identity(employee_id=uuid.uuid4(), is_admin=True)
    hits = 0
    async with async_session_factory() as db:
        for q, exp in GOLD:
            chunks = await retriever.retrieve(db, ident, q, top_n=k)
            labels = await _labels(db, chunks)
            ok = any(exp.lower() in labels.get(getattr(c, "source_id", None), "").lower()
                     for c in chunks)
            hits += int(ok)
            print(f"  [{'✓' if ok else '✗'}] {q[:46]:46} -> '{exp}'")
    n = len(GOLD)
    print(f"\nrecall@{k} = {hits}/{n} = {hits / n:.0%}")
    return hits / n


if __name__ == "__main__":
    asyncio.run(main())
