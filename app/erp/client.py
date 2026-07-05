"""Read-only ERP REST client — NÂNG CẤP TÙY CHỌN Phase sau, KHÔNG gating (ADR-0016).

Mũi nhọn ship hiện tại là "Copilot AP độc lập": đầu vào = chứng từ upload, đầu ra = file
xuất (journal_export) để kế toán nhập tay. Đường đọc tự động từ ERP REST API chỉ là nâng
cấp khi BRAVO (.NET) mở API read-only đã duyệt (VISION §8) — không phải điều kiện để chạy.

Khi hiện thực: httpx client read-ONLY, truyền scope (department/unit/period) xuống để RLS
giữ end-to-end; KHÔNG bao giờ ghi.
"""
from __future__ import annotations

# Chưa có API surface từ BRAVO -> module là placeholder có chủ đích, không stub một đường
# chạy dở. Import an toàn (không side-effect); các nhánh cần ERP đọc phải kiểm cấu hình trước.
raise_on_import = False
