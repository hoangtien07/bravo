"""Auth routes: login (issues JWT). Registration/admin handled separately."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.database.models import Employee
from app.security.auth import create_access_token, get_current_identity
from app.security.rls import Identity

router = APIRouter()
_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")


@router.post("/auth/login")
async def login(form: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    emp = (await db.execute(select(Employee).where(Employee.email == form.username))).scalar_one_or_none()
    if emp is None or not _pwd.verify(form.password, emp.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Sai email hoặc mật khẩu")
    return {"access_token": create_access_token(emp.id), "token_type": "bearer"}


@router.get("/me")
async def me(identity: Identity = Depends(get_current_identity), db: AsyncSession = Depends(get_db)):
    emp = await db.get(Employee, identity.employee_id)
    return {
        "id": str(identity.employee_id),
        "full_name": emp.full_name if emp else "",
        "department_ids": [str(d) for d in identity.department_ids],
        "is_admin": identity.is_admin,
        "permissions": sorted(identity.permissions),
    }
