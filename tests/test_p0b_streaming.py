"""P0b — single-generation decide-answer streaming.

Guards the invariants that made the OLD compose path unsafe:
  - C1: NO second generation -> exactly one chat_stream call per knowledge turn, no double-emit.
  - F3: world-knowledge numbers + abstain tails are held back until the post-gen guard runs,
        so nothing unguarded reaches the client mid-stream.
  - M2: service (infra) errors are classified apart from genuine ambiguity.
Financial turns (engine values present) must NOT stream (invariant #3 verify-gate).
"""
from __future__ import annotations

import json
import uuid

import pytest

from app.agent import loop as agent_loop
from app.agent.loop import (
    AgentSession,
    _AnswerStreamer,
    _is_service_error,
    _WK_LABEL,
    _ABSTAIN_PREFIX,
)
from app.security.rls import Identity


# --------------------------------------------------------------------------------------
# Fakes
# --------------------------------------------------------------------------------------
class _FakeDB:
    def add(self, obj): ...
    async def commit(self): ...
    async def refresh(self, obj): ...


def _identity():
    return Identity(employee_id=uuid.uuid4(), department_ids=[],
                    permissions=frozenset(), is_admin=False)


def _chunks(s: str, n: int = 4):
    for i in range(0, len(s), n):
        yield s[i:i + n]


def _mock_chat_stream(monkeypatch, full_json: str, *, backend="cloud", tokens=42):
    """Patch router.chat_stream to stream `full_json` in small deltas. Returns a call counter."""
    calls = {"n": 0}

    async def fake(messages, **kw):
        calls["n"] += 1
        for piece in _chunks(full_json):
            yield {"type": "delta", "text": piece}
        from app.llm.router import RoutingDecision
        d = RoutingDecision(backend, "gpt-4o", "test")
        d.total_tokens = tokens
        yield {"type": "done", "decision": d, "text": full_json}

    monkeypatch.setattr(agent_loop.llm, "chat_stream", fake)
    return calls


async def _drive_decide(sess, *, allow_stream):
    deltas, decision, streamer = [], None, None
    async for ev in sess._decide_streaming([{"role": "user", "content": "x"}], [],
                                           allow_stream=allow_stream):
        if ev["type"] == "__decision__":
            decision, streamer = ev["decision"], ev["streamer"]
        else:
            deltas.append(ev["delta"])
    return deltas, decision, streamer


# --------------------------------------------------------------------------------------
# _AnswerStreamer (pure)
# --------------------------------------------------------------------------------------
def test_streamer_normal_answer_streams_with_taildback_then_finalizes():
    s = _AnswerStreamer()
    full = "Bước 1 làm A [1]. Bước 2 làm B [2]."
    out = ""
    for i in range(1, len(full) + 1):
        out += s.update(full[:i])
    out += s.finalize()
    assert out == full  # exactly the answer, nothing dropped or duplicated


def test_streamer_holds_back_world_knowledge_numbers_until_guard():
    s = _AnswerStreamer()
    money = "5.000.000đ"
    full = ("Theo tài liệu [1], quy trình gồm 2 bước.\n\n"
            + _WK_LABEL + "\nThông thường số dư khoảng " + money + " tùy doanh nghiệp.")
    streamed = ""
    for i in range(1, len(full) + 1):
        streamed += s.update(full[:i])
    # Mid-stream: the raw money figure is NEVER emitted (held back with the WK block).
    assert money not in streamed
    final = streamed + s.finalize()
    # After finalize the WK block is present but the number is redacted (guard ran).
    assert _WK_LABEL in final
    assert money not in final
    assert "đã ẩn" in final


def test_streamer_abstain_opener_streams_nothing_then_canonical():
    s = _AnswerStreamer()
    full = _ABSTAIN_PREFIX.capitalize() + ". Nhưng bạn có thể thử vào menu X rồi bấm Y."
    streamed = ""
    for i in range(1, len(full) + 1):
        streamed += s.update(full[:i])
    assert streamed == ""  # fabricated tail never streamed
    final = s.finalize()
    assert final.lower().startswith(_ABSTAIN_PREFIX)
    assert "menu X" not in final  # tail clipped (fail-closed)


# --------------------------------------------------------------------------------------
# _decide_streaming (single generation)
# --------------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_knowledge_answer_streams_single_generation(monkeypatch):
    full = json.dumps({"action": "answer", "answer": "Bước 1 làm A [1]. Bước 2 làm B."},
                      ensure_ascii=False)
    calls = _mock_chat_stream(monkeypatch, full)
    sess = AgentSession(_FakeDB(), _identity())
    sess._routed_cloud = False
    deltas, decision, streamer = await _drive_decide(sess, allow_stream=True)
    assert calls["n"] == 1                      # C1: exactly ONE generation, no compose
    assert decision.action == "answer"
    assert streamer is not None                 # streamed path
    live = "".join(deltas)
    assert live                                 # tokens streamed live during the single gen
    answer = "Bước 1 làm A [1]. Bước 2 làm B."
    assert answer.startswith(live)              # streamed text is a true prefix (tail-held)
    assert streamer.full == answer              # finalize will flush the remainder
    assert sess._routed_cloud is True           # cloud backend threaded through


@pytest.mark.asyncio
async def test_financial_turn_is_not_streamed(monkeypatch):
    full = json.dumps({"action": "answer", "answer": "Doanh thu là 1000 triệu [1]."},
                      ensure_ascii=False)
    _mock_chat_stream(monkeypatch, full)
    sess = AgentSession(_FakeDB(), _identity())
    sess._routed_cloud = False
    deltas, decision, streamer = await _drive_decide(sess, allow_stream=False)
    assert streamer is None                     # buffered for verify-gate (invariant #3)
    assert deltas == []                          # no tokens leaked before the gate
    assert decision.action == "answer"
    assert decision.answer and "1000" in decision.answer


@pytest.mark.asyncio
async def test_tool_decision_buffers_no_answer_deltas(monkeypatch):
    full = json.dumps({"action": "tool", "tool": "kb_search", "args": {"q": "nghỉ phép"}},
                      ensure_ascii=False)
    _mock_chat_stream(monkeypatch, full)
    sess = AgentSession(_FakeDB(), _identity())
    sess._routed_cloud = False
    deltas, decision, streamer = await _drive_decide(sess, allow_stream=True)
    assert streamer is None
    assert deltas == []
    assert decision.action == "tool"
    assert decision.tool == "kb_search"
    assert decision.args == {"q": "nghỉ phép"}


# --------------------------------------------------------------------------------------
# M2 service-error classifier
# --------------------------------------------------------------------------------------
@pytest.mark.parametrize("exc,expected", [
    (Exception("Rate limit reached for gpt-4o"), True),
    (Exception("Request timed out"), True),
    (Exception("context_length_exceeded: maximum context"), True),
    (TimeoutError("x"), True),
    (ValueError("thiếu tham số bắt buộc"), False),
    (Exception("random parse ambiguity"), False),
])
def test_is_service_error(exc, expected):
    assert _is_service_error(exc) is expected


# --------------------------------------------------------------------------------------
# RC-BE1 vision routing guard
# --------------------------------------------------------------------------------------
def _img_messages():
    return [{"role": "user", "content": [
        {"type": "text", "text": "ảnh này là gì"},
        {"type": "image_url", "image_url": {"url": "data:image/png;base64,AAA"}}]}]


def test_vision_guard_raises_for_textonly_slot(monkeypatch):
    from app.llm import router
    monkeypatch.setattr(router._settings, "llm_local_vision", False)
    d = router.RoutingDecision("local", "qwen", "test")
    with pytest.raises(router.VisionUnsupportedError):
        router._guard_vision(d, _img_messages())


def test_vision_guard_ok_for_vision_slot(monkeypatch):
    from app.llm import router
    monkeypatch.setattr(router._settings, "cloud_vision", True)
    d = router.RoutingDecision("cloud", "gpt-4o", "test")
    router._guard_vision(d, _img_messages())          # no raise


def test_vision_guard_noop_without_image():
    from app.llm import router
    d = router.RoutingDecision("local", "qwen", "test")
    router._guard_vision(d, [{"role": "user", "content": "chỉ có chữ"}])   # no raise
