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


# High-detail image ≈ 1–2k tokens; a flat estimate keeps multimodal turns from being counted as
# ~0 tokens (M4 — a content-window cap that couldn't see images was effectively blind).
IMAGE_TOKEN_EST = 1600


def count_messages(messages: list[dict]) -> int:
    """Tổng token xấp xỉ của một list message (+4/message cho overhead role).

    M4: content có thể là str HOẶC mảng multimodal (text + image_url). Ảnh được tính bằng
    IMAGE_TOKEN_EST (không phải ~0) để cap context không 'mù' với payload ảnh."""
    total = 0
    for m in messages:
        content = m.get("content", "")
        if isinstance(content, list):
            for part in content:
                if not isinstance(part, dict):
                    total += count_tokens(str(part))
                elif part.get("type") == "image_url":
                    total += IMAGE_TOKEN_EST
                else:
                    total += count_tokens(part.get("text", ""))
        else:
            total += count_tokens(content)
        total += 4
    return total
