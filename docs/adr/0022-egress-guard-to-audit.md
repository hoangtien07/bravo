# 0022. Egress GUARD → egress AUDIT (giữ code, đổi vai trò dưới cloud-only)

- **Trạng thái:** Accepted (2026-07-12)
- **Ngày:** 2026-07-12
- **Amends:** [ADR-0011](0011-egress-classification-audit.md) (phân loại độ nhạy + audit-then-egress).
- **Liên quan:** [ADR-0019](0019-cloud-only-llm-strategy.md).

## Bối cảnh (Context)

ADR-0011 dựng hai cơ chế: (a) **guard** — chặn nội dung nhạy rời mạng (fail-closed về local); (b) **audit** — ghi `AuditLog action=llm.egress` (hash prompt) TRƯỚC khi gọi cloud. Dưới cloud-only (ADR-0019) không còn backend local, nên "chặn về local" vô nghĩa — nếu giữ nguyên, guard sẽ **crash** (embedding raise) hoặc **âm thầm giảm chất lượng** (rerank bỏ qua chunk nhạy).

## Quyết định (Decision)

**Chuyển GUARD thành AUDIT — KHÔNG xoá code phân loại.**

- `egress_policy=cloud_only`: `sensitivity.classify_context`/`ingest_sensitive` vẫn CHẠY và vẫn ghi nhãn nhạy vào `AuditLog`/`Chunk.extra[is_sensitive]`, nhưng KHÔNG chặn. Đây là **dấu vết tuân thủ PDPL/91-2025** (biết cái gì nhạy đã rời mạng), không phải rào sovereignty.
- `egress_policy=hybrid` (mặc định): hành vi ADR-0011 nguyên vẹn (guard fail-closed về local).
- **Audit vẫn fail-closed:** nếu ghi `AuditLog` lỗi → KHÔNG egress (giữ nguyên `_audit_egress`). Mất được cloud, không được mất vết.
- **Định nghĩa lại EGRESS_LEAK trong eval:** từ "gọi cloud với nội dung nhạy" → "gọi cloud MÀ THIẾU audit row đi trước" (audit-integrity thay cho egress-prevention). Probe pass^k cập nhật.

## Hệ quả (Consequences)

- **Tích cực:** không crash/không giảm chất lượng dưới cloud-only; giữ toàn bộ hạ tầng phân loại để quay lại `hybrid` khi cần; audit trở thành artifact pháp lý.
- **Tiêu cực:** dưới cloud-only, dữ liệu nhạy CÓ rời mạng (chấp nhận theo ADR-0019 + rà soát pháp lý paid-tier). Ba quy ước NULL/empty-scope (Chunk/Source visibility · ArchivalPassage owner-or-dept · Draft NULL=global) cùng tồn tại — ghi trong SECURITY-RLS.md chống copy-paste leak.
- **Bất biến:** #1/#2/#3 giữ; #4 theo ADR-0019.

## Tham chiếu
`app/security/sensitivity.py`, `app/llm/router.py::_audit_egress`, `app/rag/embedding.py`, `app/eval/probes.py`.
