"""Embedding — local bge-m3 (production, ADR-0009) OR cloud API (demo, weak machine).

Switch via EMBEDDING_PROVIDER. For the demo the BRAVO 10 guides are non-sensitive
technical docs, so a cloud embedding API is acceptable; production flips back to local.
IMPORTANT: EMBEDDING_DIM must match the chosen model BEFORE creating the DB (the Vector
column size is fixed). bge-m3=1024; OpenAI text-embedding-3-small=1536, -large=3072.
"""
from __future__ import annotations

from functools import lru_cache

from app.config import get_settings

_settings = get_settings()


@lru_cache
def _local_model():
    from FlagEmbedding import BGEM3FlagModel  # lazy

    return BGEM3FlagModel(_settings.embedding_model, use_fp16=True)


@lru_cache
def _cloud_client():
    from openai import OpenAI  # lazy

    return OpenAI(base_url=_settings.cloud_embedding_base_url or None,
                  api_key=_settings.cloud_embedding_api_key)


def embed(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    if _settings.embedding_provider == "openai_compatible":
        client, model = _cloud_client(), _settings.cloud_embedding_model
        out: list[list[float]] = []
        for i in range(0, len(texts), 128):  # batch to stay under request-size limits
            resp = client.embeddings.create(model=model, input=texts[i:i + 128])
            out.extend(d.embedding for d in resp.data)
        return out
    vecs = _local_model().encode(texts, batch_size=16, max_length=8192)
    return [v.tolist() for v in vecs["dense_vecs"]]


def embed_one(text: str) -> list[float]:
    return embed([text])[0]
