"""W0.3 — embedding egress guard (invariant #4).

Nội dung NHẠY không bao giờ được nhúng-embed lên cloud. Nội dung thường đi cloud thì
phải để lại VẾT AUDIT (log) trước khi rời mạng.
"""
from __future__ import annotations

import pytest

from app.rag import embedding


def test_sensitive_content_refused_on_cloud(monkeypatch):
    monkeypatch.setattr(embedding._settings, "embedding_provider", "openai_compatible")
    with pytest.raises(RuntimeError, match="egress-guard"):
        embedding.embed(["bảng lương nhân viên tháng 6"], sensitive=True)
    with pytest.raises(RuntimeError, match="egress-guard"):
        embedding.embed_one("số CMND 0123", sensitive=True)


def test_local_provider_ignores_guard(monkeypatch):
    # provider=local: guard không áp (sẽ cố nạp model — chỉ kiểm tới nhánh, mock encode).
    monkeypatch.setattr(embedding._settings, "embedding_provider", "local")

    class _Vec(list):
        def tolist(self):
            return list(self)

    class _FakeModel:
        def encode(self, texts, **kw):
            return {"dense_vecs": [_Vec([0.0, 1.0]) for _ in texts]}

    monkeypatch.setattr(embedding, "_local_model", lambda: _FakeModel())
    out = embedding.embed(["nội dung nhạy"], sensitive=True)  # local: không raise
    assert out == [[0.0, 1.0]]


def test_cloud_non_sensitive_audits(monkeypatch, caplog):
    import logging

    monkeypatch.setattr(embedding._settings, "embedding_provider", "openai_compatible")
    monkeypatch.setattr(embedding._settings, "cloud_embedding_model", "text-embedding-3-small")

    class _Resp:
        def __init__(self, n):
            self.data = [type("D", (), {"embedding": [0.1, 0.2]})() for _ in range(n)]

    class _FakeClient:
        class embeddings:
            @staticmethod
            def create(model, input):
                return _Resp(len(input))

    monkeypatch.setattr(embedding, "_cloud_client", lambda: _FakeClient())
    with caplog.at_level(logging.INFO, logger="bravo.egress"):
        out = embedding.embed(["cẩm nang BRAVO chương 1"])
    assert len(out) == 1
    assert any("embedding.egress" in r.message for r in caplog.records)


def test_cloud_only_policy_allows_sensitive_embed_with_audit(monkeypatch, caplog):
    """ADR-0019: under cloud_only there is no local embedder, so the sensitive-raise is
    downgraded to an audit log — sensitive content embeds on cloud but leaves a trail."""
    import logging
    monkeypatch.setattr(embedding._settings, "embedding_provider", "openai_compatible")
    monkeypatch.setattr(embedding._settings, "egress_policy", "cloud_only")
    monkeypatch.setattr(embedding._settings, "cloud_embedding_model", "text-embedding-3-small")

    class _Resp:
        def __init__(self, n):
            self.data = [type("D", (), {"embedding": [0.1, 0.2]})() for _ in range(n)]

    class _FakeClient:
        class embeddings:
            @staticmethod
            def create(model, input):
                return _Resp(len(input))

    monkeypatch.setattr(embedding, "_cloud_client", lambda: _FakeClient())
    with caplog.at_level(logging.INFO, logger="bravo.egress"):
        out = embedding.embed(["bảng lương tháng 6"], sensitive=True)  # would raise under hybrid
    assert out == [[0.1, 0.2]]
    assert any("embedding.egress" in r.message for r in caplog.records)
