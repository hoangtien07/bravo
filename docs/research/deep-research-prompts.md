# Deep Research Prompts — BRAVO AI Copilot

> Bộ prompt để nghiên cứu sâu nhằm **cải thiện dự án, tránh lỗi triển khai thực tế, tìm điểm mạnh, và định vị BRAVO AI trên thị trường Việt Nam**. Mỗi prompt tự-chứa (có sẵn khối bối cảnh) → dán thẳng vào công cụ deep research bất kỳ.

## Cách dùng
1. **Chạy bằng Claude:** gọi skill `/deep-research` rồi dán một prompt bên dưới.
2. **Công cụ ngoài** (ChatGPT/Gemini/Perplexity Deep Research): dán nguyên prompt (đã gồm khối bối cảnh).
3. **Thứ tự đề xuất:** chạy 4 prompt chuyên sâu (A→D) để có chiều sâu, rồi dùng Master prompt để tổng hợp. Hoặc chạy Master nếu chỉ cần một báo cáo gộp.
4. **Đưa kết quả về dự án:** mỗi phát hiện lớn → cập nhật [VISION.md](../VISION.md) / tạo [ADR](../adr/) / thêm rủi ro vào [VISION §7](../VISION.md). Lưu báo cáo vào `docs/research/findings/`.

> ⚠️ Yêu cầu mọi prompt: **trích dẫn nguồn** cho từng khẳng định (link + ngày), ưu tiên nguồn ≤ 24 tháng cho thị trường/sản phẩm và nguồn peer-reviewed cho học thuật, và **phân biệt rõ sự thật có dẫn chứng vs suy luận**.

---

## KHỐI BỐI CẢNH (đã nhúng sẵn trong mỗi prompt — đây là bản gốc để bạn chỉnh)

> **Dự án:** BRAVO AI Copilot — lớp AI hội thoại + phân tích tài chính đặt trên hệ ERP BRAVO (nền .NET / SQL Server), cho doanh nghiệp Việt Nam. **Bốn nguyên tắc:** (1) **RLS phòng ban** ép buộc ở tầng SQL — nhân viên chỉ thấy dữ liệu trong quyền; (2) **không xâm lấn** — chỉ đọc ERP qua REST read-only, mọi tác vụ ghi chỉ tạo *bản nháp chờ người duyệt*; (3) **zero-hallucination số liệu** — mọi câu trả lời có số liệu phải kèm trích dẫn nguồn (trang/ô/chứng từ); (4) **chủ quyền dữ liệu (hybrid)** — mặc định chạy offline/on-prem bằng LLM cục bộ (Qwen-2.5), cloud chỉ opt-in có kiểm soát, dữ liệu nhạy không rời mạng. **Năng lực:** RAG đa định dạng (PDF/DOCX/Excel, bóc tách bảng), tra cứu tri thức nội bộ (MVP); hỏi-đáp số liệu tài chính, phát hiện bất thường, soạn nháp chứng từ (nâng cao). **Khách hàng:** tệp doanh nghiệp/SME đang dùng BRAVO ERP tại Việt Nam.

---

## MASTER PROMPT (báo cáo tổng hợp)

```
Bạn là nhà phân tích chiến lược sản phẩm AI cho doanh nghiệp. Hãy thực hiện một nghiên cứu sâu, có dẫn chứng, phục vụ việc cải thiện và định vị sản phẩm dưới đây.

[DÁN KHỐI BỐI CẢNH Ở TRÊN VÀO ĐÂY]

MỤC TIÊU: (a) học từ các sản phẩm AI doanh nghiệp tương tự để cải thiện thiết kế; (b) nhận diện các lỗi & khó khăn thực tế khi triển khai để né tránh; (c) tìm điểm mạnh khác biệt; (d) định vị BRAVO AI trên thị trường Việt Nam sao cho có giá trị thực cho công ty và khách hàng.

Hãy trả lời 4 phần, mỗi khẳng định có trích dẫn nguồn (link + ngày):

PHẦN 1 — BẢN ĐỒ CẠNH TRANH. So sánh các nhóm: (i) trợ lý tri thức doanh nghiệp/RAG (Glean, Onyx/Danswer, Dust, Sana, Writer, Cohere North, Microsoft 365 Copilot, ChatGPT Enterprise, Google Agentspace, Guru, Hebbia, Vectara); (ii) AI nhúng trong ERP (SAP Joule, Oracle/NetSuite AI, Microsoft Dynamics 365 Copilot, Zoho Zia, Sage Copilot, Infor); (iii) đối thủ Việt Nam (MISA AVA/AMIS, FPT.AI, Viettel AI, VNPT AI, VinAI, Zalo AI, Base.vn, KiotViet, Bizzi). Với mỗi sản phẩm đáng chú ý: phân khúc, mô hình triển khai (cloud/on-prem), mô hình phân quyền dữ liệu, tính năng lõi, giá, điểm mạnh/yếu, và "BRAVO nên sao chép / tránh / khác biệt điều gì".

PHẦN 2 — TRI THỨC HỌC THUẬT & KỸ THUẬT. Tổng hợp nghiên cứu mới nhất về: RAG tài chính & hỏi-đáp tài liệu (FinQA, TAT-QA), bóc tách & QA bảng biểu, giảm ảo tưởng + grounding + attribution/citation, đánh giá RAG (RAGAS/ARES), retrieval có kiểm soát quyền (permission-aware / secure / multi-tenant RAG), NL2SQL an toàn cho dữ liệu doanh nghiệp (Spider, BIRD), bộ nhớ agent (MemGPT), LLM nhỏ/on-prem & lượng tử hoá, và LLM tiếng Việt (PhoGPT, Vistral, hiệu năng Qwen trên tiếng Việt). Rút ra "bài học áp dụng được cho BRAVO" cho mỗi chủ đề.

PHẦN 3 — LỖI & KHÓ KHĂN TRIỂN KHAI THỰC TẾ. Vì sao nhiều dự án GenAI/RAG doanh nghiệp thất bại khi lên production (dẫn báo cáo Gartner/McKinsey/MIT và case thực tế): chất lượng dữ liệu, quản trị, độ tin cậy/ảo tưởng trong tài chính, chi phí & độ trễ on-prem, bảo mật/rò dữ liệu qua LLM, sự chấp nhận của người dùng, trách nhiệm pháp lý. Mỗi khó khăn kèm "cách BRAVO phòng tránh".

PHẦN 4 — THỊ TRƯỜNG & ĐỊNH VỊ VIỆT NAM. Quy mô & mức độ ứng dụng AI trong doanh nghiệp/SME VN; khung pháp lý chủ quyền dữ liệu (Nghị định 13/2023 PDPD, Nghị định 53/2022, Luật An ninh mạng, dự thảo Luật Bảo vệ dữ liệu cá nhân, quy định hoá đơn điện tử/kế toán); hành vi mua của doanh nghiệp VN (ai quyết định, ngân sách, điều gì thuyết phục); benchmark giá cho AI add-on tại VN. Kết luận: đề xuất 2–3 định vị khả thi cho BRAVO AI dựa trên điểm mạnh khác biệt (ERP-native, RLS, chủ quyền dữ liệu on-prem, trích dẫn nguồn, tiếng Việt) so với khoảng trống đối thủ chưa lấp.

ĐẦU RA: báo cáo có cấu trúc theo 4 phần; mỗi phần kết bằng "Top 3 hành động cho BRAVO". Cuối báo cáo: một bảng tổng hợp "10 khuyến nghị ưu tiên" (xếp theo tác động × tính khả thi) và "5 rủi ro lớn nhất cần né". Ưu tiên nguồn tiếng Anh (học thuật/ngành) và tiếng Việt (thị trường/pháp lý). Nêu rõ chỗ bằng chứng yếu hoặc mâu thuẫn.
```

---

## PROMPT A — Bản đồ cạnh tranh (chuyên sâu)

```
Bạn là chuyên gia phân tích cạnh tranh phần mềm doanh nghiệp. Nghiên cứu sâu, có dẫn chứng, về các sản phẩm AI hội thoại/RAG cho doanh nghiệp tương tự dự án dưới đây — để tôi học điểm mạnh, tránh điểm yếu, và tìm khác biệt.

[DÁN KHỐI BỐI CẢNH]

YÊU CẦU:
1. Lập danh mục các đối thủ theo 3 nhóm: (A) trợ lý tri thức doanh nghiệp/enterprise RAG; (B) AI nhúng trong ERP/kế toán; (C) nhà cung cấp Việt Nam. BẮT BUỘC phủ tối thiểu: Glean, Onyx (Danswer), Dust, Sana, Writer, Microsoft 365 Copilot, ChatGPT Enterprise, Google Agentspace, Hebbia; SAP Joule, Oracle/NetSuite AI, Microsoft Dynamics 365 Copilot, Zoho Zia, Sage Copilot; và VIỆT NAM: MISA AVA/AMIS, FPT.AI, Viettel AI, VNPT AI, VinAI, Zalo AI, Base.vn, KiotViet, Bizzi. Bổ sung đối thủ khác nếu phát hiện.
2. Với MỖI sản phẩm đáng chú ý, lập hồ sơ: phân khúc khách hàng; mô hình triển khai (SaaS cloud / private cloud / on-prem / air-gapped); có hỗ trợ LLM cục bộ không; mô hình phân quyền dữ liệu (có RLS/permission-aware retrieval không); tính năng lõi; cách xử lý trích dẫn/chống ảo tưởng; tích hợp ERP/kế toán; mô hình & mức giá (nếu công khai); điểm mạnh; điểm yếu/khiếu nại của người dùng (từ review G2/Reddit/diễn đàn).
3. ĐẶC BIỆT về MISA (đối thủ kế toán/ERP VN trực tiếp): phân tích kỹ AI của MISA — làm được gì, hạn chế, cách định vị, giá — và BRAVO cần khác biệt thế nào.
4. Lập **bảng so sánh** các đối thủ theo các trục quan trọng với BRAVO: on-prem/offline, RLS phòng ban, trích dẫn nguồn số liệu, bóc tách bảng tài chính, tiếng Việt, tích hợp ERP sâu, giá.

ĐẦU RA: hồ sơ từng đối thủ + bảng so sánh + mục "Khoảng trống thị trường BRAVO có thể chiếm" + "Top 5 điều nên sao chép" + "Top 5 sai lầm của đối thủ nên tránh". Mọi khẳng định có nguồn (link + ngày).
```

---

## PROMPT B — Nghiên cứu học thuật & kỹ thuật (chuyên sâu)

```
Bạn là nhà nghiên cứu ML/NLP. Khảo sát tài liệu học thuật & kỹ thuật mới nhất (ưu tiên peer-reviewed và preprint arXiv ≤ 24 tháng) cho các chủ đề lõi của dự án dưới đây, rút ra bài học áp dụng được.

[DÁN KHỐI BỐI CẢNH]

CÁC CHỦ ĐỀ (mỗi chủ đề: tổng hợp 3–6 công trình/benchmark tiêu biểu + bài học cho BRAVO):
1. RAG cho tài chính & hỏi-đáp tài liệu doanh nghiệp (FinQA, TAT-QA, DocFinQA, financial document understanding).
2. Bóc tách & hỏi-đáp BẢNG BIỂU (table extraction, table-aware RAG, TableLlama, table QA) — cốt lõi cho số liệu kế toán.
3. Chống ảo tưởng: grounding, faithfulness, attribution/citation, self-checking; cách ĐO (RAGAS, ARES, faithfulness metrics).
4. Retrieval có kiểm soát quyền: permission-aware / access-controlled / secure / multi-tenant RAG; rủi ro rò dữ liệu qua RAG/LLM.
5. NL2SQL an toàn cho doanh nghiệp (Spider, BIRD); ràng buộc & guardrail để không truy vấn sai/đếm trùng số liệu tài chính.
6. Bộ nhớ agent & quản lý ngữ cảnh dài (MemGPT/Letta và kế thừa); agent gọi API có phê duyệt (human-in-the-loop).
7. LLM nhỏ/on-prem cho doanh nghiệp: lượng tử hoá (GGUF/AWQ), đánh đổi chất lượng/chi phí, phục vụ bằng vLLM/Ollama.
8. NLP & LLM TIẾNG VIỆT: PhoGPT, Vistral, VBD-LLaMA, hiệu năng Qwen-2.5 trên tiếng Việt; embedding & OCR tiếng Việt; benchmark tiếng Việt.

ĐẦU RA: với mỗi chủ đề — tóm tắt hiện trạng, kỹ thuật/benchmark nổi bật (kèm link), và "Khuyến nghị kỹ thuật cụ thể cho BRAVO". Cuối: danh sách "kỹ thuật nên áp dụng ngay" vs "nên theo dõi", và các cạm bẫy kỹ thuật đã được chứng minh.
```

---

## PROMPT C — Lỗi & khó khăn triển khai thực tế (chuyên sâu)

```
Bạn là cố vấn triển khai AI doanh nghiệp. Nghiên cứu sâu các nguyên nhân thất bại và khó khăn THỰC TẾ khi đưa trợ lý AI/RAG vào production trong doanh nghiệp, để dự án dưới đây né tránh.

[DÁN KHỐI BỐI CẢNH]

YÊU CẦU:
1. Vì sao phần lớn pilot GenAI/RAG doanh nghiệp KHÔNG lên được production (dẫn báo cáo Gartner, McKinsey, MIT, Deloitte và case thực tế). Phân loại nguyên nhân: dữ liệu (chất lượng, quyền, silo), kỹ thuật (ảo tưởng, độ chính xác, độ trễ, chi phí), tổ chức (chấp nhận của người dùng, change management, ROI không rõ), bảo mật & pháp lý (rò dữ liệu qua LLM, prompt injection, trách nhiệm khi AI sai số liệu).
2. Các SỰ CỐ thực tế đáng học: AI trả lời sai số liệu/tài chính gây hậu quả; rò dữ liệu nhạy qua chatbot doanh nghiệp; tấn công prompt injection/exfiltration trong RAG nội bộ.
3. Khó khăn riêng của ON-PREM/offline LLM: phần cứng (GPU/VRAM), vận hành, cập nhật model, throughput, so với cloud.
4. Khó khăn riêng của tích hợp với ERP/hệ kế toán legacy (.NET/SQL Server): API hạn chế, ngữ nghĩa dữ liệu, kỳ khoá sổ, độ chính xác.

ĐẦU RA: bảng "Khó khăn → Bằng chứng/nguồn → Mức độ phổ biến → Cách BRAVO phòng tránh (gắn với 4 nguyên tắc)". Cuối: "Checklist 15 điều phải làm đúng trước khi đưa BRAVO AI cho khách thật" và "10 dấu hiệu cảnh báo dự án đang đi chệch". Mọi khẳng định có nguồn.
```

---

## PROMPT D — Thị trường & định vị Việt Nam (chuyên sâu)

```
Bạn là chuyên gia chiến lược thị trường phần mềm B2B tại Việt Nam. Nghiên cứu sâu, có dẫn chứng, để định vị sản phẩm dưới đây sao cho có giá trị thực cho công ty (BRAVO) và khách hàng doanh nghiệp Việt.

[DÁN KHỐI BỐI CẢNH]

YÊU CẦU:
1. THỊ TRƯỜNG: quy mô & tốc độ ứng dụng AI trong doanh nghiệp/SME Việt Nam; ngành nào đang dẫn đầu; mức độ trưởng thành dữ liệu; thái độ với AI và với on-prem vs cloud.
2. PHÁP LÝ & CHỦ QUYỀN DỮ LIỆU (rất quan trọng cho định vị): Nghị định 13/2023/NĐ-CP (bảo vệ dữ liệu cá nhân), Nghị định 53/2022, Luật An ninh mạng, dự thảo Luật Bảo vệ dữ liệu cá nhân (2024–2025), quy định kế toán/hoá đơn điện tử (Thông tư 200, Nghị định về hoá đơn). Các quy định này tạo lợi thế gì cho giải pháp on-prem/offline như BRAVO?
3. HÀNH VI MUA: ai ra quyết định mua phần mềm AI trong doanh nghiệp VN (CFO/CIO/IT/chủ DN)? Chu kỳ bán, ngân sách điển hình, rào cản, điều gì thật sự thuyết phục? Vai trò của niềm tin, bảo mật, tham chiếu khách hàng.
4. ĐỊNH GIÁ: benchmark cách định giá AI add-on / module trong phần mềm doanh nghiệp VN và khu vực (per-user, per-site, theo tính năng); mức khách VN sẵn sàng trả.
5. ĐỊNH VỊ: dựa trên điểm mạnh khác biệt của BRAVO (ERP-native, RLS phòng ban, chủ quyền dữ liệu on-prem, trích dẫn nguồn kế toán, tiếng Việt) và khoảng trống đối thủ (đặc biệt MISA) chưa lấp — đề xuất 2–3 phương án định vị, mỗi phương án kèm thông điệp giá trị (value proposition), phân khúc mục tiêu, và lý do thắng.

ĐẦU RA: báo cáo theo 5 mục; kết bằng "3 định vị đề xuất (so sánh)", "thông điệp 1 câu cho Ban lãnh đạo BRAVO", và "thông điệp 1 câu cho khách hàng (CFO)". Mọi khẳng định có nguồn (ưu tiên nguồn tiếng Việt cho thị trường/pháp lý).
```

---

## Phụ lục — Từ khoá tìm kiếm gợi ý (để công cụ không bỏ sót)
- **Đối thủ:** `MISA AVA`, `MISA AMIS AI`, `Glean enterprise search`, `Onyx Danswer open source RAG`, `Dust AI agents`, `SAP Joule`, `Microsoft 365 Copilot enterprise`, `Zoho Zia`, `FPT.AI`, `Viettel AI`, `Base.vn AI`, `KiotViet AI`, `Bizzi AI accounting`.
- **Học thuật:** `enterprise RAG survey`, `financial document QA FinQA TAT-QA`, `table extraction RAG`, `RAG hallucination faithfulness RAGAS`, `access control aware retrieval RAG`, `text-to-SQL BIRD benchmark`, `MemGPT agent memory`, `quantized LLM on-prem enterprise`, `PhoGPT Vistral Vietnamese LLM`, `Qwen2.5 Vietnamese evaluation`.
- **Triển khai:** `why enterprise GenAI pilots fail production`, `MIT GenAI divide report`, `RAG data leakage prompt injection enterprise`, `LLM hallucination finance incident`.
- **Thị trường/pháp lý VN:** `Nghị định 13/2023 bảo vệ dữ liệu cá nhân`, `Vietnam data localization Decree 53`, `Luật Bảo vệ dữ liệu cá nhân dự thảo`, `AI adoption Vietnam SME enterprise`, `Vietnam B2B SaaS pricing AI`.

## Đầu ra mong muốn (chung)
- Báo cáo có dẫn chứng, phân biệt sự thật vs suy luận, nêu chỗ bằng chứng yếu.
- Mỗi prompt kết bằng danh sách **hành động ưu tiên cho BRAVO** — để đưa thẳng vào [VISION.md](../VISION.md), [ROADMAP.md](../ROADMAP.md), hoặc [ADR mới](../adr/).
