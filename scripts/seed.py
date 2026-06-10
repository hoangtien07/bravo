"""Seed sample departments, an admin, and scoped employees. Run: `python -m scripts.seed`.

Demonstrates the RLS model: an accountant sees Accounting + global; an HR person sees
HR + global; neither sees the other's documents.
"""
from __future__ import annotations

import asyncio

from sqlalchemy import select

from app.database import async_session_factory
from app.database.models import Department, Employee, EmployeeDepartment
from app.security.passwords import hash_password

VIEWER_PERMS = ["doc:read:own_dept"]
CONTRIB_PERMS = ["doc:read:own_dept", "doc:create:own_dept"]


async def _get_or_create_dept(db, name: str, sensitive: bool) -> Department:
    d = (await db.execute(select(Department).where(Department.name == name))).scalar_one_or_none()
    if d is None:
        d = Department(name=name, sensitive=sensitive)
        db.add(d)
        await db.flush()
    return d


async def _upsert_employee(db, email, name, password, perms, admin=False, depts=()):
    emp = (await db.execute(select(Employee).where(Employee.email == email))).scalar_one_or_none()
    if emp is None:
        emp = Employee(email=email, full_name=name, password_hash=hash_password(password),
                       is_admin=admin, permissions=perms)
        db.add(emp)
        await db.flush()
        for d in depts:
            db.add(EmployeeDepartment(employee_id=emp.id, department_id=d.id))
    return emp


async def main() -> None:
    async with async_session_factory() as db:
        accounting = await _get_or_create_dept(db, "Kế toán", sensitive=True)
        hr = await _get_or_create_dept(db, "Nhân sự", sensitive=True)
        await _get_or_create_dept(db, "Chung", sensitive=False)

        await _upsert_employee(db, "admin@bravo.vn", "Quản trị", "admin123",
                               perms=["doc:read:all", "doc:create:all"], admin=True)
        await _upsert_employee(db, "ketoan@bravo.vn", "Kế toán viên", "ketoan123",
                               perms=CONTRIB_PERMS, depts=[accounting])
        await _upsert_employee(db, "nhansu@bravo.vn", "HR viên", "nhansu123",
                               perms=VIEWER_PERMS, depts=[hr])
        await db.commit()
    print("Seed done: admin@bravo.vn / ketoan@bravo.vn / nhansu@bravo.vn (mật khẩu *123)")


if __name__ == "__main__":
    asyncio.run(main())
