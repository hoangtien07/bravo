# 0003. Chiến lược LLM: Hybrid — local mặc định, cloud opt-in có kiểm soát theo độ nhạy dữ liệu

- **Trạng thái:** Accepted
- **Ngày:** 2026-06-08
- **Người quyết định:** Đội dự án BRAVO AI Copilot
- **Liên quan:** [VISION.md §2, §4.3](../VISION.md), [SECURITY-RLS.md §9](../SECURITY-RLS.md), [ARCHITECTURE.md](../ARCHITECTURE.md). Thay thế giả định "offline 100% / local-only" trong brief gốc.

## Bối cảnh (Context)
Brief gốc đặt nguyên tắc "vận hành offline 100% bằng LLM cục bộ (Qwen-2.5)". Phân tích cho thấy:
- **Vì local là đúng:** chủ quyền dữ liệu (Nghị định 13/2023, Luật An ninh mạng), tệp khách air-gapped, đây là moat khó sao chép, chi phí dự đoán được.
- **Nhưng local-only có giá:** trần chất lượng thấp hơn (Qwen-2.5 32B < Opus/GPT về suy luận phức tạp); một phần khách hàng *chấp nhận* dùng cloud cho dữ liệu không nhạy cảm để đổi lấy chất lượng và sẽ thất vọng nếu bị khoá cứng vào local.

Câu hỏi nền: **local-only hay hybrid?** Quyết định này định hình tầng LLM, bảo mật, và định vị sản phẩm nên phải chốt sớm.

## Các phương án đã cân nhắc (Options)
1. **Local-only (offline 100%).** Ưu: an toàn tuyệt đối, moat rõ, đơn giản. Nhược: trần chất lượng thấp; mất phân khúc khách muốn chất lượng cao và *được phép* dùng cloud; khó cạnh tranh ở tác vụ phân tích tinh vi.
2. **Cloud-first (model ngoài là chính, local là fallback).** Ưu: chất lượng cao nhất. Nhược: **phá nguyên tắc chủ quyền dữ liệu** — loại bỏ phân khúc air-gapped (chính là tệp khách lõi của BRAVO ERP on-prem); rủi ro pháp lý. **Bị loại.**
3. **Hybrid — local mặc định + cloud opt-in có kiểm soát theo độ nhạy dữ liệu.** Sàn bắt buộc là offline 100%; cloud chỉ bật khi khách chủ động cho phép, và chỉ với *lớp dữ liệu được chính sách cho phép rời mạng*. Phục vụ cả hai phân khúc bằng một kiến trúc.

## Quyết định (Decision)
Chọn **Phương án 3 (Hybrid)**. Cụ thể:

1. **Sàn offline là bất biến.** Mọi bản triển khai *phải* chạy được 100% air-gapped với LLM cục bộ (Qwen-2.5 qua vLLM/Ollama). Đây là cấu hình mặc định, ra-khỏi-hộp.
2. **Cloud là opt-in cấp triển khai.** Admin của khách bật/tắt; mặc định TẮT. Dùng abstraction LLM kiểu OpenAI-compatible (đã có trong docsgpt) để cùng một interface chạy local hoặc cloud.
3. **Model Router cưỡng chế chính sách phát tán dữ liệu (data-egress).** Mọi lời gọi LLM đi qua một router. Router quyết định local-vs-cloud dựa trên: cấu hình (cloud bật?), **độ nhạy của dữ liệu trong ngữ cảnh** (tái dùng nhãn phòng ban/loại tri thức từ RLS), và loại tác vụ.
4. **Dữ liệu nhạy cảm bị ghim cứng ở local.** Dữ liệu kế toán/lương/HR/PII và mọi nội dung gắn nhãn nhạy cảm **không bao giờ** rời mạng — kể cả khi cloud đã bật. Chỉ lớp dữ liệu được whitelist (vd cẩm nang kỹ thuật công khai, mã lỗi) mới được phép dùng cloud.
5. **Kiểm toán + (tuỳ chọn) khử nhận dạng.** Mọi lời gọi cloud được ghi audit (lớp dữ liệu, nhà cung cấp, ai, khi nào). Có thể bật lớp redaction PII trước khi gọi cloud.

**Reframe nguyên tắc bất biến #4:** từ *"Offline 100%"* → *"Chủ quyền dữ liệu: bắt buộc có đường offline 100% được đảm bảo (mặc định); cloud chỉ opt-in có kiểm soát, dữ liệu nhạy cảm không bao giờ tự động rời mạng."* Sàn không nhân nhượng vẫn là *offline phải khả thi*; cái mở ra là *được phép dùng cloud cho dữ liệu không nhạy khi khách đồng ý*.

## Hệ quả (Consequences)
- **Tích cực:** phục vụ cả khách air-gapped lẫn khách chấp nhận cloud bằng một sản phẩm; nâng trần chất lượng nơi được phép; moat vẫn nguyên (đối thủ cloud không có nổi *sàn offline được đảm bảo*); định giá linh hoạt (gói offline-only vs gói hybrid).
- **Tiêu cực / nợ kỹ thuật:**
  - **Bề mặt tấn công mới:** đường ra cloud là nơi dữ liệu có thể rò. Phải phân loại độ nhạy dữ liệu *chính xác* và kiểm toán nghiêm — `security-rls-auditor` phải duyệt mọi đường egress.
  - Cần xây **phân loại độ nhạy** (sensitivity classification) cho tài liệu/ngữ cảnh — gắn vào pipeline ingestion + RLS.
  - Router thêm độ phức tạp; cần fail-safe: nếu không xác định được độ nhạy ⇒ mặc định local (fail-closed).
- **Ảnh hưởng 4 nguyên tắc bất biến:** reframe #4 (không yếu đi — sàn offline giữ nguyên); **củng cố** kỷ luật bảo mật vì giờ có chính sách egress tường minh thay vì giả định ngầm "không có cloud".
- **Việc tiếp:** ADR con — danh sách nhà cung cấp cloud được hỗ trợ; lược đồ phân loại độ nhạy; cơ chế cấu hình policy theo khách; có/không lớp redaction PII.

## Tham chiếu
Abstraction LLM đa nhà cung cấp: [docsgpt-notes §5](../reference/docsgpt-notes.md). Chính sách egress chi tiết: [SECURITY-RLS.md §9](../SECURITY-RLS.md). Thảo luận gốc dẫn tới quyết định này nằm trong lịch sử hội thoại dự án.
