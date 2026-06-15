"""Kế toán VN-native (TT99/2025) — phần ĐẦU của money-engine AP.

- coa.py        : danh mục tài khoản TT99 (lookup chính xác, KHÔNG RAG/embedding).
- crosswalk.py  : ánh xạ TT200 -> TT99 (đổi tên/thêm/bỏ) cho di trú.
- account_mapper: rule-first map hoá đơn -> tài khoản (LLM chỉ gợi ý khi mơ hồ).
- journal.py    : dựng bút toán kép + validator Nợ=Có (deterministic, ADR-0014).

Nguyên tắc: số liệu từ XML/calc — LLM KHÔNG sinh số (invariant #3). Ghi = nháp chờ duyệt
(invariant #2). Dữ liệu nguồn: file_system/Danh mục TK TT99.xlsx (freeze ra data/*.yaml).
"""
