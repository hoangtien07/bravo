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
from app.rag import number_integrity, retriever
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


# --------------------------------------------------------------------------------------------
# Guarded arm (B1): same RLS-scoped retrieval, but a prompt that MAY do useful things a strict
# grounded answer refuses (present a worked how-to, name TT200 accounts as *labeled suggestions*)
# WITHOUT relaxing invariant #3. Every money figure is gated by number_integrity against a
# trusted set = question numbers + retrieved context + optional money-engine facts. Derived
# figures (VAT/total) MUST come from `money_facts` (the deterministic engine), never the model.
GUARDED_SYSTEM = (
    "Bạn là chuyên gia hướng dẫn sử dụng & nghiệp vụ phần mềm BRAVO, trả lời người dùng nghiệp vụ.\n"
    "Dùng NGỮ CẢNH (khối đánh số [1],[2],...) cho THAO TÁC phần mềm (menu/màn hình/phím tắt/trường "
    "nhập); sau mỗi ý lấy từ ngữ cảnh CHÈN trích dẫn [N]. KHÔNG bịa thao tác không có trong ngữ cảnh.\n"
    "QUY TẮC SỐ (bất biến #3 — nghiêm ngặt): MỌI con số tiền/thuế/tổng PHẢI lấy NGUYÊN VĂN từ câu "
    "hỏi hoặc từ khối 'SỐ LIỆU MONEY-ENGINE' (nếu có). TUYỆT ĐỐI không tự tính lại, không suy ra số "
    "tiền mới. Nếu cần một con số dẫn xuất (thuế/tổng) mà KHÔNG có trong hai nguồn đó: nói 'cần tính "
    "qua money-engine', không tự bịa.\n"
    "Số hiệu tài khoản kế toán: được PHÉP gợi ý theo chuẩn TT200 nhưng BẮT BUỘC gắn nhãn '(gợi ý — "
    "kế toán đối chiếu hệ thống tài khoản của đơn vị)'; KHÔNG gắn [N] cho phần gợi ý này.\n"
    "Nếu câu hỏi có phân bổ nhiều bộ phận: bung mỗi bộ phận thành một DÒNG hạch toán (TK nợ + số "
    "tiền + bộ phận). Trình bày theo BƯỚC đánh số. KHÔNG lặp lại nhãn nội bộ ('SỐ LIỆU MONEY-ENGINE') "
    "trong câu trả lời. Trả lời bằng tiếng Việt.\n"
    f"Nếu ngữ cảnh HOÀN TOÀN không liên quan và KHÔNG có số liệu engine: trả lời DUY NHẤT: '{ABSTAIN}'"
)


async def answer_guarded(db: AsyncSession, identity: Identity, question: str, *,
                         money_facts: str | None = None, top_n: int = 12,
                         temperature: float = 0.1) -> dict[str, Any]:
    """Guarded how-to answer. Returns the answer_grounded shape plus an ``integrity`` block
    {ok, ungrounded_numbers}. ``money_facts`` is a pre-computed money-engine text block (numbers
    the model must treat as the ONLY source of derived figures); pass it from an accounting
    context (parsed invoice -> build_journal_entry) — this function never lets the LLM compute money.
    """
    chunks = await retriever.retrieve(db, identity, question, top_n=top_n)
    if not chunks and not money_facts:
        return {"answer": ABSTAIN, "grounded": False, "citations": [], "routed_cloud": False,
                "integrity": {"ok": True, "ungrounded_numbers": []}}

    context = "\n\n".join(f"[{i+1}] {c.content}\n{c.citation()}" for i, c in enumerate(chunks))
    facts_block = f"\n\nSỐ LIỆU MONEY-ENGINE (nguồn sự thật cho MỌI con số):\n{money_facts}" \
        if money_facts else ""
    messages = [
        {"role": "system", "content": GUARDED_SYSTEM},
        {"role": "user", "content": f"NGỮ CẢNH:\n{context}{facts_block}\n\nCÂU HỎI: {question}"},
    ]
    answer, decision = await llm.chat(
        messages, context=chunks, db=db,
        allow_cloud_task=_settings.demo_allow_cloud_answers, temperature=temperature)

    answer = number_integrity.strip_markers(answer)
    is_abstain = answer.strip().lower().startswith(ABSTAIN.lower()[:30])
    if is_abstain:
        answer = ABSTAIN
    grounded = not is_abstain

    # Integrity gate: trusted numbers = question + retrieved context + engine facts.
    allowed = number_integrity.allowed_from(question, context, money_facts or "")
    ungrounded = number_integrity.violations(answer, allowed) if grounded else []

    if not grounded:
        cited: list[dict[str, Any]] = []
    else:
        nums = {int(n) for n in re.findall(r"\[(\d+)\]", answer)}
        used = [chunks[i - 1] for i in sorted(nums) if 1 <= i <= len(chunks)] or chunks
        cited = [{"source_id": str(c.source_id), "page_number": c.page_number,
                  "sheet_name": c.sheet_name, "cell_range": c.cell_range} for c in used]
    return {"answer": answer, "grounded": grounded, "citations": cited,
            "routed_cloud": getattr(decision, "backend", "local") == "cloud",
            "integrity": {"ok": not ungrounded, "ungrounded_numbers": ungrounded}}
