"""Wave 1 Track A — chat_stream token thật + usage + decide-retry (W1.1/1.2/1.3)."""
from __future__ import annotations

import pytest

from app.agent import loop as loopmod
from app.llm import router


class _Delta:
    def __init__(self, content):
        self.content = content


class _Choice:
    def __init__(self, content):
        self.delta = _Delta(content)


class _Usage:
    prompt_tokens = 30
    completion_tokens = 12
    total_tokens = 42


class _Chunk:
    def __init__(self, content=None, usage=None):
        self.choices = [_Choice(content)] if content is not None else []
        self.usage = usage


class _FakeStream:
    """Async iterator mô phỏng stream OpenAI: vài delta token + chunk usage cuối."""
    def __init__(self):
        self._chunks = [_Chunk("Xin "), _Chunk("chào"), _Chunk(None, _Usage())]

    def __aiter__(self):
        return self

    async def __anext__(self):
        if not self._chunks:
            raise StopAsyncIteration
        return self._chunks.pop(0)


class _FakeClient:
    class chat:
        class completions:
            @staticmethod
            async def create(**kw):
                assert kw.get("stream") is True
                return _FakeStream()


@pytest.mark.asyncio
async def test_chat_stream_yields_real_deltas_and_usage(monkeypatch):
    # The fake client is local; assert this historical stream contract under hybrid policy.
    monkeypatch.setattr(router._settings, "egress_policy", "hybrid")
    monkeypatch.setattr(router, "_local", _FakeClient())
    deltas, done = [], None
    async for ev in router.chat_stream([{"role": "user", "content": "hi"}], db=None):
        if ev["type"] == "delta":
            deltas.append(ev["text"])
        elif ev["type"] == "done":
            done = ev
    assert deltas == ["Xin ", "chào"]
    assert done["text"] == "Xin chào"
    assert done["decision"].total_tokens == 42        # usage THẬT từ chunk cuối


@pytest.mark.asyncio
async def test_usage_tokens_prefers_real_over_estimate():
    d = router.RoutingDecision("local", "m", "r", total_tokens=99)
    assert loopmod.AgentSession._usage_tokens(d, "abcd" * 100, [{"content": "x" * 400}]) == 99
    d0 = router.RoutingDecision("local", "m", "r")   # không có usage -> ước lượng len//4
    est = loopmod.AgentSession._usage_tokens(d0, "abcd", [{"content": "x" * 400}])
    assert est == len("abcd") // 4 + 400 // 4


def test_parse_decision_strict_flags_invalid():
    ok_dec, ok = loopmod._parse_decision_strict('{"action":"answer","answer":"hi"}')
    assert ok and ok_dec.action == "answer"
    prose_dec, bad = loopmod._parse_decision_strict("đây là văn xuôi không JSON")
    assert not bad and prose_dec.action == "answer"   # graceful coerce + cờ ok=False (để retry)
