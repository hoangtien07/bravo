"""Authentication & authorization (JWT + permission dependencies + MCP token hashing).

Rewritten from arkon patterns (ADR-0008). Tokens hashed with HMAC-SHA256 + pepper;
plaintext never stored (SECURITY-RLS §5).
"""
from __future__ import annotations

import hashlib
import hmac
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.database.models import Employee
from app.security.rls import Identity

_settings = get_settings()
_oauth2 = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


def create_access_token(employee_id: uuid.UUID) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=_settings.jwt_expire_minutes)
    payload = {"sub": str(employee_id), "exp": expire}
    return jwt.encode(payload, _settings.jwt_secret, algorithm=_settings.jwt_algorithm)


def hash_token(token: str) -> str:
    """HMAC-SHA256(pepper, token) — used for MCP/API tokens. Never store plaintext."""
    return hmac.new(_settings.mcp_token_pepper.encode(), token.encode(), hashlib.sha256).hexdigest()


async def _employee_to_identity(emp: Employee) -> Identity:
    return Identity(
        employee_id=emp.id,
        department_ids=list(emp.department_ids),
        permissions=frozenset(emp.permissions or []),
        is_admin=emp.is_admin,
    )


async def get_current_identity(
    token: str | None = Depends(_oauth2),
    db: AsyncSession = Depends(get_db),
) -> Identity:
    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    try:
        payload = jwt.decode(token, _settings.jwt_secret, algorithms=[_settings.jwt_algorithm])
        employee_id = uuid.UUID(payload["sub"])
    except (JWTError, KeyError, ValueError) as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token") from exc
    emp = await db.get(Employee, employee_id)
    if emp is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Unknown user")
    identity = await _employee_to_identity(emp)
    # P0.6: when the native RLS backstop is armed, stamp this request's transaction with the
    # per-identity GUCs the 0017 policies filter on. No-op by default (layer #1 WHERE clauses
    # remain the enforced path); this is defense-in-depth once an operator arms native RLS.
    if _settings.native_rls_enabled:
        from app.security.native_rls import apply_rls_gucs
        await apply_rls_gucs(db, identity)
    return identity


def require_permission(permission: str):
    """FastAPI dependency enforcing a permission. For scoped resources, accepts either
    the `:own_dept` or `:all` variant (scope is then narrowed in-query via rls.py)."""
    resource, action = permission.split(":", 1)

    async def _dep(identity: Identity = Depends(get_current_identity)) -> Identity:
        if identity.scope_level(resource, action) is None and not identity.is_admin:
            raise HTTPException(status.HTTP_403_FORBIDDEN, f"Missing permission: {permission}")
        return identity

    return _dep


async def require_admin(identity: Identity = Depends(get_current_identity)) -> Identity:
    """Chỉ admin (quản trị user/phòng ban). Khác require_permission: is_admin cứng."""
    if not identity.is_admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Chỉ quản trị viên")
    return identity


async def resolve_mcp_identity(token: str, db: AsyncSession) -> Identity | None:
    """Resolve an MCP bearer token (plaintext) to an Identity via its stored hash."""
    digest = hash_token(token)
    emp = (await db.execute(select(Employee).where(Employee.mcp_token_hash == digest))).scalar_one_or_none()
    return await _employee_to_identity(emp) if emp else None
