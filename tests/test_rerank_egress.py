"""REM-EGRESS-02 — sensitive or unknown retrieval candidates never use cloud rerank."""
from __future__ import annotations

import uuid

import pytest

from app.rag import rerank, retriever
from app.rag.retriever import Retrieved
from app.security.rls import Identity


def _hit(*, sensitive: bool = True) -> Retrieved:
    return Retrieved(
        chunk_id=str(uuid.uuid4()), content="private passage", source_id=str(uuid.uuid4()),
        page_number=None, sheet_name=None, cell_range=None, score=1.0,
        is_sensitive=sensitive,
    )


@pytest.mark.asyncio
async def test_llm_rerank_propagates_explicit_sensitivity(monkeypatch):
    seen: dict[str, object] = {}

    async def fake_chat(_messages, **kwargs):
        seen.update(kwargs)
        return "0", object()

    monkeypatch.setattr("app.llm.router.chat", fake_chat)
    await rerank.llm_rerank("q", ["private passage"], 1, sensitive=True)
    assert seen["sensitive"] is True
    assert seen["allow_cloud_task"] is False


@pytest.mark.asyncio
async def test_retrieve_skips_llm_rerank_when_any_candidate_is_sensitive(monkeypatch):
    sensitive = _hit(sensitive=True)
    called = False

    async def fake_search(*_args, **_kwargs):
        return [sensitive]

    async def fake_llm_rerank(*_args, **_kwargs):
        nonlocal called
        called = True
        return [0]

    monkeypatch.setattr(retriever, "vector_search", fake_search)
    monkeypatch.setattr(retriever, "lexical_search", fake_search)
    monkeypatch.setattr(retriever, "rrf_fuse", lambda *_lists: [sensitive])
    monkeypatch.setattr(retriever, "boost_for_bravo_intent", lambda _q, rows: rows)
    monkeypatch.setattr(retriever._rerank, "llm_rerank", fake_llm_rerank)
    monkeypatch.setattr("app.config.get_settings", lambda: type("S", (), {
        "rerank_enabled": True, "retrieval_min_score": 0.0, "rerank_provider": "llm",
    })())

    rows = await retriever.retrieve(
        db=object(),
        identity=Identity(employee_id=uuid.uuid4(), permissions=frozenset({"doc:read:all"})),
        query="q",
        use_rerank=True,
    )
    assert rows == [sensitive]
    assert called is False
