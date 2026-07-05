"""Rate-limit per-user (W2.3) — slowapi. Chặn lạm dụng endpoint chat/agent.

Key = bearer token (per-user) nếu có, fallback IP. Vượt hạn -> 429 + Retry-After (không
treo). Bật/tắt qua settings.rate_limit_per_minute (0 = tắt).
"""
from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import get_settings

_settings = get_settings()


def _key(request) -> str:
    auth = request.headers.get("authorization") or ""
    if auth.lower().startswith("bearer "):
        return "u:" + auth[7:][-24:]      # đuôi token đủ phân biệt user, không log full token
    return "ip:" + get_remote_address(request)


limiter = Limiter(key_func=_key, enabled=_settings.rate_limit_per_minute > 0)


def chat_limit() -> str:
    """Chuỗi giới hạn cho endpoint chat/agent (vd '30/minute')."""
    return f"{_settings.rate_limit_per_minute}/minute"
