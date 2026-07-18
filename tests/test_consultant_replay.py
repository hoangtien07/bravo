import asyncio
import json

from app.api.routes_conversations import ChatIn
from app.eval.consultant_replay import _stream_answer


def test_chat_contract_accepts_consultant_ab_override():
    assert ChatIn(question="x", consultant_mode="off").consultant_mode == "off"
    assert ChatIn(question="x", consultant_mode="on").consultant_mode == "on"
    assert ChatIn(question="x", consultant_profile="implementation").consultant_profile == "implementation"


class _FakeStream:
    """Mimic httpx client.stream() -> async ctx manager exposing status_code + aiter_lines."""

    def __init__(self, events):
        self._lines = ["data: " + json.dumps(e, ensure_ascii=False) for e in events]
        self.status_code = 200

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    async def aiter_lines(self):
        for line in self._lines:
            yield line


class _FakeClient:
    def __init__(self, events):
        self._events = events

    def stream(self, *a, **kw):
        return _FakeStream(self._events)


def test_persist_answers_captures_text_and_citations():
    """P1.1: capture mode reconstructs the answer + grounded/citations from the SSE stream."""
    events = [
        {"type": "id", "conversation_id": "c"},
        {"type": "answer", "delta": "Bạn cần "},
        {"type": "answer", "delta": "hoàn tất khóa sổ."},
        {"type": "done", "grounded": True, "citations": ["nguồn A trang 3"]},
    ]
    captured = asyncio.run(_stream_answer(
        _FakeClient(events), "http://t", {}, "conv-1", "Lên BCTC?", "on"))
    assert captured["answer"] == "Bạn cần hoàn tất khóa sổ."
    assert captured["grounded"] is True
    assert captured["citations"] == ["nguồn A trang 3"]
    assert captured["http_status"] == 200
