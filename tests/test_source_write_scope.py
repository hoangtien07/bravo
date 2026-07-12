"""REM-SCOPE-01 — source-write authority and retrieval-isolation coverage."""
from __future__ import annotations

import asyncio
from io import BytesIO
import uuid

import pytest

from app.security.rls import Identity, resolve_source_write_scope


DEPT_A = uuid.uuid4()
DEPT_B = uuid.uuid4()


def _identity(*, departments=(), permissions=(), admin=False) -> Identity:
    return Identity(
        employee_id=uuid.uuid4(),
        department_ids=list(departments),
        permissions=frozenset(permissions),
        is_admin=admin,
    )


def test_own_department_creator_can_request_own_department():
    writer = _identity(
        departments=[DEPT_A], permissions={"doc:create:own_dept"},
    )
    assert resolve_source_write_scope(writer, [DEPT_A], shared=False) == [DEPT_A]


@pytest.mark.parametrize("requested", [[], []])
def test_single_department_creator_omitted_or_empty_scope_resolves_to_authoritative_department(requested):
    writer = _identity(
        departments=[DEPT_A], permissions={"doc:create:own_dept"},
    )
    assert resolve_source_write_scope(writer, requested, shared=False) == [DEPT_A]


def test_own_department_creator_cannot_request_foreign_or_mixed_scope():
    writer = _identity(
        departments=[DEPT_A], permissions={"doc:create:own_dept"},
    )
    with pytest.raises(PermissionError):
        resolve_source_write_scope(writer, [DEPT_B], shared=False)
    with pytest.raises(PermissionError):
        resolve_source_write_scope(writer, [DEPT_A, DEPT_B], shared=False)


def test_multi_department_creator_may_request_only_authorized_departments():
    writer = _identity(
        departments=[DEPT_A, DEPT_B], permissions={"doc:create:own_dept"},
    )
    assert resolve_source_write_scope(writer, [DEPT_A, DEPT_B], shared=False) == [DEPT_A, DEPT_B]


def test_own_department_creator_cannot_publish_shared_source():
    writer = _identity(
        departments=[DEPT_A], permissions={"doc:create:own_dept"},
    )
    with pytest.raises(PermissionError):
        resolve_source_write_scope(writer, [], shared=True)


def test_shared_source_requires_explicit_all_scope_permission_and_explicit_flag():
    publisher = _identity(permissions={"doc:create:all"})
    assert resolve_source_write_scope(publisher, [], shared=True) == []
    with pytest.raises(ValueError):
        resolve_source_write_scope(publisher, [], shared=False)

    admin_without_publication_permission = _identity(admin=True)
    with pytest.raises(PermissionError):
        resolve_source_write_scope(admin_without_publication_permission, [], shared=True)


@pytest.mark.asyncio
async def test_rejected_uploads_fail_before_source_or_chunk_persistence(monkeypatch, tmp_path):
    from fastapi import HTTPException, UploadFile

    import app.api.routes_sources as routes_sources

    class NoWriteSession:
        def add(self, _value):  # pragma: no cover - assertion path only
            raise AssertionError("rejected upload must not create a Source or Chunk")

    writer = _identity(
        departments=[DEPT_A], permissions={"doc:create:own_dept"},
    )

    async def assert_denied(*, visibility: str = "department",
                            department_ids: str | None = None, shared: bool = False) -> None:
        upload = UploadFile(filename="scope.txt", file=BytesIO(b"fixture"))
        with pytest.raises(HTTPException) as exc:
            await routes_sources.upload_source(
                file=upload,
                visibility=visibility,
                department_ids=department_ids,
                shared=shared,
                identity=writer,
                db=NoWriteSession(),
            )
        assert exc.value.status_code == 403

    # Authorization is resolved BEFORE the file is read or any row is added.
    await assert_denied(department_ids=str(DEPT_B))
    await assert_denied(department_ids=f"{DEPT_A},{DEPT_B}")
    await assert_denied(visibility="global", shared=True)


def _db_available() -> bool:
    import asyncpg

    async def _check() -> bool:
        try:
            conn = await asyncpg.connect("postgresql://bravo:bravo@localhost:5432/bravo")
            await conn.close()
            return True
        except Exception:
            return False

    return asyncio.run(_check())


pytestmark_db = pytest.mark.skipif(not _db_available(), reason="Postgres not reachable")


@pytestmark_db
def test_source_upload_scope_and_retrieval_isolation(monkeypatch, tmp_path):
    """Rejected uploads persist neither Source nor Chunk; shared is explicit only."""
    from httpx import ASGITransport, AsyncClient
    from sqlalchemy import delete, select
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
    from sqlalchemy.pool import NullPool

    import app.api.routes_sources as routes_sources
    from app.config import get_settings
    from app.database import get_db
    from app.database.models import Chunk, Department, Source, SourceDepartment
    from app.main import app
    from app.rag.retriever import lexical_search
    from app.security.auth import get_current_identity

    tag = f"rem-scope-{uuid.uuid4().hex}"
    vector = [0.1] * get_settings().embedding_dim
    state: dict[str, Identity] = {}

    async def _identity_override() -> Identity:
        return state["identity"]

    async def _fake_ingest(db, source_id, _path, *, trusted_knowledge_type=None):
        src = await db.get(Source, source_id)
        assert src is not None
        dept_ids = list((await db.execute(
            select(SourceDepartment.department_id).where(SourceDepartment.source_id == source_id)
        )).scalars().all())
        db.add(Chunk(
            source_id=source_id,
            content=f"{tag} {src.filename}",
            embedding=vector,
            department_ids=dept_ids,
            visibility=src.visibility,
            owner_id=src.owner_id,
            extra={},
        ))
        src.status = "ready"
        await db.commit()
        return 1

    async def run() -> None:
        engine = create_async_engine(get_settings().database_url, poolclass=NullPool)
        factory = async_sessionmaker(engine, expire_on_commit=False)

        async def _db_override():
            async with factory() as db:
                try:
                    yield db
                finally:
                    await db.rollback()

        app.dependency_overrides[get_db] = _db_override
        app.dependency_overrides[get_current_identity] = _identity_override
        # v2: files land under upload_root/workspace/...; ingest runs inline in tests.
        monkeypatch.setattr(get_settings(), "upload_root", str(tmp_path))
        monkeypatch.setattr(get_settings(), "ingest_sync", True)
        monkeypatch.setattr(routes_sources._settings, "ingest_sync", True)
        import app.storage_paths as storage_paths
        monkeypatch.setattr(storage_paths._settings, "upload_root", str(tmp_path))
        monkeypatch.setattr(routes_sources, "ingest_source", _fake_ingest)

        async with factory() as db:
            dept_a = Department(name=f"{tag}-A")
            dept_b = Department(name=f"{tag}-B")
            db.add_all([dept_a, dept_b])
            await db.commit()
            await db.refresh(dept_a)
            await db.refresh(dept_b)

        writer_a = _identity(
            departments=[dept_a.id],
            permissions={"doc:create:own_dept", "doc:read:own_dept"},
        )
        publisher = _identity(permissions={"doc:create:all", "doc:read:all"})
        reader_a = _identity(departments=[dept_a.id], permissions={"doc:read:own_dept"})
        reader_b = _identity(departments=[dept_b.id], permissions={"doc:read:own_dept"})

        upload_seq = {"n": 0}

        async def upload(identity: Identity, data: dict[str, str] | None = None):
            state["identity"] = identity
            upload_seq["n"] += 1
            # Unique bytes per call so scope-aware content-hash dedup does not collapse
            # these distinct authorization probes into one source.
            body = f"scope fixture {upload_seq['n']}".encode()
            return await client.post(
                "/api/sources",
                data=data,
                files={"file": (f"{tag}.txt", body, "text/plain")},
            )

        source_ids: list[uuid.UUID] = []
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                # 1. Explicit own department succeeds.
                own = await upload(writer_a, {"visibility": "department",
                                              "department_ids": str(dept_a.id)})
                assert own.status_code == 201, own.text
                source_ids.append(uuid.UUID(own.json()["id"]))

                # 2–3. Omitted/empty scope resolves only to the sole authoritative department.
                omitted = await upload(writer_a, {"visibility": "department"})
                empty = await upload(writer_a, {"visibility": "department", "department_ids": ""})
                assert omitted.status_code == empty.status_code == 201
                source_ids.extend([uuid.UUID(omitted.json()["id"]), uuid.UUID(empty.json()["id"])])

                # 4–5. Foreign and mixed requests fail without persisting a new source/chunk.
                rejected_before = len(source_ids)
                foreign = await upload(writer_a, {"visibility": "department",
                                                  "department_ids": str(dept_b.id)})
                mixed = await upload(writer_a, {"visibility": "department",
                                                "department_ids": f"{dept_a.id},{dept_b.id}"})
                assert foreign.status_code == mixed.status_code == 403

                # Own-department writers cannot opt into shared publication.
                shared_denied = await upload(writer_a, {"shared": "true"})
                assert shared_denied.status_code == 403

                # 6. An explicit all-scope publisher may create an explicitly shared source.
                shared = await upload(publisher, {"shared": "true"})
                assert shared.status_code == 201, shared.text
                shared_id = uuid.UUID(shared.json()["id"])
                source_ids.append(shared_id)

            async with factory() as db:
                mappings = (await db.execute(select(SourceDepartment))).scalars().all()
                by_source: dict[uuid.UUID, set[uuid.UUID]] = {}
                for mapping in mappings:
                    if mapping.source_id in source_ids:
                        by_source.setdefault(mapping.source_id, set()).add(mapping.department_id)
                assert all(by_source.get(sid) == {dept_a.id} for sid in source_ids[:-1])
                assert by_source.get(shared_id, set()) == set()

                stored_sources = (await db.execute(select(Source.id).where(Source.id.in_(source_ids)))).scalars().all()
                stored_chunks = (await db.execute(select(Chunk.source_id).where(Chunk.source_id.in_(source_ids)))).scalars().all()
                assert len(stored_sources) == rejected_before + 1
                assert len(stored_chunks) == rejected_before + 1

                # 7–8. The real lexical retrieval path preserves the stored scope.
                reader_a_hits = await lexical_search(db, reader_a, tag, k=50)
                reader_b_hits = await lexical_search(db, reader_b, tag, k=50)
                reader_a_sources = {uuid.UUID(hit.source_id) for hit in reader_a_hits}
                reader_b_sources = {uuid.UUID(hit.source_id) for hit in reader_b_hits}
                assert set(source_ids[:-1]).issubset(reader_a_sources)
                assert shared_id in reader_b_sources
                assert not (set(source_ids[:-1]) & reader_b_sources)
        finally:
            app.dependency_overrides.pop(get_db, None)
            app.dependency_overrides.pop(get_current_identity, None)
            async with factory() as db:
                await db.execute(delete(Chunk).where(Chunk.content.like(f"{tag}%")))
                await db.execute(delete(Source).where(Source.filename == f"{tag}.txt"))
                await db.execute(delete(Department).where(Department.name.in_([f"{tag}-A", f"{tag}-B"])))
                await db.commit()
            await engine.dispose()

    asyncio.run(run())
