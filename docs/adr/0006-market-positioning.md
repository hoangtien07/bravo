# 0006. Định vị thị trường: "AI tài chính có chủ quyền & không bịa số"

- **Trạng thái:** Accepted (định vị làm việc — tinh chỉnh sau khảo sát hành vi mua + xác nhận pháp lý)
- **Ngày:** 2026-06-08
- **Người quyết định:** Đội dự án BRAVO AI Copilot
- **Liên quan:** [VISION §3.1](../VISION.md), [findings/A](../research/findings/A-competitive-landscape.md), [findings/D](../research/findings/D-vietnam-market-positioning.md), [findings/E](../research/findings/E-vietnam-legal.md).

## Bối cảnh (Context)
Cần một định vị phòng thủ được trên thị trường VN, dựa trên bằng chứng (deep research đã kiểm chứng), không phải phỏng đoán. Phát hiện then chốt:
- **White space đã xác nhận:** Oracle NetSuite Next, M365 Copilot Finance, SAP Joule (ERP-AI) và **MISA AVA** (đối thủ VN trực tiếp) **đều cloud-only**; không cái nào có on-prem sovereignty + RLS tầng dữ liệu + trích dẫn nguồn kế toán. MISA mạnh marketing AI nhưng **không công bố** 3 điểm đó.
- **Số liệu sai là rủi ro #1** → "không bịa số" là điểm tin cậy khác biệt.
- **Đòn bẩy pháp lý (có điều kiện):** cloud nước ngoài = chuyển dữ liệu xuyên biên giới → thêm nghĩa vụ; on-prem né lớp này (cần luật sư xác nhận chi tiết).
- **Cạm bẫy:** thị trường "đói giá trị" (50% pilot bỏ); on-prem **không rẻ hơn** → không bán bằng chi phí.

## Quyết định (Decision)
Định vị chính: **"AI tài chính có chủ quyền & không bịa số"** — kết hợp hai trụ:
1. **Chủ quyền dữ liệu (on-prem):** AI phân tích chạy *trong nhà bạn*, dữ liệu không rời mạng nội bộ; phù hợp khung pháp lý bảo vệ dữ liệu cá nhân VN (Luật 91/2025). *Bán bằng chủ quyền & tuân thủ, KHÔNG bán bằng "rẻ hơn".*
2. **Không bịa số:** mọi con số tính ở tầng deterministic, trích dẫn tới chứng từ ([ADR-0004]/[ADR-0005]).

Trụ kỹ thuật hỗ trợ: **RLS phòng ban tầng SQL** ("mỗi người chỉ thấy dữ liệu trong quyền") — không đối thủ nào có.

**Phân khúc mục tiêu ưu tiên:** DN vừa-lớn ngành tài chính/sản xuất nhạy cảm, nhiều phòng ban, đang dùng BRAVO ERP, coi trọng kiểm soát dữ liệu & độ chính xác.

**Thông điệp:**
- *Cho Ban lãnh đạo BRAVO:* "Biến tệp khách ERP hiện hữu thành dòng doanh thu AI add-on, bằng đúng thứ các ông lớn cloud và MISA không làm được: AI tài chính chạy on-prem, không bịa số, phân quyền tới từng phòng ban."
- *Cho khách hàng (CFO):* "Hỏi số liệu tài chính bằng tiếng Việt, nhận câu trả lời có dẫn chứng tới từng chứng từ — chạy hoàn toàn trong hệ thống của bạn, không đẩy dữ liệu ra cloud."

## Hệ quả (Consequences)
- Tích cực: định vị dựa trên khác biệt đã kiểm chứng + khó sao chép (đối thủ cloud không thể "bắt chước" on-prem nhanh); gắn với điểm đau thật (tin số liệu, kiểm soát dữ liệu).
- Tiêu cực/nợ: phải **chứng minh** được (demo on-prem + RLS + trích dẫn); chưa có dữ liệu hành vi mua/định giá VN → định vị còn là giả thuyết làm việc.
- Rủi ro pháp lý (đã re-verify — [findings/F](../research/findings/F-reverification.md)): đòn bẩy on-prem **CÓ THẬT nhưng HẸP** — chỉ cho dữ liệu **khách hàng/nghiệp vụ** (cloud nước ngoài = chuyển xuyên biên giới → CTIA, phạt tới 3 tỷ/5% DT). Dữ liệu **HR/lương của chính nhân viên được MIỄN** (Khoản 6 Điều 20) → **không dùng làm điểm bán**. Số điều mẫu NĐ 356/2025 vẫn cần luật sư xác nhận trước khi đưa vào tài liệu bán.
- Việc tiếp: khảo sát hành vi mua + mức sẵn-lòng-trả VN; xác nhận pháp lý; xây demo "đinh" (hỏi số liệu có trích dẫn, on-prem).

## Tham chiếu
[findings/A](../research/findings/A-competitive-landscape.md), [findings/D](../research/findings/D-vietnam-market-positioning.md), [findings/E](../research/findings/E-vietnam-legal.md), [SUMMARY](../research/findings/SUMMARY.md).
