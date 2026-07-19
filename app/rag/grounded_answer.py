"""Single-shot grounded answer: RLS retrieve -> one LLM call over retrieved context -> cite.

This is the minimal "retrieve + answer + cite" path with NO agent loop, workflow cards,
prerequisite planner or critic. It is the shared core behind the `/api/ask` endpoint and the
C0 evaluation arm (app/eval/c0_arm.py) — the "bare model + evidence" baseline the V2 stop-rule
compares against (plan QĐ-4). It keeps the non-negotiable safety gates (RLS-in-SQL retrieval,
audit-then-egress via the router, abstain-on-no-context, citation hygiene) because those are
invariants, not architecture.
"""
from __future__ import annotations

import re
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.llm import router as llm
from app.rag import retriever
from app.security.rls import Identity

_settings = get_settings()

# Canonical abstain sentence — detectable so citation hygiene drops sources on a refusal.
ABSTAIN = "Tôi không tìm thấy thông tin này trong tài liệu được phép truy cập."

SYSTEM = (
    "Bạn là chuyên gia hướng dẫn sử dụng & nghiệp vụ phần mềm BRAVO, trả lời người dùng nghiệp vụ.\n"
    "CHỈ dùng NGỮ CẢNH (các khối đánh số [1],[2],...) làm căn cứ sự thật; TUYỆT ĐỐI không bịa "
    "số liệu/định khoản, KHÔNG dùng kiến thức ngoài tài liệu.\n"
    "Khi CÓ căn cứ: trình bày CHI TIẾT, có CẤU TRÚC — chia các BƯỚC đánh số, mỗi bước nêu rõ thao "
    "tác (menu/màn hình/phím tắt/trường nhập nếu ngữ cảnh có), gạch đầu dòng cho lựa chọn con. "
    "Sau mỗi ý lấy từ ngữ cảnh, CHÈN trích dẫn [N] đúng số khối nguồn.\n"
    "Nếu ngữ cảnh CHỈ có một phần: trả lời phần CÓ, nói rõ phần còn thiếu, rồi GỢI Ý người dùng "
    "cung cấp tên chức năng/màn hình cụ thể để tra tiếp — KHÔNG dừng cụt.\n"
    "Nếu ngữ cảnh HOÀN TOÀN không liên quan/không chứa câu trả lời: trả lời DUY NHẤT câu sau, "
    f"không thêm gì: '{ABSTAIN}'\n"
    "Trả lời bằng tiếng Việt."
)


async def answer_grounded(db: AsyncSession, identity: Identity, question: str, *,
                          top_n: int = 12, temperature: float = 0.1) -> dict[str, Any]:
    """Retrieve RLS-scoped context and answer over it only. Returns
    {answer, grounded, citations, routed_cloud}. citations are dicts with source provenance."""
    chunks = await retriever.retrieve(db, identity, question, top_n=top_n)
    if not chunks:
        return {"answer": ABSTAIN, "grounded": False, "citations": [], "routed_cloud": False}

    context = "\n\n".join(f"[{i+1}] {c.content}\n{c.citation()}" for i, c in enumerate(chunks))
    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": f"NGỮ CẢNH:\n{context}\n\nCÂU HỎI: {question}"},
    ]
    # Egress: never hard-code sensitive=False. The router classifies context=chunks (fail-closed to
    # local for a sensitive department) and audits before any prompt leaves the network.
    answer, decision = await llm.chat(
        messages, context=chunks, db=db,
        allow_cloud_task=_settings.demo_allow_cloud_answers, temperature=temperature)

    # Fail-closed against "abstain then fabricate": if it OPENS with the abstain sentence, cut the
    # tail (a partial answer may mention 'không tìm thấy' mid-text, so match the prefix only).
    is_abstain = answer.strip().lower().startswith(ABSTAIN.lower()[:30])
    if is_abstain:
        answer = ABSTAIN
    grounded = not is_abstain
    if not grounded:
        cited: list[dict[str, Any]] = []
    else:
        nums = {int(n) for n in re.findall(r"\[(\d+)\]", answer)}
        used = [chunks[i - 1] for i in sorted(nums) if 1 <= i <= len(chunks)] or chunks
        cited = [{"source_id": str(c.source_id), "page_number": c.page_number,
                  "sheet_name": c.sheet_name, "cell_range": c.cell_range} for c in used]
    return {"answer": answer, "grounded": grounded, "citations": cited,
            "routed_cloud": getattr(decision, "backend", "local") == "cloud"}
