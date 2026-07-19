"""P1.3 — the C0 'bare model + evidence' arm: retrieve -> one LLM call -> cite, no architecture.

Pure-unit (retriever + router mocked). Verifies C0 grounds on retrieved context, cites, and
fails closed (abstain) with no context — the floor the V2 stop-rule compares against.
"""
from __future__ import annotations

import asyncio
import uuid

from app.eval.c0_arm import C0Arm
from app.rag.grounded_answer import ABSTAIN
from app.security.rls import Identity


class _Chunk:
    def __init__(self, sid, content, page=None):
        self.source_id = sid
        self.content = content
        self.page_number = page
        self.sheet_name = None
        self.cell_range = None

    def citation(self):
        return f"(nguồn {self.source_id}, trang {self.page_number})"


class _Decision:
    backend = "local"


def _ident():
    return Identity(employee_id=uuid.uuid4(), department_ids=[uuid.uuid4()],
                    permissions=frozenset({"doc:read"}))


def _run(monkeypatch, chunks, answer):
    async def _fake_retrieve(*a, **kw):
        return chunks

    async def _fake_chat(messages, **kw):
        return answer, _Decision()

    monkeypatch.setattr("app.rag.grounded_answer.retriever.retrieve", _fake_retrieve)
    monkeypatch.setattr("app.rag.grounded_answer.llm.chat", _fake_chat)
    arm = C0Arm(db=None, identity=_ident())
    return asyncio.run(arm.step("Làm sao lên BCTC?"))


def test_c0_grounds_and_cites(monkeypatch):
    sid = str(uuid.uuid4())
    out = _run(monkeypatch, [_Chunk(sid, "Khóa sổ trước khi lên báo cáo.", page=3)],
               "Bạn cần hoàn tất khóa sổ trước [1].")
    assert out["grounded"] is True
    assert out["citations"] and sid in out["citations"][0] and "trang 3" in out["citations"][0]


def test_c0_abstains_without_context(monkeypatch):
    out = _run(monkeypatch, [], "bất kỳ")
    assert out["grounded"] is False
    assert out["answer"] == ABSTAIN
    assert out["citations"] == []


def test_c0_cuts_tail_after_abstain_prefix(monkeypatch):
    out = _run(monkeypatch, [_Chunk("s", "nội dung", page=1)],
               ABSTAIN + " Nhưng đây là bịa thêm không nguồn.")
    assert out["grounded"] is False
    assert out["answer"] == ABSTAIN
