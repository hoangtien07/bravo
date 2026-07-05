"""Seed DỮ LIỆU MẪU để bản deploy sẵn sàng test nội bộ (không màn hình rỗng).

Tạo vài BÚT TOÁN NHÁP chờ duyệt từ hoá đơn fixture (do 'ketoan' = maker tạo), để:
  - Trang Hàng đợi duyệt (/drafts) + Money Engine có nội dung ngay.
  - 'ketoantruong' (checker ≠ maker) duyệt được -> test maker-checker E2E.
Idempotent nhẹ: nếu đã có ≥1 draft journal_entry thì bỏ qua (tránh nhân đôi khi chạy lại).

Chạy SAU seed_demo + alembic:  PYTHONPATH=. python scripts/seed_content.py
Cần Postgres đang chạy (DATABASE_URL trỏ đúng).
"""
from __future__ import annotations

import asyncio
from pathlib import Path

from sqlalchemy import func, select

from app.accounting import ap_service
from app.database import async_session_factory
from app.database.models import Draft, Employee
from app.security.rls import Identity

# Hoá đơn fixture parse SẠCH (cân Nợ=Có) — dùng làm nháp demo. Bỏ inv_bad_totals (cố tình lệch).
_ROOT = Path(__file__).resolve().parent.parent
SAMPLE_INVOICES = [
    _ROOT / "tests/fixtures/invoices/inv_single_10pct_goods.xml",
    _ROOT / "tests/fixtures/invoices/inv_multi_rate.xml",
    _ROOT / "tests/fixtures/invoices_demo/tscd_over30m.xml",
    _ROOT / "tests/fixtures/invoices_demo/vat_over20m.xml",
]
MAKER_EMAIL = "ketoan@bravo.vn"


async def main() -> None:
    async with async_session_factory() as db:
        n_existing = (await db.execute(
            select(func.count()).select_from(Draft).where(Draft.kind == "journal_entry"))).scalar()
        if n_existing and n_existing > 0:
            print(f"Đã có {n_existing} bút toán nháp — bỏ qua seed content (idempotent).")
            return

        emp = (await db.execute(
            select(Employee).where(Employee.email == MAKER_EMAIL))).scalar_one_or_none()
        if emp is None:
            print(f"Chưa có {MAKER_EMAIL} — chạy scripts/seed_demo.py trước.")
            return
        identity = Identity(employee_id=emp.id, department_ids=list(emp.department_ids),
                            permissions=frozenset(emp.permissions or []), is_admin=emp.is_admin)

        created = 0
        for path in SAMPLE_INVOICES:
            if not path.exists():
                print(f"  (bỏ qua, không thấy) {path.name}")
                continue
            try:
                draft, je = await ap_service.create_invoice_draft(
                    db, identity, path.read_bytes(), raw_xml_path=str(path))
                created += 1
                print(f"  + nháp {draft.id} từ {path.name} "
                      f"(Nợ={je.total_debit} = Có={je.total_credit})")
            except Exception as e:  # noqa: BLE001 — một fixture lỗi không chặn cả seed
                print(f"  ! lỗi {path.name}: {e}")

        print(f"Seed content xong: {created} bút toán nháp chờ duyệt (maker={MAKER_EMAIL}). "
              f"Đăng nhập 'ketoantruong@bravo.vn' để DUYỆT (maker-checker).")


if __name__ == "__main__":
    asyncio.run(main())
