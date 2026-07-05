"""OIDC SSO (W2.1) — Authorization Code + PKCE qua Authlib. LDAP/AD federate ở Keycloak.

Luồng: /auth/oidc/login -> IdP -> /auth/oidc/callback -> đổi code lấy userinfo -> map email
sang Employee (tạo nếu chưa có, quyền tối thiểu) -> phát JWT NỘI BỘ của app -> redirect SPA
kèm token. App KHÔNG tự bind LDAP; Keycloak lo AD/LDAP. Chỉ bật khi settings.oidc_enabled.

KHÔNG kiểm thử được đầy đủ nếu thiếu IdP thật — code gate + fail-closed; xem docs/SSO-OIDC.md
và deploy/docker-compose.keycloak.yml để dựng Keycloak self-host thử.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.database.models import Employee
from app.security.auth import create_access_token
from app.security.passwords import hash_password

router = APIRouter()
_settings = get_settings()

# Authlib OAuth client — chỉ khởi tạo khi bật OIDC (tránh cần metadata khi tắt).
_oauth = None


def _client():
    global _oauth
    if _oauth is None:
        from authlib.integrations.starlette_client import OAuth
        oauth = OAuth()
        oauth.register(
            name="bravo_idp",
            client_id=_settings.oidc_client_id,
            client_secret=_settings.oidc_client_secret,
            server_metadata_url=_settings.oidc_issuer.rstrip("/") + "/.well-known/openid-configuration",
            client_kwargs={"scope": "openid email profile"},
        )
        _oauth = oauth
    return _oauth.bravo_idp


def _require_enabled() -> None:
    if not _settings.oidc_enabled:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "OIDC không bật")


@router.get("/auth/config")
async def auth_config() -> dict:
    """Public: FE biết có hiện nút SSO không (không lộ secret)."""
    return {"oidc_enabled": _settings.oidc_enabled}


@router.get("/auth/oidc/login")
async def oidc_login(request: Request):
    _require_enabled()
    return await _client().authorize_redirect(request, _settings.oidc_redirect_uri)


@router.get("/auth/oidc/callback")
async def oidc_callback(request: Request, db: AsyncSession = Depends(get_db)):
    _require_enabled()
    token = await _client().authorize_access_token(request)
    userinfo = token.get("userinfo") or await _client().userinfo(token=token)
    email = (userinfo or {}).get("email")
    if not email:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "IdP không trả email")

    emp = (await db.execute(select(Employee).where(Employee.email == email))).scalar_one_or_none()
    if emp is None:
        # Tạo user tối thiểu từ SSO — quyền tối thiểu; admin gán phòng ban/quyền sau. Mật khẩu
        # ngẫu nhiên (không dùng — đăng nhập qua IdP). Không auto-admin.
        import secrets
        emp = Employee(email=email, full_name=(userinfo.get("name") or email),
                       password_hash=hash_password(secrets.token_urlsafe(24)),
                       is_admin=False, permissions=["doc:read:own_dept"])
        db.add(emp)
        await db.commit()
        await db.refresh(emp)

    app_jwt = create_access_token(emp.id)
    # Redirect SPA kèm token trong fragment (không lọt vào log server/referrer như query).
    return RedirectResponse(url=f"/login#token={app_jwt}", status_code=status.HTTP_302_FOUND)
