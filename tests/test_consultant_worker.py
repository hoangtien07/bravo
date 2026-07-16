from __future__ import annotations

import app.worker as worker


async def test_gap_curation_is_disabled_by_default(monkeypatch):
    monkeypatch.setattr(worker._settings, "consultant_curation_enabled", False)

    result = await worker.consultant_gap_curation_task({})

    assert result == {"status": "disabled", "created": 0}


async def test_gap_curation_creates_only_review_required_candidates(monkeypatch):
    class _SessionContext:
        async def __aenter__(self):
            return object()

        async def __aexit__(self, *_args):
            return None

    async def fake_create(_db, *, limit: int):
        assert limit == 7
        return 3

    monkeypatch.setattr(worker._settings, "consultant_curation_enabled", True)
    monkeypatch.setattr(worker._settings, "consultant_curation_max_gaps", 7)
    monkeypatch.setattr(worker, "async_session_factory", lambda: _SessionContext())
    monkeypatch.setattr("app.consultant.jobs.create_candidates_from_open_gaps", fake_create)

    result = await worker.consultant_gap_curation_task({})

    assert result == {"status": "review_required", "created": 3}


async def test_task_state_retention_is_disabled_by_default(monkeypatch):
    monkeypatch.setattr(worker._settings, "consultant_state_retention_enabled", False)

    result = await worker.consultant_state_retention_task({})

    assert result == {"status": "disabled", "deleted": 0}


async def test_task_state_retention_purges_only_policy_scoped_blocks(monkeypatch):
    class _Result:
        rowcount = 2

    class _Session:
        committed = False
        statement = None

        async def execute(self, statement):
            self.statement = statement
            return _Result()

        async def commit(self):
            self.committed = True

    class _SessionContext:
        def __init__(self):
            self.session = _Session()

        async def __aenter__(self):
            return self.session

        async def __aexit__(self, *_args):
            return None

    context = _SessionContext()
    monkeypatch.setattr(worker._settings, "consultant_state_retention_enabled", True)
    monkeypatch.setattr(worker._settings, "consultant_state_retention_days", 30)
    monkeypatch.setattr(worker, "async_session_factory", lambda: context)

    result = await worker.consultant_state_retention_task({})

    assert result == {"status": "purged_task_state_only", "deleted": 2}
    assert context.session.committed is True
    compiled = str(context.session.statement.compile(compile_kwargs={"literal_binds": True}))
    assert "consultant_task_state/v1" in compiled
    assert "memory_blocks" in compiled
