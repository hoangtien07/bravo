"""Đếm token cho quản lý context-window (pattern letta context_window_calculator).

Dùng tiktoken (đã là dep) — cl100k_base xấp xỉ tốt cho cả tiếng Việt. Không có tiktoken
hoặc lỗi -> fallback ước lượng ~4 ký tự/token. Mục đích: quyết định khi nào nén hội thoại
dài để không tràn context của model (đặc biệt model cục bộ context nhỏ).
"""
from __future__ import annotations

from functools import lru_cache


@lru_cache(maxsize=1)
def _enc():
    try:
        import tiktoken
        return tiktoken.get_encoding("cl100k_base")
    except Exception:
        return None


def count_tokens(text: str) -> int:
    if not text:
        return 0
    enc = _enc()
    if enc is None:
        return max(1, len(text) // 4)
    try:
        return len(enc.encode(text))
    except Exception:
        return max(1, len(text) // 4)


def count_messages(messages: list[dict]) -> int:
    """Tổng token xấp xỉ của một list message (+4/message cho overhead role)."""
    return sum(count_tokens(m.get("content", "")) + 4 for m in messages)
