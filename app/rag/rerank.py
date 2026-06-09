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
    """Return a relevance score per passage for (query, passage) pairs."""
    if not passages:
        return []
    scores = _model().predict([(query, p) for p in passages])
    return [float(s) for s in scores]
