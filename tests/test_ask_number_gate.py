"""Council blocker (RAG-C3): the /api/ask knowledge path (answer_grounded) previously ran NO
number-integrity gate — the gate lived only in answer_guarded. A hallucinated money figure could
reach the user with a citation they trust (invariant #3 violation). These pure-unit tests drive
answer_grounded with a fake retriever + LLM and assert the gate now masks ungrounded money.
"""
from __future__ import annotations

import asyncio
import types

from app.rag import grounded_answer
from app.rag.number_integrity import MASK


class _FakeChunk:
    def __init__(self, content: str, source_id: str = "s1", page: int = 8):
        self.content = content
        self.source_id = source_id
        self.page_number = page
        self.sheet_name = None
        self.cell_range = None

    def citation(self) -> str:
        return f"(nguồn {self.source_id} tr.{self.page_number})"


def _patch(monkeypatch, chunk_text: str, model_answer: str):
    async def fake_retrieve(db, identity, question, top_n=12):
        return [_FakeChunk(chunk_text)]

    async def fake_chat(messages, **kw):
        return model_answer, types.SimpleNamespace(backend="local")

    monkeypatch.setattr(grounded_answer.retriever, "retrieve", fake_retrieve)
    monkeypatch.setattr(grounded_answer.llm, "chat", fake_chat)


def test_ask_masks_ungrounded_money(monkeypatch):
    # Model invents 49,050,000 — not in the question nor the retrieved context.
    _patch(monkeypatch, "Hướng dẫn nhập phiếu chi.",
           "Tổng chi trước thuế là 49,050,000 đồng theo hướng dẫn [1].")
    res = asyncio.run(grounded_answer.answer_grounded(None, None, "cách nhập phiếu chi"))
    assert res["grounded"] is True
    assert res["integrity"]["ok"] is False
    assert 49_050_000 in res["integrity"]["ungrounded_numbers"]
    assert MASK in res["answer"] and "49,050,000" not in res["answer"]


def test_ask_keeps_grounded_money(monkeypatch):
    # The figure is present in the retrieved context -> trusted -> must survive untouched.
    _patch(monkeypatch, "Phí dịch vụ trọn gói là 1,200,000 đồng.",
           "Phí dịch vụ là 1,200,000 đồng [1].")
    res = asyncio.run(grounded_answer.answer_grounded(None, None, "phí dịch vụ bao nhiêu"))
    assert res["integrity"]["ok"] is True
    assert res["integrity"]["ungrounded_numbers"] == []
    assert "1,200,000" in res["answer"]
