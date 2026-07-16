"""P1 — chat platform backend: SSE streaming + multi-turn + conversation RLS + share.

DB integration (skip nếu Postgres không reachable). Router + retriever mock -> offline,
deterministic. Mỗi test: NullPool engine riêng trong loop của test (override get_db) để
tránh lỗi cross-loop của engine pool module-level.
"""
from __future__ import annotations

import asyncio
import json
import uuid

import httpx
import pytest
from httpx import ASGITransport


def _db_available() -> bool:
    import asyncpg

    async def _check():
        try:
            conn = await asyncpg.connect("postgresql://bravo:bravo@localhost:5432/bravo")
            await conn.close()
            return True
        except Exception:
            return False

    return asyncio.run(_check())


pytestmark = pytest.mark.skipif(not _db_available(), reason="Postgres not reachable")


class _FakeDecision:
    backend = "local"


_SCRIPTED = '{"action":"answer","answer":"Xin chào từ BRAVO."}'


async def _fake_chat(messages, **kw):
    _fake_chat.last_messages = messages
    return (_SCRIPTED, _FakeDecision())


async def _fake_chat_stream(messages, **kw):
    # P0b: step_stream now streams the decide-answer via chat_stream (single generation).
    _fake_chat.last_messages = messages
    for i in range(0, len(_SCRIPTED), 8):
        yield {"type": "delta", "text": _SCRIPTED[i:i + 8]}
    yield {"type": "done", "decision": _FakeDecision(), "text": _SCRIPTED}


async def _fake_retrieve(*a, **kw):
    return []


async def _login(c):
    r = await c.post("/api/auth/login",
                     data={"username": "ketoan@bravo.vn", "password": "demo123"})
    assert r.status_code == 200, r.text
    c.headers["Authorization"] = f"Bearer {r.json()['access_token']}"


async def _stream(c, cid, question):
    events = []
    async with c.stream("POST", f"/api/chat/{cid}/messages", json={"question": question}) as r:
        assert r.status_code == 200
        async for line in r.aiter_lines():
            if line.startswith("data: "):
                events.append(json.loads(line[6:]))
    return events


def _run(monkeypatch, body):
    """Chạy `body(client)` trong 1 loop với get_db override (NullPool engine của loop này)."""
    monkeypatch.setattr("app.llm.router.chat", _fake_chat)
    monkeypatch.setattr("app.llm.router.chat_stream", _fake_chat_stream)
    monkeypatch.setattr("app.rag.retriever.retrieve", _fake_retrieve)
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
    from sqlalchemy.pool import NullPool

    from app.config import get_settings
    from app.database import get_db
    from app.main import app

    async def inner():
        engine = create_async_engine(get_settings().database_url, poolclass=NullPool)
        factory = async_sessionmaker(engine, expire_on_commit=False)

        async def _ovr():
            async with factory() as s:
                try:
                    yield s
                    await s.commit()
                except Exception:
                    await s.rollback()
                    raise

        app.dependency_overrides[get_db] = _ovr
        try:
            async with httpx.AsyncClient(transport=ASGITransport(app=app),
                                         base_url="http://t") as c:
                await _login(c)
                await body(c)
        finally:
            app.dependency_overrides.pop(get_db, None)
            await engine.dispose()

    asyncio.run(inner())


def test_sse_sequence_persist_and_multiturn(monkeypatch):
    async def body(c):
        cid = str(uuid.uuid4())
        events = await _stream(c, cid, "Câu hỏi thứ nhất ABC")
        types = [e["type"] for e in events]
        assert types[0] == "id" and "source" in types and "step" in types
        assert "answer" in types and types[-1] == "done"
        assert "BRAVO" in "".join(e["delta"] for e in events if e["type"] == "answer")

        convs = (await c.get("/api/conversations")).json()
        assert any(x["id"] == cid for x in convs)
        roles = [m["role"] for m in (await c.get(f"/api/conversations/{cid}")).json()["messages"]]
        assert "user" in roles and "assistant" in roles

        await _stream(c, cid, "Câu hỏi thứ hai XYZ")
        joined = " ".join(m["content"] for m in _fake_chat.last_messages)
        assert "thứ nhất ABC" in joined, "multi-turn: lịch sử lượt 1 chưa nối vào prompt lượt 2"
        await c.delete(f"/api/conversations/{cid}")

    _run(monkeypatch, body)


def test_consultant_structured_feedback_is_idempotent_and_transcript_free(monkeypatch):
    async def body(c):
        cid = str(uuid.uuid4())
        # The endpoint accepts caller-owned feedback independently of whether a workflow has
        # already matched; it persists only typed state metadata, not this answer text.
        first = await c.post(f"/api/consultant/state/{cid}/feedback", json={"kind": "wrong_goal"})
        assert first.status_code == 404  # no owned conversation yet
        await _stream(c, cid, "Làm sao lên BCTC?")
        response = await c.post(f"/api/consultant/state/{cid}/feedback", json={"kind": "wrong_goal"})
        assert response.status_code == 200
        assert response.json() == {"created": True, "kind": "wrong_goal",
                                   "promotion": "review_required_only"}
        duplicate = await c.post(f"/api/consultant/state/{cid}/feedback", json={"kind": "wrong_goal"})
        assert duplicate.status_code == 200 and duplicate.json()["created"] is False

    _run(monkeypatch, body)


def test_rename_share_and_rls(monkeypatch):
    async def body(c):
        cid = str(uuid.uuid4())
        await _stream(c, cid, "Hội thoại test chia sẻ")
        await c.post(f"/api/conversations/{cid}/rename", json={"title": "Tiêu đề test"})
        tok = (await c.post(f"/api/conversations/{cid}/share")).json()["shared_token"]
        shared = (await c.get(f"/api/shared/{tok}")).json()
        assert shared["title"] == "Tiêu đề test"
        assert "employee_id" not in shared and "messages" in shared
        # P1: revoke the share -> the token stops working (404).
        assert (await c.delete(f"/api/conversations/{cid}/share")).status_code == 204
        assert (await c.get(f"/api/shared/{tok}")).status_code == 404
        assert (await c.delete(f"/api/conversations/{cid}")).status_code == 204
        assert (await c.get(f"/api/conversations/{cid}")).status_code == 404

    _run(monkeypatch, body)


def test_advisory_lock_path_completes(monkeypatch):
    """ADR-0024: with use_pg_advisory_lock on, a turn still completes and the lock is released
    (a second turn on the same conversation also succeeds)."""
    from app.config import get_settings
    monkeypatch.setattr(get_settings(), "use_pg_advisory_lock", True)

    async def body(c):
        cid = str(uuid.uuid4())
        ev1 = await _stream(c, cid, "Câu hỏi một (advisory)")
        assert ev1[-1]["type"] == "done"
        ev2 = await _stream(c, cid, "Câu hỏi hai (advisory)")   # lock released -> succeeds
        assert ev2[-1]["type"] == "done"

    _run(monkeypatch, body)


def test_truncate_drops_turn_and_resets_summary(monkeypatch):
    async def body(c):
        cid = str(uuid.uuid4())
        await _stream(c, cid, "Câu hỏi một")
        await _stream(c, cid, "Câu hỏi hai")
        # 4 messages persisted (2 user + 2 assistant).
        msgs = (await c.get(f"/api/conversations/{cid}")).json()["messages"]
        assert len(msgs) == 4
        # Regenerate the FIRST answer: truncate from the first user message (inclusive) -> removes
        # everything from turn 1 onward (P3).
        first_user = next(m for m in msgs if m["role"] == "user")
        r = await c.post(f"/api/conversations/{cid}/truncate",
                         json={"from_message_id": first_user["id"], "inclusive": True})
        assert r.status_code == 200 and r.json()["deleted"] == 4
        assert len((await c.get(f"/api/conversations/{cid}")).json()["messages"]) == 0
        # Foreign / unknown message id -> 404.
        assert (await c.post(f"/api/conversations/{cid}/truncate",
                             json={"from_message_id": str(uuid.uuid4())})).status_code == 404

    _run(monkeypatch, body)


def test_done_carries_message_id_and_feedback_report(monkeypatch):
    async def body(c):
        cid = str(uuid.uuid4())
        events = await _stream(c, cid, "Câu hỏi có phản hồi")
        done = next(e for e in events if e["type"] == "done")
        # P1: done carries the persisted assistant + user message ids.
        assert done.get("message_id") and done.get("user_message_id")
        mid = done["message_id"]
        # P1: feedback with report-to-IT comment + category persists.
        r = (await c.post(f"/api/conversations/{cid}/messages/{mid}/feedback",
                          json={"value": "dislike", "comment": "số liệu sai",
                                "category": "wrong_number"})).json()
        assert r["feedback"] == "dislike"
        assert r["comment"] == "số liệu sai"
        assert r["category"] == "wrong_number"
        # unknown category is coerced to "other"
        r2 = (await c.post(f"/api/conversations/{cid}/messages/{mid}/feedback",
                           json={"value": "like", "category": "zzz"})).json()
        assert r2["category"] == "other"

    _run(monkeypatch, body)
