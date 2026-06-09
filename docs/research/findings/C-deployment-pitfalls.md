# Findings C — Lỗi & Khó khăn triển khai thực tế (Deep Research)

> Deep research, kiểm chứng 3 phiếu. Chạy 2026-06-08. Run `wf_e16fc210-0a0`. **23/25 khẳng định qua kiểm chứng** (nguồn primary chất lượng cao: Gartner, Deloitte, OWASP, arXiv/ICLR).

## 0. Hai phát hiện đổi định vị (quan trọng)

> **(a) On-prem KHÔNG rẻ hơn — đừng bán bằng "tiết kiệm chi phí".** Break-even của LLM on-prem so với API cloud giá rẻ (Gemini 2.5 Pro) có thể **5–9 năm**. → Lý do chọn Qwen-2.5 cục bộ **phải là chủ quyền dữ liệu**, không phải chi phí. (arXiv 2509.18101). *Hai claim "on-prem rẻ/break-even nhanh" đã BỊ BÁC (1-2, 0-3) — không dùng.*

> **(b) "Draft + người duyệt" của BRAVO là tính năng quản trị dẫn đầu thị trường.** Deloitte 2026: chỉ **21%** tổ chức có mô hình quản trị agentic AI trưởng thành, trong khi 74% định dùng agent đáng kể vào 2027. → Nguyên tắc "không xâm lấn" (read-only + nháp chờ duyệt) chính là cơ chế oversight mà **79% thị trường còn thiếu**.

## 1. Vì sao pilot GenAI thất bại (định lượng)
- **Gartner:** ≥**30%** dự án GenAI bị bỏ sau PoC cuối 2025 (thực tế nâng ~50%), do **4 nguyên nhân gốc**: chất lượng dữ liệu kém · kiểm soát rủi ro không đủ · chi phí leo thang · **giá trị kinh doanh không rõ**. (gartner.com, 29/07/2024)
- **MIT 2025:** 95% pilot không có lợi nhuận tài chính đo được. **Deloitte 2026:** chỉ **20%** đã tăng doanh thu nhờ AI; chỉ **25%** đưa được ≥40% pilot vào production → **pilot-to-production gap là rủi ro #1**.
- → *Bài học BRAVO:* **đừng hứa doanh thu**; định vị giá trị ở **năng suất + ra quyết định** (Deloitte: efficiency 66%, decision-making 60%) với **chi phí dự đoán được**. Mỗi use-case phải gắn metric đo được để né bẫy "unclear business value".

## 2. Sự cố bảo mật RAG thực tế — củng cố "non-invasive + RLS"
- **Slack AI (08/2024):** indirect prompt injection → exfiltrate API key từ private channel kẻ tấn công **không có quyền**; gốc rễ: RAG kéo nội dung từ public channel user không thuộc về, LLM không phân biệt được system prompt vs context chèn vào. (promptarmor, theregister)
- **M365 Copilot / EchoLeak (CVE-2025-32711, CVSS 9.3, zero-click):** prompt injection qua email/tài liệu → tự gọi tool tìm thêm dữ liệu nhạy → exfiltrate qua **ASCII smuggling**. Lớp lỗ hổng **tái diễn** (CVE-2026-26133). (embracethered, hackthebox)
- **OWASP LLM01:2025:** *"RAG và fine-tuning KHÔNG khử được lỗ hổng prompt injection"*; hậu quả: rò thông tin nhạy, lộ system prompt, truy cập hàm trái phép, thực thi lệnh tuỳ ý.
- → *Bài học BRAVO:* vì BRAVO ingest PDF/DOCX/Excel do người dùng tải lên = **bề mặt injection không thể khử ở tầng model** → phòng thủ ở **kiến trúc**: read-only + nháp chờ duyệt (cắt chuỗi exfiltration tự động) + **RLS SQL kiểm soát phạm vi retrieval theo quyền** (không để RAG kéo dữ liệu ngoài quyền vào context — đúng lỗi Slack).

## 3. Rủi ro số liệu sai là THẬT và phổ biến
- **FailSafeQA** (Writer/arXiv 2502.06329, 02/2025, 24 model): model bền vững nhất (**o3-mini**) vẫn **bịa số trong 41%** trường hợp dưới input nhiễu (sai chính tả, OCR lỗi, thiếu context); model tài chính chuyên biệt nhất vẫn gãy **17%**. Đánh đổi cơ bản: không model nào vừa kháng nhiễu vừa biết từ chối khi thiếu context.
- → *Bài học BRAVO:* zero-hallucination + trích dẫn + **cơ chế "từ chối" (refrain)** là **bắt buộc, không phải tuỳ chọn**. (Cộng hưởng phát hiện Track B: LLM không tự tính số.)

## 4. Tích hợp ERP legacy: text-to-SQL sụp đổ trên DB thực
- **Spider 2.0** (ICLR 2025): code agent SOTA (o1-preview) chỉ giải **21.3%** tác vụ text-to-SQL doanh nghiệp thực, so với **91.2%** trên Spider 1.0 học thuật và 73% BIRD. DB thực có 1000+ cột, SQL 100+ dòng. (arXiv 2411.07763)
- → *Bài học BRAVO:* **không để LLM tự sinh SQL tự do** trên ERP. Cần **semantic layer / view đã định nghĩa & duyệt**, ngữ nghĩa hoá schema, + RLS tầng SQL. Xác nhận khó khăn ERP legacy (ngữ nghĩa dữ liệu, kỳ khoá sổ) là rủi ro độ chính xác thật. (Cộng hưởng `erp-accounting-expert`: đọc qua view đã duyệt, không SQL tự do.)

## 5. Khó khăn riêng on-prem
- Phần cứng GPU/VRAM, vận hành, cập nhật model, throughput thấp hơn cloud; kinh tế yếu nếu mục tiêu là tiết kiệm (§0a). → cloud opt-in có kiểm soát là **van xả chi phí/chất lượng** hợp lý (khớp ADR-0003 hybrid).

## 6. ⚠️ Khoảng trống & cảnh báo
- **Toàn bộ bằng chứng là quốc tế (Mỹ/EU).** KHÔNG có nguồn về thất bại GenAI tại doanh nghiệp VN hay khung pháp lý VN (Nghị định 13/2023, Luật An ninh mạng, trách nhiệm pháp lý khi AI sai số liệu) → Track D phải lấp.
- Con số 41% (FailSafeQA) là tỷ lệ *dưới nhiễu cố ý*, không phải tỷ lệ lỗi vận hành bình thường — dùng làm bằng chứng rủi ro, không phải dự báo lỗi của BRAVO.
- COI nhẹ: FailSafeQA do Writer tạo (model họ "thắng"); Gartner là dự báo, không phải đo.

## 7. Checklist "phải làm đúng trước khi giao khách thật" (rút từ C, gắn 4 nguyên tắc)
1. RLS tầng SQL kiểm soát **phạm vi retrieval** theo quyền (chống lỗi kiểu Slack). [NT1]
2. RAG **không bao giờ** đưa chunk ngoài quyền user vào context. [NT1]
3. Tài liệu ingest được coi là **không tin cậy** (injection) — sanitize, không cho nội dung tài liệu điều khiển hành vi/tool. [NT2]
4. Mọi tác vụ ghi = **nháp chờ duyệt**, không auto-execute (cắt exfiltration/agency). [NT2]
5. LLM **không tự tính số**; số từ SQL/ERP deterministic. [NT3]
6. **Không sinh SQL tự do**; chỉ view/semantic layer đã duyệt. [NT3]
7. Mọi câu trả lời số liệu **kèm trích dẫn tới ô/dòng/chứng từ**. [NT3]
8. Cơ chế **từ chối** khi context không đủ căn cứ (không bịa). [NT3]
9. Chống exfiltration: không render link/ảnh từ nội dung không tin cậy (chống ASCII smuggling). [NT1,2]
10. Lý do on-prem = **chủ quyền dữ liệu**, truyền thông đúng (không bán bằng "rẻ hơn"). [NT4]
11. Mô hình **chi phí dự đoán được** cho khách. [NT4]
12. Mỗi use-case gắn **metric giá trị đo được** (né bẫy ROI).
13. **Bộ eval** (faithfulness/citation/refusal) chạy CI trước mỗi release.
14. Kế hoạch **pilot→production** rõ (đừng kẹt ở PoC).
15. **Audit log** mọi truy cập + mọi draft (trách nhiệm pháp lý).

## 8. 10 dấu hiệu dự án đang đi chệch
1. Bán/biện minh on-prem bằng "tiết kiệm chi phí". 2. Để LLM tự tính số liệu. 3. Để LLM sinh SQL tự do trên ERP. 4. Câu trả lời số liệu không có nguồn. 5. Không có cơ chế từ chối khi thiếu dữ liệu. 6. RAG lọc quyền *sau* khi nạp RAM (không ở SQL). 7. Tài liệu ingest được tin tưởng như lệnh. 8. Có đường auto-write vào ERP. 9. Không có bộ eval/metric giá trị. 10. Kẹt ở demo/PoC, không có lộ trình production.

## 9. Hành động ưu tiên cho BRAVO (rút từ Track C)
1. **[ĐỊNH VỊ] Sửa thông điệp on-prem:** bán bằng **chủ quyền dữ liệu**, không phải chi phí. Cập nhật VISION §3.1 + ROADMAP (mô hình giá dự đoán được). *(Quan trọng.)*
2. **[ĐỊNH VỊ] Nâng "draft+duyệt" thành điểm bán quản trị** (79% thị trường thiếu oversight agent).
3. **[BẢO MẬT] Thêm phòng thủ injection vào thiết kế** (SECURITY): tài liệu = không tin cậy, chống render link exfil, scoped retrieval. Đưa vào agent `security-rls-auditor`.
4. **[KIẾN TRÚC] Chốt "không sinh SQL tự do"** → semantic layer/view đã duyệt (cộng hưởng B + erp-accounting-expert).
5. **[GĐ0] Đưa checklist §7 + bộ eval vào ROADMAP** như cổng ra production.

---
*Phương pháp: 5 góc → 25 nguồn → 124 claim → kiểm chứng 25 → 23 xác nhận / 2 bị bác → 11 sau tổng hợp.*
