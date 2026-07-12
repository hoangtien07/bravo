"""Embedding — local bge-m3 (production, ADR-0009) OR cloud API (demo, weak machine).

Switch via EMBEDDING_PROVIDER. For the demo the BRAVO 10 guides are non-sensitive
technical docs, so a cloud embedding API is acceptable; production flips back to local.
IMPORTANT: EMBEDDING_DIM must match the chosen model BEFORE creating the DB (the Vector
column size is fixed). bge-m3=1024; OpenAI text-embedding-3-small=1536, -large=3072.
"""
from __future__ import annotations

import hashlib
import logging
from functools import lru_cache

from app.config import get_settings

_settings = get_settings()
_log = logging.getLogger("bravo.egress")


@lru_cache
def _local_model():
    from FlagEmbedding import BGEM3FlagModel  # lazy

    return BGEM3FlagModel(_settings.embedding_model, use_fp16=True)


@lru_cache
def _cloud_client():
    from openai import OpenAI  # lazy

    return OpenAI(base_url=_settings.cloud_embedding_base_url or None,
                  api_key=_settings.cloud_embedding_api_key, timeout=30.0, max_retries=2)


def embed(texts: list[str], *, sensitive: bool = False) -> list[list[float]]:
    """Embed `texts`. `sensitive=True` (nội dung HR/kế toán/PII) -> CẤM egress lên cloud
    (invariant #4): nếu provider là cloud thì raise; nguồn nhạy phải dùng embedding local."""
    if not texts:
        return []
    if _settings.embedding_provider == "openai_compatible":
        # Egress-guard: KHÔNG nhúng nội dung nhạy lên cloud — TRỪ khi egress_policy=cloud_only
        # (ADR-0019/0022): không còn embedding local nên guard hạ xuống AUDIT (vẫn ghi vết ở
        # dưới), không chặn. Dưới policy hybrid (mặc định) guard vẫn fail-closed như cũ.
        if sensitive and _settings.egress_policy != "cloud_only":
            raise RuntimeError(
                "[egress-guard] Từ chối nhúng nội dung NHẠY (HR/kế toán/PII) lên cloud — "
                "đặt EMBEDDING_PROVIDER=local cho nguồn nhạy (invariant #4)."
            )
        # Audit-then-egress: ghi vết TRƯỚC khi text rời mạng (hash, không lưu nội dung thô).
        _log.info("embedding.egress provider=cloud model=%s n=%d hash=%s",
                  _settings.cloud_embedding_model, len(texts),
                  hashlib.sha256("\x01".join(texts).encode()).hexdigest()[:16])
        client, model = _cloud_client(), _settings.cloud_embedding_model
        out: list[list[float]] = []
        for i in range(0, len(texts), 128):  # batch to stay under request-size limits
            resp = client.embeddings.create(model=model, input=texts[i:i + 128])
            out.extend(d.embedding for d in resp.data)
        return out
    vecs = _local_model().encode(texts, batch_size=16, max_length=8192)
    return [v.tolist() for v in vecs["dense_vecs"]]


def embed_one(text: str, *, sensitive: bool = False) -> list[float]:
    return embed([text], sensitive=sensitive)[0]
