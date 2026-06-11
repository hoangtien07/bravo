"""Seed dữ liệu demo: departments + employees + permissions cho demo agentic (RLS + eval).

Idempotent: department upsert theo tên; 4 employee demo recreate theo email.
Chạy:  PYTHONPATH=. python scripts/seed_demo.py   (cần Postgres đang chạy).
Khớp docs/MOCK-DATA-SPEC.md (DN "Thép DEMO") + email mà eval/run.py mong đợi.

Permission (2 kiểu trong codebase):
  - tool filter (metric_lookup) dùng exact-match  -> "metric:read"
  - routes/RLS dùng scope-level {res}:{act}:{scope} -> "doc:read:own_dept", "draft:approve:own_dept"
  - chỉ tiêu nhạy quy_luong_thang (WP-F) yêu cầu     -> "metric:read:hr"  (chỉ Nhân sự/Giám đốc)
"""
from __future__ import annotations

import asyncio

from sqlalchemy import delete, select

from app.database import async_session_factory
from app.database.models import Department, Employee, EmployeeDepartment
from app.security.passwords import hash_password

# (tên, sensitive) — sensitive => egress ghim local + chỉ tiêu nhạy.
DEPARTMENTS: list[tuple[str, bool]] = [
    ("Ban Giám đốc", False),
    ("Phòng Kế toán", True),
    ("Phòng Kinh doanh", False),
    ("Phòng Nhân sự", True),
    ("Phòng Kho-Sản xuất", False),
    ("Phòng Mua hàng", False),
]

# email, full_name, is_admin, [dept names], [permissions]
EMPLOYEES: list[tuple[str, str, bool, list[str], list[str]]] = [
    ("giamdoc@bravo.vn", "Giám đốc", True, ["Ban Giám đốc"], []),  # admin bypass
    ("ketoan@bravo.vn", "Kế toán viên", False, ["Phòng Kế toán"],
     ["doc:read:own_dept", "metric:read", "draft:create:own_dept", "draft:approve:own_dept"]),
    ("kinhdoanh@bravo.vn", "Nhân viên Kinh doanh", False, ["Phòng Kinh doanh"],
     ["doc:read:own_dept", "metric:read"]),
    ("nhansu@bravo.vn", "Nhân viên Nhân sự", False, ["Phòng Nhân sự"],
     ["doc:read:own_dept", "metric:read", "metric:read:hr"]),  # thấy được lương
]

PASSWORD = "demo123"


async def main() -> None:
    async with async_session_factory() as db:
        # 1) departments: get-or-create theo tên (cập nhật cờ sensitive).
        dept_id: dict[str, object] = {}
        for name, sensitive in DEPARTMENTS:
            d = (await db.execute(
                select(Department).where(Department.name == name))).scalar_one_or_none()
            if d is None:
                d = Department(name=name, sensitive=sensitive)
                db.add(d)
                await db.flush()
            else:
                d.sensitive = sensitive
            dept_id[name] = d.id
        await db.commit()

        # 2) employees: recreate theo email (idempotent).
        pw = hash_password(PASSWORD)
        for email, full_name, is_admin, depts, perms in EMPLOYEES:
            existing = (await db.execute(
                select(Employee).where(Employee.email == email))).scalar_one_or_none()
            if existing is not None:
                await db.execute(delete(EmployeeDepartment).where(
                    EmployeeDepartment.employee_id == existing.id))
                await db.execute(delete(Employee).where(Employee.id == existing.id))
                await db.commit()
            emp = Employee(email=email, full_name=full_name, password_hash=pw,
                           is_admin=is_admin, permissions=perms)
            db.add(emp)
            await db.flush()
            for dn in depts:
                db.add(EmployeeDepartment(employee_id=emp.id, department_id=dept_id[dn]))
            await db.commit()

        print(f"Seeded {len(DEPARTMENTS)} departments + {len(EMPLOYEES)} employees "
              f"(mật khẩu demo: '{PASSWORD}').")
        for email, full_name, is_admin, depts, perms in EMPLOYEES:
            tag = "ADMIN" if is_admin else ",".join(perms)
            print(f"  - {email:22} [{','.join(depts)}]  {tag}")


if __name__ == "__main__":
    asyncio.run(main())
