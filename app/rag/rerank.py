"""Cross-encoder reranking (ViRanker — Vietnamese, findings/J/I).

Reranking is the single biggest retrieval-quality lever (findings/J: -67% failure /
+17 pts). Applied to the fused candidate set: top-150 -> rerank -> top-20.
Loaded lazily; runs on-prem.
"""
from __future__ import annotations

from functools import lru_cache

RERANKER_MODEL = "namdp-ptit/ViRanker"  # Vietnamese cross-encoder on BGE-M3


@lru_cache
def _model():
    from sentence_transformers import CrossEncoder  # lazy import

    return CrossEncoder(RERANKER_MODEL, max_length=512)


def rerank(query: str, passages: list[str]) -> list[float]:
    """Return a relevance score per passage for (query, passage) pairs (ViRanker)."""
    if not passages:
        return []
    scores = _model().predict([(query, p) for p in passages])
    return [float(s) for s in scores]


async def llm_rerank(query: str, passages: list[str], top_n: int, *, sensitive: bool) -> list[int]:
    """Listwise rerank via the cloud chat model (demo). Returns ranked passage indices.

    Cheap and provider-agnostic (uses the chat model already configured). Used when no
    local reranker is available (machine too weak). Falls back to original order on error.
    """
    import re

    from app.llm import router as llm

    # Snippet head+tail ~700 ký tự (council 2026-07-12 #1): chunk dài tới ~2.700 ký tự,
    # cắt 280 làm reranker chỉ thấy heading + 1-2 câu đầu — phần thân (các bước thao tác)
    # vô hình với người chấm.
    def _snippet(p: str) -> str:
        return p if len(p) <= 700 else p[:500] + " … " + p[-180:]

    listing = "\n".join(f"[{i}] {_snippet(p)}" for i, p in enumerate(passages))
    prompt = (
        f"Câu hỏi: {query}\n\nCác đoạn trích:\n{listing}\n\n"
        f"Chọn tối đa {top_n} đoạn LIÊN QUAN NHẤT để trả lời câu hỏi. "
        f"Chỉ trả về số thứ tự trong [], theo thứ tự liên quan giảm dần, cách nhau bởi dấu phẩy. "
        f"Ví dụ: 3,0,7"
    )
    try:
        ans, _ = await llm.chat(
            [{"role": "user", "content": prompt}],
            sensitive=sensitive,
            allow_cloud_task=not sensitive,
            temperature=0,
        )
        seen, order = set(), []
        for x in re.findall(r"\d+", ans):
            i = int(x)
            if 0 <= i < len(passages) and i not in seen:
                seen.add(i)
                order.append(i)
        return order[:top_n] or list(range(min(top_n, len(passages))))
    except Exception:  # noqa: BLE001 — degrade to original fused order
        return list(range(min(top_n, len(passages))))

