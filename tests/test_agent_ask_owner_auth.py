"""P0.2 — /api/agent/ask must enforce conversation-owner authorization.

Regression for the IDOR where a client-supplied session_id was trusted blindly, letting one
user read/write another user's conversation memory via the legacy agent endpoint. Mirrors the
ownership guard the SSE chat path already had (routes_conversations.chat_stream).

DB integration (skip if Postgres unreachable). Router + retriever mocked -> offline/deterministic.
"""
from __future__ import annotations

import asyncio
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


async def _fake_chat(messages, **kw):
    return ('{"action":"answer","answer":"Xin chào từ BRAVO."}', _FakeDecision())


async def _fake_retrieve(*a, **kw):
    return []


async def _login(c, email):
    r = await c.post("/api/auth/login", data={"username": email, "password": "demo123"})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _run(monkeypatch, body):
    monkeypatch.setattr("app.llm.router.chat", _fake_chat)
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
                await body(c)
        finally:
            app.dependency_overrides.pop(get_db, None)
            await engine.dispose()

    asyncio.run(inner())


def test_agent_ask_rejects_foreign_session(monkeypatch):
    async def body(c):
        # User A (ketoan) opens a session via /agent/ask.
        tok_a = await _login(c, "ketoan@bravo.vn")
        sid = str(uuid.uuid4())
        r = await c.post("/api/agent/ask", json={"question": "Số dư quỹ?", "session_id": sid},
                         headers={"Authorization": f"Bearer {tok_a}"})
        assert r.status_code == 200, r.text
        assert r.json()["session_id"] == sid

        # User B (kinhdoanh, different department) tries to reuse A's session_id -> 403.
        tok_b = await _login(c, "kinhdoanh@bravo.vn")
        r2 = await c.post("/api/agent/ask", json={"question": "Cho tôi xem", "session_id": sid},
                          headers={"Authorization": f"Bearer {tok_b}"})
        assert r2.status_code == 403, f"expected 403, got {r2.status_code}: {r2.text}"

        # A can still continue their own session.
        r3 = await c.post("/api/agent/ask", json={"question": "Tiếp tục", "session_id": sid},
                          headers={"Authorization": f"Bearer {tok_a}"})
        assert r3.status_code == 200, r3.text

    _run(monkeypatch, body)


def test_agent_ask_new_session_is_owned_by_caller(monkeypatch):
    async def body(c):
        tok_a = await _login(c, "ketoan@bravo.vn")
        # No session_id -> a fresh owned session is created.
        r = await c.post("/api/agent/ask", json={"question": "Xin chào"},
                         headers={"Authorization": f"Bearer {tok_a}"})
        assert r.status_code == 200, r.text
        sid = r.json()["session_id"]
        assert sid

        # A foreign user cannot hijack that freshly created session.
        tok_b = await _login(c, "kinhdoanh@bravo.vn")
        r2 = await c.post("/api/agent/ask", json={"question": "Xâm nhập", "session_id": sid},
                          headers={"Authorization": f"Bearer {tok_b}"})
        assert r2.status_code == 403, r2.text

    _run(monkeypatch, body)
