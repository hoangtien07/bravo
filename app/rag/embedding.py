"""Local embedding (bge-m3 — ADR-0009). Loaded lazily; runs on-prem (no cloud)."""
from __future__ import annotations

from functools import lru_cache

from app.config import get_settings

_settings = get_settings()


@lru_cache
def _model():
    # Imported lazily so the API can boot without the model present (dev).
    from FlagEmbedding import BGEM3FlagModel

    return BGEM3FlagModel(_settings.embedding_model, use_fp16=True)


def embed(texts: list[str]) -> list[list[float]]:
    """Dense embeddings for a batch of texts."""
    out = _model().encode(texts, batch_size=16, max_length=8192)
    return [v.tolist() for v in out["dense_vecs"]]


def embed_one(text: str) -> list[float]:
    return embed([text])[0]
