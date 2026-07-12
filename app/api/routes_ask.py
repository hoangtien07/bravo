"""Knowledge Q&A endpoint (Phase 1 MVP).

Flow: RLS-scoped retrieval -> if no grounded context, REFUSE (no hallucination) ->
else LLM interprets ONLY the retrieved context and answers WITH citations.
The LLM never invents numbers (ADR-0004); it summarizes grounded chunks + cites.
"""
from __future__ import annotations

import re

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.llm import router as llm
from app.rag import retriever
from app.security.auth import require_permission
from app.security.rls import Identity

_settings = get_settings()

router = APIRouter()

# Câu abstain CHUẨN (dùng cho cả prompt lẫn nhánh không có ngữ cảnh) -> phát hiện được để
# citation-hygiene: khi trả lời là abstain thì KHÔNG đính citations (tránh trích dẫn nguồn không dùng).
_ABSTAIN = "Tôi không tìm thấy thông tin này trong tài liệu được phép truy cập."

_SYSTEM = (
    "Bạn là chuyên gia hướng dẫn sử dụng & nghiệp vụ phần mềm BRAVO, trả lời người dùng nghiệp vụ.\n"
    "CHỈ dùng NGỮ CẢNH (các khối đánh số [1],[2],...) làm căn cứ sự thật; TUYỆT ĐỐI không bịa "
    "số liệu/định khoản, KHÔNG dùng kiến thức ngoài tài liệu.\n"
    "Khi CÓ căn cứ: trình bày CHI TIẾT, có CẤU TRÚC — chia các BƯỚC đánh số, mỗi bước nêu rõ thao "
    "tác (menu/màn hình/phím tắt/trường nhập nếu ngữ cảnh có), gạch đầu dòng cho lựa chọn con. "
    "Sau mỗi ý lấy từ ngữ cảnh, CHÈN trích dẫn [N] đúng số khối nguồn.\n"
    "Nếu ngữ cảnh CHỈ có một phần: trả lời phần CÓ, nói rõ phần còn thiếu, rồi GỢI Ý người dùng "
    "cung cấp tên chức năng/màn hình cụ thể để tra tiếp — KHÔNG dừng cụt.\n"
    "Nếu ngữ cảnh HOÀN TOÀN không liên quan/không chứa câu trả lời: trả lời DUY NHẤT câu sau, "
    f"không thêm gì: '{_ABSTAIN}'\n"
    "Trả lời bằng tiếng Việt."
)


class AskRequest(BaseModel):
    question: str


class Citation(BaseModel):
    source_id: str
    page_number: int | None = None
    sheet_name: str | None = None
    cell_range: str | None = None


class AskResponse(BaseModel):
    answer: str
    citations: list[Citation]
    grounded: bool


@router.post("/ask", response_model=AskResponse)
async def ask(
    req: AskRequest,
    identity: Identity = Depends(require_permission("doc:read")),
    db: AsyncSession = Depends(get_db),
) -> AskResponse:
    # top_n cao hơn -> nhiều ngữ cảnh hơn cho câu trả lời CHI TIẾT (giữ nguyên grounding).
    chunks = await retriever.retrieve(db, identity, req.question, top_n=12)

    # Grounding / refusal gate (findings/H) — no context => refuse, don't hallucinate.
    if not chunks:
        return AskResponse(answer=_ABSTAIN, citations=[], grounded=False)

    context = "\n\n".join(f"[{i+1}] {c.content}\n{c.citation()}" for i, c in enumerate(chunks))
    messages = [
        {"role": "system", "content": _SYSTEM},
        {"role": "user", "content": f"NGỮ CẢNH:\n{context}\n\nCÂU HỎI: {req.question}"},
    ]
    # Egress (invariant #4): KHÔNG hard-code sensitive=False. Truyền context=chunks + db để
    # router TỰ classify_context (fail-closed -> local nếu chunk thuộc phòng nhạy) và
    # audit-then-egress trước khi prompt rời mạng. Demo: chunk cẩm nang non-sensitive -> cloud.
    answer, _decision = await llm.chat(
        messages, context=chunks, db=db,
        allow_cloud_task=_settings.demo_allow_cloud_answers, temperature=0.1,
    )

    # Chặn 'abstain rồi bịa tiếp' (fail-closed): đã có câu abstain -> cắt mọi phần đuôi
    # (model có lúc mở đầu abstain rồi vẫn tự sinh các bước từ kiến thức ngoài, không nguồn).
    if _ABSTAIN in answer:
        answer = _ABSTAIN
    # Citation-hygiene: abstain -> KHÔNG đính nguồn; nếu answer có marker [N] -> CHỈ trả nguồn
    # thực sự được trích; không có marker -> giữ toàn bộ (câu trả lời grounded nhưng model không đánh số).
    grounded = _ABSTAIN not in answer
    if not grounded:
        cited = []
    else:
        nums = {int(n) for n in re.findall(r"\[(\d+)\]", answer)}
        used = [chunks[i - 1] for i in sorted(nums) if 1 <= i <= len(chunks)] or chunks
        cited = [
            Citation(source_id=c.source_id, page_number=c.page_number,
                     sheet_name=c.sheet_name, cell_range=c.cell_range)
            for c in used
        ]
    return AskResponse(answer=answer, citations=cited, grounded=grounded)
