"""B1 — guarded answer arm: worked how-to + labeled TT200 suggestions, money gated by
number-integrity. Pure-unit (retriever + router mocked)."""
from __future__ import annotations

import asyncio
import uuid

from app.rag.grounded_answer import ABSTAIN, answer_guarded
from app.security.rls import Identity


class _Chunk:
    def __init__(self, sid, content, page=None):
        self.source_id, self.content, self.page_number = sid, content, page
        self.sheet_name = self.cell_range = None

    def citation(self):
        return f"(nguồn {self.source_id}, trang {self.page_number})"


class _Decision:
    backend = "cloud"


def _ident():
    return Identity(employee_id=uuid.uuid4(), department_ids=[uuid.uuid4()],
                    permissions=frozenset({"doc:read"}))


def _run(monkeypatch, chunks, answer, *, money_facts=None, question="Nhập phiếu chi thế nào?"):
    async def _fake_retrieve(*a, **kw):
        return chunks

    async def _fake_chat(messages, **kw):
        return answer, _Decision()

    monkeypatch.setattr("app.rag.grounded_answer.retriever.retrieve", _fake_retrieve)
    monkeypatch.setattr("app.rag.grounded_answer.llm.chat", _fake_chat)
    return asyncio.run(answer_guarded(None, _ident(), question, money_facts=money_facts))


def test_integrity_ok_when_numbers_from_engine_facts(monkeypatch):
    out = _run(monkeypatch, [_Chunk("s", "Vào Phiếu chi, nhập ngày.", page=8)],
               "Nợ 6427: 54,500,000; VAT 5,450,000; Có 331: 59,950,000 [1].",
               money_facts="tiền hàng 54,500,000; thuế 5,450,000; tổng 59,950,000")
    assert out["grounded"] is True
    assert out["integrity"]["ok"] is True
    assert out["integrity"]["ungrounded_numbers"] == []


def test_integrity_flags_selfcomputed_number(monkeypatch):
    # No engine facts; model invents a pre-tax figure -> gate flags it.
    out = _run(monkeypatch, [_Chunk("s", "Vào Phiếu chi.", page=8)],
               "Tiền trước thuế 49,050,000, tổng 54,500,000 [1].",
               question="số tiền 54,500,000 chịu thuế 10%")
    assert out["integrity"]["ok"] is False
    assert 49_050_000 in out["integrity"]["ungrounded_numbers"]


def test_strips_leaked_marker(monkeypatch):
    out = _run(monkeypatch, [_Chunk("s", "Vào Phiếu chi.", page=8)],
               "Số tiền 54,500,000 [SỐ LIỆU ĐÃ ĐƯỢC MONEY-ENGINE TÍNH] [1].",
               money_facts="tiền hàng 54,500,000")
    assert "MONEY-ENGINE" not in out["answer"]


def test_abstains_with_no_context_and_no_facts(monkeypatch):
    out = _run(monkeypatch, [], "bất kỳ")
    assert out["grounded"] is False
    assert out["answer"] == ABSTAIN
