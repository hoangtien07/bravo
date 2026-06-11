"""Sensitivity classification for egress control (WP-C / ADR-0011).

DETERMINISTIC — KHÔNG để LLM tự đánh giá độ nhạy. Router gọi hàm này để quyết
local-vs-cloud; KHÔNG nhận `sensitive` thủ công từ caller (council Critical: một bước
truyền nhầm làm rò lương/HR ra cloud không vết audit).

Quy tắc (fail-closed): nhạy nếu BẤT KỲ phần tử ngữ cảnh nào chạm phòng ban nhạy,
loại tri thức nhạy, cờ nhạy, hoặc là số liệu tài chính THẬT (không phải mock demo).
Không có căn cứ để phán -> coi là nhạy -> local.

Tái dùng nhãn RLS (department/knowledge_type) làm nhãn nhạy (invariant #1 -> #4).
`sensitive_dept_ids` do router resolve từ Department.sensitive (DB) rồi truyền vào -> hàm
này thuần, test được không cần DB.
"""
from __future__ import annotations

from collections.abc import Iterable

# Loại tri thức nhạy mặc định (chuẩn hoá lower, không dấu được thêm để bắt cả 2 cách viết).
DEFAULT_SENSITIVE_KNOWLEDGE_TYPES: frozenset[str] = frozenset({
    "accounting", "ketoan", "kế toán", "ke toan",
    "payroll", "luong", "lương",
    "hr", "nhân sự", "nhan su",
    "pii", "salary", "finance_internal",
})


def classify_context(
    items: Iterable[object],
    *,
    sensitive_dept_ids: frozenset | set = frozenset(),
    sensitive_knowledge_types: frozenset[str] = DEFAULT_SENSITIVE_KNOWLEDGE_TYPES,
) -> bool:
    """True = ngữ cảnh nhạy -> ép LOCAL. Fail-closed: không có căn cứ -> True."""
    saw_any = False
    for it in items:
        saw_any = True
        # 1) phòng ban nhạy
        for dept in (getattr(it, "department_ids", None) or []):
            if dept in sensitive_dept_ids:
                return True
        # 2) loại tri thức nhạy
        kt = (getattr(it, "knowledge_type", None) or "").strip().lower()
        if kt in sensitive_knowledge_types:
            return True
        # 3) cờ nhạy tường minh
        if getattr(it, "is_sensitive", False):
            return True
        # 4) số liệu tài chính THẬT (MetricResult, không phải mock demo) -> nhạy
        if getattr(it, "metric_id", None) and getattr(it, "currency", None) \
                and getattr(it, "is_demo", False) is False:
            return True
    # Có phần tử và không phần tử nào nhạy -> cho phép cloud; rỗng/không rõ -> fail-closed local.
    return not saw_any
