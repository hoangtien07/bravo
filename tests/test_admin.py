"""W1.8 — admin CRUD user/phòng ban + đổi mật khẩu (DB integration, skip nếu Postgres tắt)."""
from __future__ import annotations

import asyncio
import uuid

import httpx
import pytest
from httpx import ASGITransport


def _db_available() -> bool:
    import asyncpg

    async def _c():
        try:
            conn = await asyncpg.connect("postgresql://bravo:bravo@localhost:5432/bravo")
            await conn.close()
            return True
        except Exception:
            return False

    return asyncio.run(_c())


pytestmark = pytest.mark.skipif(not _db_available(), reason="Postgres not reachable")


def _run(body):
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
                await body(c, factory)
        finally:
            app.dependency_overrides.pop(get_db, None)
            await engine.dispose()

    asyncio.run(inner())


async def _make_admin(factory) -> tuple[uuid.UUID, str]:
    from app.database.models import Employee
    from app.security.auth import create_access_token
    from app.security.passwords import hash_password

    async with factory() as s:
        emp = Employee(email=f"admin_{uuid.uuid4().hex[:8]}@bravo.vn", full_name="Admin Test",
                       password_hash=hash_password("admin123"), is_admin=True, permissions=[])
        s.add(emp)
        await s.commit()
        await s.refresh(emp)
        return emp.id, create_access_token(emp.id)


def test_admin_creates_user_and_user_can_login_and_change_password():
    async def body(c, factory):
        _, token = await _make_admin(factory)
        c.headers["Authorization"] = f"Bearer {token}"

        # tạo phòng ban
        dept = (await c.post("/api/admin/departments",
                             json={"name": f"KT_{uuid.uuid4().hex[:6]}"})).json()
        email = f"nv_{uuid.uuid4().hex[:8]}@bravo.vn"
        r = await c.post("/api/admin/users", json={
            "email": email, "full_name": "Nhân viên", "password": "matkhau1",
            "permissions": ["doc:read:own_dept"], "department_ids": [dept["id"]]})
        assert r.status_code == 201, r.text
        uid = r.json()["id"]
        assert r.json()["department_ids"] == [dept["id"]]

        # user mới login được
        lr = await c.post("/api/auth/login", data={"username": email, "password": "matkhau1"})
        assert lr.status_code == 200, lr.text
        utok = lr.json()["access_token"]

        # user tự đổi mật khẩu (sai current -> 403; đúng -> 204)
        uc = httpx.Headers({"Authorization": f"Bearer {utok}"})
        bad = await c.post("/api/auth/change-password", headers=uc,
                           json={"current_password": "sai", "new_password": "matkhau2"})
        assert bad.status_code == 403
        ok = await c.post("/api/auth/change-password", headers=uc,
                          json={"current_password": "matkhau1", "new_password": "matkhau2"})
        assert ok.status_code == 204

        # đăng nhập bằng mật khẩu mới
        lr2 = await c.post("/api/auth/login", data={"username": email, "password": "matkhau2"})
        assert lr2.status_code == 200

        # permission không hợp lệ -> 422
        bad_perm = await c.patch(f"/api/admin/users/{uid}", json={"permissions": ["hack:all"]})
        assert bad_perm.status_code == 422

    _run(body)


def test_non_admin_forbidden():
    async def body(c, factory):
        from app.database.models import Employee
        from app.security.auth import create_access_token
        from app.security.passwords import hash_password

        async with factory() as s:
            emp = Employee(email=f"u_{uuid.uuid4().hex[:8]}@bravo.vn", full_name="U",
                           password_hash=hash_password("x"), is_admin=False, permissions=[])
            s.add(emp)
            await s.commit()
            await s.refresh(emp)
            tok = create_access_token(emp.id)
        c.headers["Authorization"] = f"Bearer {tok}"
        assert (await c.get("/api/admin/users")).status_code == 403

    _run(body)
