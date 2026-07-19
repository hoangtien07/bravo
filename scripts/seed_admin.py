"""D1 — seed ONE real admin from env for an internal dogfood (not the shared demo123 accounts).

Creates/updates a single `is_admin` employee from BRAVO_ADMIN_EMAIL + BRAVO_ADMIN_PASSWORD so the
deploy has a strong, per-person admin who then creates team accounts via the Admin UI
(routes_admin `POST /api/admin/users`). Idempotent by email. Refuses a weak/short password.

Run:  BRAVO_ADMIN_EMAIL=it@congty.vn BRAVO_ADMIN_PASSWORD='<strong>' python scripts/seed_admin.py
"""
from __future__ import annotations

import asyncio
import os
import sys

from sqlalchemy import select

from app.database import async_session_factory
from app.database.models import Employee
from app.security.passwords import hash_password

_WEAK = {"demo123", "admin123", "change-me", "password"}


async def _seed(email: str, password: str, full_name: str) -> None:
    async with async_session_factory() as db:
        emp = (await db.execute(select(Employee).where(Employee.email == email))).scalar_one_or_none()
        if emp is None:
            emp = Employee(email=email, full_name=full_name,
                           password_hash=hash_password(password), is_admin=True)
            db.add(emp)
            action = "created"
        else:
            emp.password_hash = hash_password(password)
            emp.is_admin = True
            action = "updated"
        await db.commit()
    print(f"admin {action}: {email} (is_admin=True). Tạo tài khoản team qua trang Quản trị.")


def main() -> int:
    email = os.getenv("BRAVO_ADMIN_EMAIL", "").strip()
    password = os.getenv("BRAVO_ADMIN_PASSWORD", "")
    full_name = os.getenv("BRAVO_ADMIN_NAME", "Quản trị viên").strip()
    if not email or not password:
        print("Set BRAVO_ADMIN_EMAIL và BRAVO_ADMIN_PASSWORD.", file=sys.stderr)
        return 2
    if password in _WEAK or len(password) < 10:
        print("BRAVO_ADMIN_PASSWORD quá yếu/ngắn (≥10 ký tự, không dùng mật khẩu demo).",
              file=sys.stderr)
        return 2
    asyncio.run(_seed(email, password, full_name))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
