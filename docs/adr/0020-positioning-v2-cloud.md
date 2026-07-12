# 0020. Định vị v2.0 — moat = nghiệp vụ BRAVO, KHÔNG phải chủ quyền/on-prem

- **Trạng thái:** Accepted (2026-07-12)
- **Ngày:** 2026-07-12
- **Người quyết định:** Chủ dự án.
- **Supersedes:** [ADR-0006](0006-market-positioning.md) (moat = chủ quyền + không bịa số).
- **Liên quan:** [ADR-0019](0019-cloud-only-llm-strategy.md) (cloud-only); [MATURITY-LADDER.md](../MATURITY-LADDER.md); cập nhật `docs/VISION.md`, `docs/SOVEREIGNTY-DEMO-NOTE.md`.

## Bối cảnh (Context)

ADR-0006 đặt moat kép: (a) chủ quyền/on-prem + (b) không bịa số. ADR-0019 vừa bỏ (a) khỏi phạm vi v2 (cloud-only). Cần định vị lại kẻo mất luận điểm bán hàng.

Quan sát từ council 2026-07-12: người dùng chấm bravo như một chatbot tra cứu tổng quát — trục mà Gemini thắng sẵn nhờ world-knowledge. Nhưng thứ Gemini KHÔNG làm được: hiểu nghiệp vụ BRAVO ERP cụ thể (mã giao dịch, định khoản, quy trình khoá sổ), cưỡng chế phân quyền phòng ban, tạo bút toán nháp qua maker-checker, và **không bịa số kế toán**.

## Quyết định (Decision)

**Moat v2 = nghiệp vụ BRAVO + kỷ luật số, KHÔNG phải hạ tầng.** Cụ thể, bốn thứ một LibreChat+Gemini phổ thông KHÔNG có:

1. **Số kiểm chứng được** — verify-gate cân Nợ=Có + trích nguồn từng ô/số (bất biến #3). Gemini bịa số trôi chảy; bravo từ chối hoặc trích nguồn.
2. **RLS-in-SQL theo phòng ban + cá nhân** (bất biến #1) — chatbot công khai không có.
3. **Maker-checker / draft-only** (bất biến #2) — đề xuất bút toán thành nháp chờ duyệt, xuất file nhập tay.
4. **Corpus đặc thù BRAVO** — catalog mã giao dịch, ticket helpdesk, quy trình — dữ liệu Gemini không có (xem `docs/CORPUS-OPS.md`).

**Stop-rule (kỷ luật chống đào-sâu Q&A):** khi đạt citation ≥95% + parity ≥ hoà với BravoGen + first-token <3s → **DỪNG** đầu tư đánh bóng Q&A tổng quát, quay lại track AP/agentic (ADR-0016). Không đua world-knowledge với Gemini — đó là trục thua theo cấu tạo; thắng ở trục nghiệp vụ.

## Hệ quả (Consequences)

- **Tích cực:** luận điểm bán rõ ("AI hiểu BRAVO + không bịa số + phân quyền", không phải "rẻ/offline"); tránh đua tính năng chatbot vô tận.
- **Tiêu cực:** mất khách coi trọng on-prem/air-gap (đường lui: `hybrid` của ADR-0019 nếu thị trường đòi). "Không bịa số" giữ nguyên từ ADR-0006 — chỉ bỏ vế chủ quyền.
- **Bất biến:** #1/#2/#3 GIỮ; #4 đổi theo ADR-0019.

## Tham chiếu
ADR-0006, ADR-0016, ADR-0019; COUNCIL-REVIEW-2026-07-12.md.
