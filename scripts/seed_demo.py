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
# Bộ tài khoản phủ MỌI vai để test nội bộ E2E:
#  - giamdoc  = ADMIN (test trang Quản trị, cost/usage).
#  - ketoan   = MAKER (tạo bút toán nháp; KHÔNG có draft:approve -> không tự duyệt được).
#  - ketoantruong = CHECKER (draft:approve:own_dept) -> duyệt nháp của ketoan (maker-checker THẬT).
#  - kinhdoanh = ngoài phòng kế toán (test RLS: KHÔNG thấy nháp/lương phòng khác).
#  - nhansu   = có metric:read:hr (test chỉ tiêu nhạy lương chỉ HR thấy).
EMPLOYEES: list[tuple[str, str, bool, list[str], list[str]]] = [
    ("giamdoc@bravo.vn", "Giám đốc", True, ["Ban Giám đốc"], []),  # admin bypass
    ("ketoan@bravo.vn", "Kế toán viên (maker)", False, ["Phòng Kế toán"],
     ["doc:read:own_dept", "doc:create", "metric:read", "draft:create:own_dept"]),
    ("ketoantruong@bravo.vn", "Kế toán trưởng (checker)", False, ["Phòng Kế toán"],
     ["doc:read:own_dept", "doc:create", "metric:read", "draft:create:own_dept",
      "draft:approve:own_dept"]),
    ("kinhdoanh@bravo.vn", "Nhân viên Kinh doanh", False, ["Phòng Kinh doanh"],
     ["doc:read:own_dept", "metric:read"]),
    ("nhansu@bravo.vn", "Nhân viên Nhân sự", False, ["Phòng Nhân sự"],
     ["doc:read:own_dept", "metric:read", "metric:read:hr"]),  # thấy được lương
]

PASSWORD = "demo123"

# Token MCP demo (plaintext) cho ketoantruong — để test kết nối Claude Desktop/Code vào /mcp.
# CHỈ dùng cho demo/test nội bộ; production cấp token ngẫu nhiên riêng.
MCP_DEMO_TOKEN = "bravo-mcp-demo-token"
MCP_DEMO_EMAIL = "ketoantruong@bravo.vn"


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

        # 2) employees: UPSERT tại chỗ (idempotent + an toàn FK — KHÔNG xoá-tạo-lại vì employee
        #    có thể đang bị draft/audit tham chiếu qua khoá ngoại).
        pw = hash_password(PASSWORD)
        from app.security.auth import hash_token
        for email, full_name, is_admin, depts, perms in EMPLOYEES:
            emp = (await db.execute(
                select(Employee).where(Employee.email == email))).scalar_one_or_none()
            if emp is None:
                emp = Employee(email=email)
                db.add(emp)
            emp.full_name = full_name
            emp.password_hash = pw
            emp.is_admin = is_admin
            emp.permissions = perms
            emp.mcp_token_hash = hash_token(MCP_DEMO_TOKEN) if email == MCP_DEMO_EMAIL else None
            await db.flush()
            # Reset phòng ban của employee này (chỉ xoá bảng nối, không xoá employee).
            await db.execute(delete(EmployeeDepartment).where(
                EmployeeDepartment.employee_id == emp.id))
            for dn in depts:
                db.add(EmployeeDepartment(employee_id=emp.id, department_id=dept_id[dn]))
            await db.commit()

        print(f"Seeded {len(DEPARTMENTS)} departments + {len(EMPLOYEES)} employees "
              f"(mật khẩu demo: '{PASSWORD}').")
        for email, full_name, is_admin, depts, perms in EMPLOYEES:
            tag = "ADMIN" if is_admin else ",".join(perms)
            print(f"  - {email:24} [{','.join(depts)}]  {tag}")
        print(f"MCP demo token cho {MCP_DEMO_EMAIL}: '{MCP_DEMO_TOKEN}' (bearer khi nối /mcp).")


if __name__ == "__main__":
    asyncio.run(main())
