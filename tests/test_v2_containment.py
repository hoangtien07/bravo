from __future__ import annotations

import uuid
from types import SimpleNamespace

import pytest
from sqlalchemy.exc import IntegrityError

from app.agent.conversations import ensure_conversation
from app.agent.loop import AgentSession
from app.consultant.service import ConsultantService, ConsultantStateCorruptError
from app.security.rls import Identity


def _identity() -> Identity:
    return Identity(employee_id=uuid.uuid4(), department_ids=[], permissions=frozenset())


class _ScalarResult:
    def __init__(self, value):
        self.value = value

    def scalar_one_or_none(self):
        return self.value


@pytest.mark.asyncio
async def test_conversation_owner_lookup_is_scoped_in_sql_before_insert():
    class DB:
        def __init__(self):
            self.statements = []
            self.commits = 0

        async def execute(self, statement):
            self.statements.append(statement)
            return _ScalarResult(None)

        def add(self, _row):
            pass

        async def commit(self):
            self.commits += 1
            raise IntegrityError("insert", {}, Exception("duplicate conversation id"))

        async def rollback(self):
            pass

    db = DB()
    with pytest.raises(PermissionError):
        await ensure_conversation(db, uuid.uuid4(), uuid.uuid4(), first_question="x")

    sql = str(db.statements[0].compile(compile_kwargs={"literal_binds": True}))
    assert "conversations.employee_id" in sql
    assert len(db.statements) == 2  # the post-conflict lookup is scoped as well


@pytest.mark.asyncio
async def test_corrupt_consultant_state_fails_closed_and_rolls_back():
    class DB:
        rolled_back = False

        async def execute(self, _statement):
            return _ScalarResult(SimpleNamespace(value="not-json"))

        async def rollback(self):
            self.rolled_back = True

    db = DB()
    service = ConsultantService(db, _identity(), uuid.uuid4())
    with pytest.raises(ConsultantStateCorruptError):
        await service.load_state()
    assert db.rolled_back is True


@pytest.mark.asyncio
async def test_sse_answer_is_emitted_only_after_shared_consultant_guard(monkeypatch):
    class DB:
        def add(self, _row):
            pass

        async def commit(self):
            pass

    session = AgentSession(DB(), _identity())
    session._consultant_turn = SimpleNamespace(
        frame=SimpleNamespace(goal_type="financial_statements_ready", risk="U1"),
        state=SimpleNamespace(current_node="closing_complete"),
    )
    session._consultant_trace = {}
    session._routed_cloud = False
    session._created_draft = False

    async def no_recall(_role, _content):
        return None

    async def no_close(_status):
        return None

    monkeypatch.setattr(session, "_safe_recall_add", no_recall)
    monkeypatch.setattr(session, "_close_run", no_close)
    monkeypatch.setattr("app.agent.loop._settings.stream_compose_answer", False)

    events = [event async for event in session._stream_answer(
        "Bạn mở báo cáo tài chính để in.", [], [], ["nguồn đã scope"])]
    answers = [event["delta"] for event in events if event["type"] == "answer"]

    assert len(answers) == 1
    assert answers[0].startswith("Lưu ý: trước khi mở/lập báo cáo")
    assert events[-1]["type"] == "done"
    assert session._consultant_trace["critic_tags"] == ["prerequisite_guard"]
