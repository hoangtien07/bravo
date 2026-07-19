"""D2 — GET /api/admin/feedback surfaces flagged chat answers for the dogfood triage loop."""
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


class _Dec:
    backend = "local"


async def _fake_chat_stream(messages, **kw):
    scripted = '{"action":"answer","answer":"Câu trả lời cần cải thiện."}'
    for i in range(0, len(scripted), 8):
        yield {"type": "delta", "text": scripted[i:i + 8]}
    yield {"type": "done", "decision": _Dec(), "text": scripted}


async def _fake_retrieve(*a, **kw):
    return []


def _run(monkeypatch, body):
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
                await body(c)
        finally:
            app.dependency_overrides.pop(get_db, None)
            await engine.dispose()

    asyncio.run(inner())


async def _login(c, email):
    r = await c.post("/api/auth/login", data={"username": email, "password": "demo123"})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def test_admin_sees_disliked_answer(monkeypatch):
    async def body(c):
        # A normal user asks a question, gets an answer, and dislikes it.
        tok = await _login(c, "ketoan@bravo.vn")
        h = {"Authorization": f"Bearer {tok}"}
        cid = str(uuid.uuid4())
        marker = f"marker-{cid[:8]}"
        async with c.stream("POST", f"/api/chat/{cid}/messages",
                            json={"question": f"Câu hỏi {marker}"}, headers=h) as r:
            assert r.status_code == 200
            mids = []
            async for line in r.aiter_lines():
                if line.startswith("data: "):
                    ev = json.loads(line[6:])
                    if ev.get("type") == "done" and ev.get("message_id"):
                        mids.append(ev["message_id"])
        msgs = (await c.get(f"/api/conversations/{cid}", headers=h)).json()["messages"]
        amid = [m["id"] for m in msgs if m["role"] == "assistant"][-1]
        r = await c.post(f"/api/conversations/{cid}/messages/{amid}/feedback",
                         json={"value": "dislike", "comment": "thiếu bước", "category": "unhelpful"},
                         headers=h)
        assert r.status_code == 200, r.text

        # Admin sees it in the feedback view.
        atok = await _login(c, "giamdoc@bravo.vn")
        rows = (await c.get("/api/admin/feedback?only_disliked=true&limit=200",
                            headers={"Authorization": f"Bearer {atok}"})).json()
        hit = [row for row in rows if marker in (row["question"] or "")]
        assert hit, "disliked answer must appear in admin feedback view"
        assert hit[0]["category"] == "unhelpful" and hit[0]["comment"] == "thiếu bước"

        # Non-admin is refused.
        r = await c.get("/api/admin/feedback", headers=h)
        assert r.status_code in (401, 403)

        await c.delete(f"/api/conversations/{cid}", headers=h)

    _run(monkeypatch, body)
