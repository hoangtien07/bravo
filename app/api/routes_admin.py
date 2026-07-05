"""Admin routes (W1.8): CRUD user + phòng ban + đổi/reset mật khẩu.

Tối thiểu để KHÔNG phải chạy script Python thêm user (chặn của IT manager/helpdesk). Gán
role = danh sách permission có sẵn (SECURITY-RLS §2.2) + phòng ban -> RLS scope đúng. Mọi
endpoint yêu cầu is_admin (require_admin) — trừ đổi mật khẩu CỦA CHÍNH MÌNH (self-service).
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.database.models import Department, Employee, EmployeeDepartment
from app.security.auth import get_current_identity, require_admin
from app.security.passwords import hash_password, verify_password
from app.security.rls import Identity

router = APIRouter()

# Bộ permission gán được (khớp scope_level trong rls.py). Giữ HẸP — không cho tự chế permission.
ASSIGNABLE_PERMISSIONS = [
    "doc:read:own_dept", "doc:read:all", "doc:create", "doc:create:all",
    "metric:read", "draft:create", "draft:approve", "draft:approve:own_dept",
]


class UserOut(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    is_admin: bool
    permissions: list[str]
    department_ids: list[uuid.UUID]


class UserCreateIn(BaseModel):
    email: str
    full_name: str
    password: str = Field(min_length=6)
    is_admin: bool = False
    permissions: list[str] = Field(default_factory=list)
    department_ids: list[uuid.UUID] = Field(default_factory=list)


class UserUpdateIn(BaseModel):
    full_name: str | None = None
    is_admin: bool | None = None
    permissions: list[str] | None = None
    department_ids: list[uuid.UUID] | None = None


class PasswordSetIn(BaseModel):
    new_password: str = Field(min_length=6)


class SelfPasswordIn(BaseModel):
    current_password: str
    new_password: str = Field(min_length=6)


class DeptIn(BaseModel):
    name: str
    sensitive: bool = False


def _user_out(e: Employee) -> UserOut:
    return UserOut(id=e.id, email=e.email, full_name=e.full_name, is_admin=e.is_admin,
                   permissions=list(e.permissions or []), department_ids=list(e.department_ids))


def _validate_perms(perms: list[str]) -> None:
    bad = [p for p in perms if p not in ASSIGNABLE_PERMISSIONS]
    if bad:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY,
                            f"Permission không hợp lệ: {bad}. Cho phép: {ASSIGNABLE_PERMISSIONS}")


async def _set_departments(db: AsyncSession, emp_id: uuid.UUID, dept_ids: list[uuid.UUID]) -> None:
    from sqlalchemy import delete
    await db.execute(delete(EmployeeDepartment).where(EmployeeDepartment.employee_id == emp_id))
    for d in dept_ids:
        db.add(EmployeeDepartment(employee_id=emp_id, department_id=d))


# --------------------------------------------------------------------------------------
# Users
# --------------------------------------------------------------------------------------
@router.get("/admin/users", response_model=list[UserOut])
async def list_users(_: Identity = Depends(require_admin),
                     db: AsyncSession = Depends(get_db)) -> list[UserOut]:
    rows = (await db.execute(select(Employee).order_by(Employee.email))).scalars().all()
    return [_user_out(e) for e in rows]


@router.get("/admin/permissions", response_model=list[str])
async def assignable_permissions(_: Identity = Depends(require_admin)) -> list[str]:
    return ASSIGNABLE_PERMISSIONS


@router.post("/admin/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(body: UserCreateIn, _: Identity = Depends(require_admin),
                      db: AsyncSession = Depends(get_db)) -> UserOut:
    _validate_perms(body.permissions)
    exists = (await db.execute(select(Employee).where(Employee.email == body.email))).scalar_one_or_none()
    if exists is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Email đã tồn tại")
    emp = Employee(email=body.email, full_name=body.full_name,
                   password_hash=hash_password(body.password), is_admin=body.is_admin,
                   permissions=body.permissions)
    db.add(emp)
    await db.flush()
    await _set_departments(db, emp.id, body.department_ids)
    await db.commit()
    await db.refresh(emp)
    return _user_out(emp)


@router.patch("/admin/users/{user_id}", response_model=UserOut)
async def update_user(user_id: uuid.UUID, body: UserUpdateIn,
                      admin: Identity = Depends(require_admin),
                      db: AsyncSession = Depends(get_db)) -> UserOut:
    emp = await db.get(Employee, user_id)
    if emp is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User không tồn tại")
    if body.permissions is not None:
        _validate_perms(body.permissions)
        emp.permissions = body.permissions
    if body.full_name is not None:
        emp.full_name = body.full_name
    if body.is_admin is not None:
        # Không cho tự hạ quyền admin của chính mình (tránh khoá mình ra ngoài).
        if emp.id == admin.employee_id and body.is_admin is False:
            raise HTTPException(status.HTTP_409_CONFLICT, "Không thể tự bỏ quyền admin của chính mình")
        emp.is_admin = body.is_admin
    if body.department_ids is not None:
        await _set_departments(db, emp.id, body.department_ids)
    await db.commit()
    await db.refresh(emp)
    return _user_out(emp)


@router.post("/admin/users/{user_id}/password", status_code=status.HTTP_204_NO_CONTENT)
async def reset_password(user_id: uuid.UUID, body: PasswordSetIn,
                         _: Identity = Depends(require_admin),
                         db: AsyncSession = Depends(get_db)):
    emp = await db.get(Employee, user_id)
    if emp is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User không tồn tại")
    emp.password_hash = hash_password(body.new_password)
    await db.commit()


# --------------------------------------------------------------------------------------
# Self-service đổi mật khẩu (mọi user, KHÔNG cần admin)
# --------------------------------------------------------------------------------------
@router.post("/auth/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_own_password(body: SelfPasswordIn,
                              identity: Identity = Depends(get_current_identity),
                              db: AsyncSession = Depends(get_db)):
    emp = await db.get(Employee, identity.employee_id)
    if emp is None or not verify_password(body.current_password, emp.password_hash):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Mật khẩu hiện tại không đúng")
    emp.password_hash = hash_password(body.new_password)
    await db.commit()


# --------------------------------------------------------------------------------------
# Departments
# --------------------------------------------------------------------------------------
class DeptOut(BaseModel):
    id: uuid.UUID
    name: str
    sensitive: bool


@router.get("/admin/departments", response_model=list[DeptOut])
async def list_departments(_: Identity = Depends(require_admin),
                           db: AsyncSession = Depends(get_db)) -> list[DeptOut]:
    rows = (await db.execute(select(Department).order_by(Department.name))).scalars().all()
    return [DeptOut(id=d.id, name=d.name, sensitive=d.sensitive) for d in rows]


@router.post("/admin/departments", response_model=DeptOut, status_code=status.HTTP_201_CREATED)
async def create_department(body: DeptIn, _: Identity = Depends(require_admin),
                            db: AsyncSession = Depends(get_db)) -> DeptOut:
    exists = (await db.execute(select(Department).where(Department.name == body.name))).scalar_one_or_none()
    if exists is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Phòng ban đã tồn tại")
    d = Department(name=body.name, sensitive=body.sensitive)
    db.add(d)
    await db.commit()
    await db.refresh(d)
    return DeptOut(id=d.id, name=d.name, sensitive=d.sensitive)


# --------------------------------------------------------------------------------------
# Usage / cost tracking (W2.4) — tổng hợp token THẬT từ AgentRun theo người dùng.
# --------------------------------------------------------------------------------------
class UsageRow(BaseModel):
    employee_id: uuid.UUID
    email: str | None = None
    turns: int
    tokens: int
    est_cost: float


@router.get("/admin/usage", response_model=list[UsageRow])
async def usage(days: int = 7, _: Identity = Depends(require_admin),
                db: AsyncSession = Depends(get_db)) -> list[UsageRow]:
    """Token + ước phí theo người dùng trong N ngày gần nhất (AgentRun.tokens_used THẬT).

    est_cost = tokens/1e6 × trung bình (prompt+completion rate) — ước lượng blended vì AgentRun
    lưu tổng token, không tách. Đơn giá đặt ở settings.cost_per_1m_* (mặc định 0 -> chi phí 0).
    """
    from datetime import timedelta

    from sqlalchemy import func

    from app.config import get_settings
    from app.database.models import AgentRun, Employee

    s = get_settings()
    blended = (s.cost_per_1m_prompt_tokens + s.cost_per_1m_completion_tokens) / 2.0
    # func.now() - interval: dùng timedelta bind qua Python (đơn giản, không cần dialect interval).
    since = func.now() - timedelta(days=max(1, days))
    rows = (await db.execute(
        select(AgentRun.employee_id,
               func.count().label("turns"),
               func.coalesce(func.sum(AgentRun.tokens_used), 0).label("tokens"))
        .where(AgentRun.created_at >= since)
        .group_by(AgentRun.employee_id)
        .order_by(func.sum(AgentRun.tokens_used).desc().nullslast()))).all()
    # nhãn email
    emp_rows = (await db.execute(select(Employee.id, Employee.email))).all()
    emails = {eid: em for eid, em in emp_rows}
    out = []
    for eid, turns, tokens in rows:
        tok = int(tokens or 0)
        out.append(UsageRow(employee_id=eid, email=emails.get(eid), turns=int(turns),
                            tokens=tok, est_cost=round(tok / 1_000_000 * blended, 4)))
    return out
