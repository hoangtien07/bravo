# 0004. LLM không bao giờ tự tính số liệu — tầng tính toán deterministic

- **Trạng thái:** Accepted
- **Ngày:** 2026-06-08
- **Người quyết định:** Đội dự án BRAVO AI Copilot
- **Liên quan:** [VISION §2 nguyên tắc #3](../VISION.md), [ARCHITECTURE](../ARCHITECTURE.md), [findings/B](../research/findings/B-academic-technical.md), [findings/C](../research/findings/C-deployment-pitfalls.md). Củng cố [ADR-0003](0003-hybrid-llm-strategy.md).

## Bối cảnh (Context)
Nguyên tắc bất biến #3 ("zero-hallucination số liệu") ban đầu chỉ yêu cầu *trích dẫn nguồn*. Deep research (đã kiểm chứng) cho thấy chừng đó **chưa đủ**:
- **FAITH (ICAIF 2025):** độ chính xác của LLM **sụt hệ thống khi cần tính toán**; ở phép tính đa biến nhiều model về **~0%** — kể cả Llama-3.3-**70B**. Qwen-3-8B chỉ **30.6%** overall (Claude-Sonnet-4 95.6%).
- **FailSafeQA (Writer 2025):** ngay model bền vững nhất (o3-mini) vẫn **bịa số 41%** dưới input nhiễu.
- BRAVO chạy **LLM cục bộ nhỏ (Qwen-2.5)** mặc định → nằm đúng vùng rủi ro cao nhất.

Kết luận: nếu để LLM tự cộng/trừ/tính tỉ lệ/suy luận đa biến trên số liệu kế toán, sai số là **không tránh khỏi và phổ biến** — phá huỷ niềm tin, rủi ro chí mạng cho sản phẩm tài chính.

## Các phương án đã cân nhắc (Options)
1. **Để LLM tự tính, kèm trích dẫn.** Đơn giản nhưng *sai số liệu thường xuyên* (bằng chứng trên). Bị loại.
2. **Dùng model lớn hơn/cloud cho phép tính.** Cải thiện nhưng vẫn không tuyệt đối (95.6% ≠ 100%), và mâu thuẫn chủ quyền dữ liệu nếu gửi số liệu nhạy ra cloud.
3. **Tầng tính toán deterministic: số do SQL/ERP tính, LLM chỉ điều phối + diễn giải + trích dẫn.** Số liệu chính xác tuyệt đối (do máy tính, không do model "đoán").

## Quyết định (Decision)
Chọn **Phương án 3**, nâng nguyên tắc #3 thành luật kiến trúc:

> **LLM bị CẤM tự tạo ra con số.** Mọi giá trị số (tổng, tỉ lệ, chênh lệch, công nợ, lãi/lỗ...) phải được **tính bằng truy vấn/biểu thức deterministic ở tầng SQL/ERP** (hoặc thư viện tính toán xác định). LLM chỉ được: (a) hiểu câu hỏi → chọn truy vấn/tham số; (b) **diễn giải** kết quả đã tính sẵn; (c) **trích dẫn** nguồn tới ô/dòng/chứng từ. Nếu một con số xuất hiện trong câu trả lời mà không truy được về một phép tính deterministic có nguồn → đó là lỗi nghiêm trọng.

Hệ quả triển khai: cần một **Calculation/Aggregation layer** giữa agent và dữ liệu (truy vấn tham số hoá / API tổng hợp đã duyệt), và **cơ chế từ chối** ("không đủ dữ liệu") thay vì bịa (học Trust-Align, đã đánh giá trên Qwen-2.5).

## Hệ quả (Consequences)
- Tích cực: số liệu chính xác tuyệt đối; biến nguyên tắc zero-hallucination thành cơ chế kỹ thuật đo được; cho phép dùng Qwen-2.5 nhỏ an toàn (vì model không gánh phần tính toán).
- Tiêu cực/nợ: phải xây tầng tính toán + bộ truy vấn/aggregation duyệt sẵn; giảm "độ linh hoạt" hỏi tự do (đánh đổi chấp nhận được — đúng đắn quan trọng hơn linh hoạt với số liệu tài chính).
- Ảnh hưởng nguyên tắc bất biến: **củng cố #3** (zero-hallucination), tương thích #2 (non-invasive — chỉ đọc), #4 (giữ số liệu nhạy on-prem). Liên kết chặt [ADR-0005](0005-no-free-form-sql.md).
- Việc tiếp: định nghĩa tầng tính toán + bộ eval đo "mọi số có nguồn".

## Tham chiếu
[findings/B §0](../research/findings/B-academic-technical.md), [findings/C §3](../research/findings/C-deployment-pitfalls.md). FAITH (arxiv 2508.05201), FailSafeQA (arxiv 2502.06329), Trust-Align (arxiv 2409.11242).
