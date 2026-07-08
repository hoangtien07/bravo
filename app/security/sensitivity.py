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


def ingest_sensitive(knowledge_type: str | None, *, has_departments: bool,
                     touches_sensitive_dept: bool) -> bool:
    """Quyết định egress khi NẠP một Source (fail-closed, invariant #4).

    Nhạy (-> embed LOCAL, cấm cloud) nếu:
      1. `knowledge_type` thuộc loại nhạy (kế toán/lương/HR/PII…), HOẶC
      2. nguồn thuộc ≥1 phòng ban nhạy, HOẶC
      3. **'không rõ scope'**: nguồn GLOBAL (không phòng ban) VÀ không có `knowledge_type` để
         phán -> coi là nhạy. Vá lỗ: tài liệu nhạy nạp global-không-nhãn từng bị cloud-embed
         (pipeline cũ bỏ qua check khi `dept_ids` rỗng). Tài liệu công khai hợp lệ luôn có
         `knowledge_type` (vd 'guide') nên KHÔNG bị chặn -> demo không đổi.
    """
    kt = (knowledge_type or "").strip().lower()
    if kt in DEFAULT_SENSITIVE_KNOWLEDGE_TYPES:
        return True
    if has_departments and touches_sensitive_dept:
        return True
    if not has_departments and not kt:
        return True
    return False


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
