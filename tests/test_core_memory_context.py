"""Regression: core-memory (persona + luồng nghiệp vụ) PHẢI được PIN vào prompt mỗi lượt.

Bug gốc: bravo bê table MemoryBlock từ letta nhưng KHÔNG render block vào prompt và KHÔNG seed
persona/nghiệp vụ -> agent 'thiếu context' giữa các lượt. Test này khoá lại 2 mắt xích đó.

  * Layer 1 (no DB): _default_core_blocks/_render_business_flows sinh nội dung THẬT từ playbooks.
  * Layer 2 (DB): seed idempotent, render loại nhãn nội bộ, và _prepare_turn CHÈN core vào messages.
"""
from __future__ import annotations

import asyncio
import uuid

import pytest

from app.agent import loop as agent_loop
from app.agent.loop import _default_core_blocks, _render_business_flows
from app.security.rls import Identity


def _db_available() -> bool:
    import asyncpg

    async def check() -> bool:
        try:
            conn = await asyncpg.connect("postgresql://bravo:bravo@localhost:5432/bravo")
            await conn.close()
            return True
        except Exception:
            return False

    return asyncio.run(check())


# --------------------------------------------------------------------------- #
# Layer 1 — nội dung core-memory mặc định (không cần DB)                        #
# --------------------------------------------------------------------------- #
def test_default_core_blocks_have_persona_and_flows():
    blocks = _default_core_blocks()
    assert "persona" in blocks and "BRAVO AI Copilot" in blocks["persona"]
    # persona mã hoá bất biến nghiệp vụ (chứng từ trước, hạch toán sau)
    assert "chứng từ" in blocks["persona"].lower()
    assert "business_flows" in blocks


def test_business_flows_render_from_playbooks():
    flows = _render_business_flows()
    # playbooks THẬT có -> phải liệt kê mode nghiệp vụ; nếu file lỗi -> '' (không được ném)
    if flows:
        assert "luồng nghiệp vụ" in flows.lower()


# --------------------------------------------------------------------------- #
# Layer 2 — DB: seed + render + wiring vào prompt                              #
# --------------------------------------------------------------------------- #
pytestmark = pytest.mark.skipif(not _db_available(), reason="Postgres not reachable")


def _engine_factory():
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
    from sqlalchemy.pool import NullPool

    from app.config import get_settings
    engine = create_async_engine(get_settings().database_url, poolclass=NullPool)
    return engine, async_sessionmaker(engine, expire_on_commit=False)


def test_seed_render_idempotent_and_excludes_internal_labels():
    async def run() -> None:
        from sqlalchemy import delete
        from app.agent.memory import MemoryStore
        from app.database.models import MemoryBlock

        engine, factory = _engine_factory()
        sid = uuid.uuid4()
        ident = Identity(employee_id=uuid.uuid4(), department_ids=[uuid.uuid4()],
                         permissions=frozenset({"doc:read"}))
        try:
            async with factory() as db:
                mem = MemoryStore(db, sid, ident)
                await mem.seed_core_defaults(_default_core_blocks())
                await mem.seed_core_defaults(_default_core_blocks())  # idempotent

                blocks = await mem.core_blocks()
                labels = [b.label for b in blocks]
                assert labels.count("persona") == 1        # KHÔNG nhân đôi khi seed lại
                assert "persona" in labels

                # nhãn nội bộ (nén history) KHÔNG lọt vào core render
                await mem.core_replace("summary", "tóm tắt cũ")
                rendered = await mem.render_core_blocks()
                assert "BRAVO AI Copilot" in rendered
                assert "tóm tắt cũ" not in rendered
                assert "summary" not in rendered
        finally:
            async with factory() as db:
                await db.execute(delete(MemoryBlock).where(MemoryBlock.session_id == sid))
                await db.commit()
            await engine.dispose()

    asyncio.run(run())


def test_prepare_turn_injects_core_memory_into_messages(monkeypatch):
    """Mắt xích quan trọng nhất: messages do _prepare_turn dựng PHẢI chứa core-memory."""
    async def run() -> None:
        from sqlalchemy import delete
        from app.database.models import ConversationMessage, MemoryBlock
        from app.rag import retriever

        # Stub retrieval -> khỏi gọi embedding/mạng; ta chỉ kiểm tra wiring core-memory.
        async def _no_chunks(*a, **k):
            return []
        monkeypatch.setattr(retriever, "retrieve", _no_chunks)

        engine, factory = _engine_factory()
        sid = uuid.uuid4()
        ident = Identity(employee_id=uuid.uuid4(), department_ids=[uuid.uuid4()],
                         permissions=frozenset({"doc:read"}))
        try:
            async with factory() as db:
                sess = agent_loop.AgentSession(db, ident, session_id=sid)
                messages, _chunks, _cites = await sess._prepare_turn("Cách tạo phiếu nhập mua?")
                sys_text = "\n".join(m["content"] for m in messages if m["role"] == "system")
                assert "BỘ NHỚ LÕI" in sys_text          # khối core được pin
                assert "BRAVO AI Copilot" in sys_text     # persona hiện diện
        finally:
            async with factory() as db:
                await db.execute(delete(MemoryBlock).where(MemoryBlock.session_id == sid))
                await db.execute(
                    delete(ConversationMessage).where(ConversationMessage.session_id == sid))
                await db.commit()
            await engine.dispose()

    asyncio.run(run())


def test_history_watermark_summarizes_once_and_keeps_recent():
    """S3: lượt cũ được tóm tắt DẦN theo watermark — không re-summarize khi không có lượt mới,
    không amnesia, tóm tắt nạp ở role user-data (S4)."""
    async def run() -> None:
        from sqlalchemy import delete
        from app.agent.memory import MemoryStore
        from app.database.models import ConversationMessage, MemoryBlock

        engine, factory = _engine_factory()
        sid = uuid.uuid4()
        ident = Identity(employee_id=uuid.uuid4(), department_ids=[uuid.uuid4()],
                         permissions=frozenset({"doc:read"}))
        calls = {"n": 0}

        async def summarize_fn(text: str, prev: str) -> str:
            calls["n"] += 1
            return (prev or "") + " | " + f"tóm tắt {len(text)} ký tự"

        try:
            async with factory() as db:
                mem = MemoryStore(db, sid, ident)
                for i in range(14):
                    await mem.recall_add("user" if i % 2 == 0 else "assistant",
                                         f"Lượt hội thoại số {i} với nội dung dài vừa đủ.")
                # keep_recent=4, max_tokens=5 -> buộc nén phần cũ (10 lượt).
                out = await mem.history_for_prompt(summarize_fn, keep_recent=4, max_tokens=5)
                assert calls["n"] == 1                       # tóm tắt đúng MỘT lần
                assert out and out[0]["role"] == "user"       # S4: summary ở role user-data
                assert "TÓM TẮT" in out[0]["content"]
                assert len(out) == 1 + 4                       # summary head + 4 recent
                assert "số 13" in out[-1]["content"]          # lượt mới nhất giữ nguyên văn

                # Gọi lại KHÔNG có lượt mới -> KHÔNG tóm tắt lại (watermark không đổi).
                await mem.history_for_prompt(summarize_fn, keep_recent=4, max_tokens=5)
                assert calls["n"] == 1

                # Thêm 2 lượt mới -> chỉ phần MỚI trượt ra được tóm tắt (1 lần nữa).
                for i in range(14, 16):
                    await mem.recall_add("user", f"Lượt mới số {i} nội dung bổ sung.")
                await mem.history_for_prompt(summarize_fn, keep_recent=4, max_tokens=5)
                assert calls["n"] == 2
        finally:
            async with factory() as db:
                await db.execute(delete(MemoryBlock).where(MemoryBlock.session_id == sid))
                await db.execute(
                    delete(ConversationMessage).where(ConversationMessage.session_id == sid))
                await db.commit()
            await engine.dispose()

    asyncio.run(run())
