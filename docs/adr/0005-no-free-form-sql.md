# 0005. Không sinh SQL tự do trên ERP — semantic layer / view kế toán đã duyệt

- **Trạng thái:** Accepted
- **Ngày:** 2026-06-08
- **Người quyết định:** Đội dự án BRAVO AI Copilot
- **Liên quan:** [ADR-0004](0004-llm-never-computes-numbers.md), [ARCHITECTURE](../ARCHITECTURE.md), [SECURITY-RLS](../SECURITY-RLS.md), [findings/C](../research/findings/C-deployment-pitfalls.md), agent `erp-accounting-expert`.

## Bối cảnh (Context)
Năng lực "hỏi-đáp số liệu tài chính" hấp dẫn nhất khi để LLM tự sinh SQL từ câu hỏi (NL2SQL). Deep research (kiểm chứng) cho thấy điều này **rất rủi ro trên ERP thực**:
- **Spider 2.0 (ICLR 2025):** code agent SOTA (o1-preview) chỉ giải **21.3%** tác vụ text-to-SQL **doanh nghiệp thực** (DB 1000+ cột, SQL 100+ dòng), so với **91.2%** trên benchmark học thuật Spider 1.0.
- SQL sai → số liệu sai (join sai, đếm trùng, lọc sai kỳ) **vẫn kèm "trích dẫn"** → ảo tưởng nguy hiểm hơn vì trông đáng tin.
- BRAVO ERP (.NET/SQL Server) có ngữ nghĩa phức tạp: kỳ khoá sổ, đơn vị cơ sở, định khoản — LLM tự sinh SQL dễ hiểu sai ngữ nghĩa.

Đồng thời, SQL tự do tới CSDL gốc mâu thuẫn nguyên tắc **non-invasive** và mở rộng bề mặt tấn công.

## Các phương án đã cân nhắc (Options)
1. **NL2SQL tự do tới CSDL ERP.** Linh hoạt tối đa nhưng độ chính xác sụp đổ (21%), rủi ro ngữ nghĩa + bảo mật. Bị loại.
2. **NL2SQL có kiểm chứng** (validate schema, chống đếm trùng) trên CSDL gốc. Tốt hơn nhưng vẫn chạm CSDL gốc, vẫn rủi ro ngữ nghĩa kế toán.
3. **Semantic layer / bộ view & API tổng hợp đã được kế toán duyệt.** LLM chỉ chọn trong tập truy vấn/metric đã định nghĩa & kiểm thử, có tham số (kỳ, đơn vị, phòng ban). Không tự viết SQL thô.

## Quyết định (Decision)
Chọn **Phương án 3**:

> Agent **không sinh SQL tự do** tới CSDL ERP. Mọi truy cập số liệu đi qua một **semantic layer**: tập **view/API/metric tham số hoá đã được kế toán định nghĩa, duyệt và kiểm thử** (vd `doanh_thu_thuan(kỳ, đơn_vị)`, `cong_no_qua_han(...)`). LLM chỉ **chọn metric + điền tham số**; lớp này là nơi nhúng RLS (lọc scope ở SQL) và đảm bảo ngữ nghĩa kế toán đúng (kỳ khoá sổ, đơn vị, nợ/có). SQL tự do (nếu có sau này) chỉ ở chế độ chuyên gia, read-only, ngoài đường chạy mặc định.

## Hệ quả (Consequences)
- Tích cực: độ chính xác & đúng ngữ nghĩa cao hơn nhiều; là nơi tự nhiên để cưỡng chế RLS + non-invasive; metric duyệt sẵn → kiểm thử & tin cậy được; phối hợp [ADR-0004] (tầng tính toán deterministic chính là các metric này).
- Tiêu cực/nợ: phải **xây & bảo trì danh mục metric/view** cùng kế toán BRAVO; câu hỏi ngoài danh mục → "chưa hỗ trợ" thay vì trả lời tự do (đánh đổi chấp nhận được). Cần quy trình thêm metric mới.
- Ảnh hưởng nguyên tắc bất biến: củng cố #2 (non-invasive), #3 (đúng số liệu); semantic layer là điểm cưỡng chế #1 (RLS).
- Việc tiếp: cùng `erp-accounting-expert` định nghĩa danh mục metric MVP; xác nhận BRAVO ERP cung cấp view/API đọc tới đâu (VISION §8).

## Tham chiếu
[findings/C §4](../research/findings/C-deployment-pitfalls.md). Spider 2.0 (arxiv 2411.07763). Liên kết [ADR-0004](0004-llm-never-computes-numbers.md).
