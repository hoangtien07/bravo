"""Knowledge Q&A endpoint (Phase 1 MVP).

Flow: RLS-scoped retrieval -> if no grounded context, REFUSE (no hallucination) ->
else LLM interprets ONLY the retrieved context and answers WITH citations.
The LLM never invents numbers (ADR-0004); it summarizes grounded chunks + cites.
"""
from __future__ import annotations

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

_SYSTEM = (
    "Bạn là trợ lý tri thức nội bộ. CHỈ trả lời dựa trên NGỮ CẢNH được cung cấp. "
    "Nếu ngữ cảnh không đủ căn cứ, hãy nói 'Tôi không tìm thấy thông tin này trong tài liệu được phép truy cập.' "
    "TUYỆT ĐỐI không bịa số liệu; mọi khẳng định phải bám ngữ cảnh. Trả lời bằng tiếng Việt, kèm trích dẫn nguồn."
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
    chunks = await retriever.retrieve(db, identity, req.question, top_n=8)

    # Grounding / refusal gate (findings/H) — no context => refuse, don't hallucinate.
    if not chunks:
        return AskResponse(
            answer="Tôi không tìm thấy thông tin này trong tài liệu bạn được phép truy cập.",
            citations=[], grounded=False,
        )

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

    return AskResponse(
        answer=answer,
        citations=[
            Citation(source_id=c.source_id, page_number=c.page_number,
                     sheet_name=c.sheet_name, cell_range=c.cell_range)
            for c in chunks
        ],
        grounded=True,
    )
