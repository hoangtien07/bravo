# Findings B — Học thuật & Kỹ thuật (Deep Research)

> Deep research, kiểm chứng 3 phiếu. Chạy 2026-06-08. Run `wf_de65793b-74d`. **23/25 khẳng định qua kiểm chứng** (chất lượng cao — phần lớn nguồn peer-reviewed ACL/NAACL/EACL/EMNLP/NeurIPS/ICAIF/ICLR).

## 0. 🚨 PHÁT HIỆN QUAN TRỌNG NHẤT — ảnh hưởng kiến trúc

> **LLM cục bộ nhỏ KHÔNG đáng tin cho phép tính tài chính. Phải tính số liệu DETERMINISTIC ở tầng SQL/ERP; LLM chỉ diễn giải kết quả đã tính sẵn và trích dẫn nguồn.**

Bằng chứng (FAITH, ICAIF 2025 — benchmark che số trong 10-K SEC thật):
- Độ chính xác **sụt hệ thống khi cần tính toán**; ở **Multivariate Calculation nhiều model về ~0%** — kể cả Llama-3.3-**70B**, Qwen-3-8B, Gemma-3-27B.
- Khoảng cách năng lực khổng lồ: Claude-Sonnet-4 **95.6%** vs **Qwen-3-8B 30.6%**, Llama-3.3-70B 37.0% (Qwen-3-32B 73.9%, GPT-4.1-mini 88.2%).

→ **Hệ quả cho BRAVO (đề xuất nâng nguyên tắc #3):** biến "zero-hallucination số liệu" từ khẩu hiệu thành **luật kiến trúc**: *mọi con số đến từ truy vấn/được tính ở tầng dữ liệu; LLM bị cấm tự cộng/trừ/tính tỉ lệ/suy luận đa biến.* Đây là cách duy nhất để Qwen-2.5 cục bộ an toàn với số liệu kế toán. (Nguồn: arxiv.org/html/2508.05201)

## 1. Hỏi-đáp tài chính trên tài liệu thật vẫn là bài toán mở
- **TAT-QA** (ACL 2021, 16.552 câu, ngữ cảnh lai bảng+văn bản): model tốt nhất lúc công bố (TAGOP) chỉ **58.0% F1** vs chuyên gia **90.8%**. (arxiv 2105.07624)
- **DocFinQA** (ACL 2024): mở rộng FinQA từ <700 từ → **~123.000 từ** ngữ cảnh; lỗi GPT-4 **tăng gấp đôi**. → Tài liệu dài phải dựa vào **retrieval chính xác (chunk + metadata)**, không nhồi cả tài liệu; long-context KHÔNG phải lời giải. (arxiv 2401.06915)
- *Bài học:* tài chính tiếng Việt sẽ còn khó hơn benchmark tiếng Anh — đừng kỳ vọng LLM tự suy luận số từ tài liệu thô.

## 2. Bóc tách & hỏi-đáp BẢNG = điểm gãy then chốt cho số liệu kế toán
- **MultiFinRAG** (preprint 2025): trên câu hỏi BẢNG đạt **69.4%** vs **5.6%** của text-only RAG cùng model → trích xuất bảng đa phương thức là *quyết định*. (Caveat: benchmark tự dựng, chưa peer-review, vote 2-1/3-0.) (arxiv 2506.20821)
- **TableRAG** (NeurIPS 2024): truy hồi **schema (tên cột) + cell** thay vì serialize cả bảng → giảm prompt, giảm mất mát, tránh positional bias. (Claim "SOTA" bị bác 1-2 — coi là kiến trúc hợp lý, không vô địch.) (arxiv 2410.04739)
- **TableLlama** (NAACL 2024): model bảng nhỏ giúp tổng quát hoá (+5–44 điểm out-of-domain) **nhưng KHÔNG thay thế hệ chuyên biệt** (claim thay-thế bị bác **0-3**). → Đừng tin một model nhỏ tự xử mọi tác vụ bảng.
- *Bài học BRAVO:* pipeline bóc tách bảng (Docling) phải là **hạng nhất**; với bảng/ SQL lớn dùng retrieval schema+cell; text-only RAG sẽ thất bại trên số liệu kế toán.

## 3. Đo lường chống-ảo-tưởng đã chín muồi — áp dụng ngay
- **RAGAS** (EACL 2024): đánh giá RAG **reference-free** 3 chiều (context relevance · faithfulness · answer relevance) → vòng eval tự động liên tục, tập trung **Faithfulness**. (aclanthology 2024.eacl-demo.16)
- **Trust-Score / Trust-Align** (ICLR 2025 Oral): căn chỉnh LLM để **TỪ CHỐI đúng cách khi thiếu căn cứ** + trích dẫn chất lượng; LLaMA-3-8B+Trust-Align vượt baseline FRONT (+12.6→+36). **Đã đánh giá cả dòng Qwen-2.5** (model của BRAVO). → Căn chỉnh model cục bộ để *nói "không đủ dữ liệu"* khi RLS lọc hết / retrieval yếu, thay vì bịa. (arxiv 2409.11242)
- **FaithJudge / FAITH** (EMNLP/ICAIF 2025): LLM-as-judge đo faithfulness (84% balanced acc) + benchmark ảo tưởng bảng tài chính. *Caveat:* judge mạnh thường là cloud → chỉ gửi dữ liệu phi nhạy/synthetic ra cloud.
- *Bài học BRAVO:* xây **benchmark nội bộ kiểu FAITH (masked-span) trên báo cáo tài chính tiếng Việt** + dùng RAGAS/Trust-Score trong CI trước khi tin bất kỳ con số nào.

## 4. Khoảng trống (KHÔNG có claim kiểm chứng — cần khảo sát bổ sung)
Track B **không** phủ được 4 chủ đề (tìm kiếm trả về nguồn nhưng không claim nào sống sót kiểm chứng):
- **Permission-aware / multi-tenant RAG & rò dữ liệu qua embedding/cache** — cốt lõi cho RLS của BRAVO. (Có nguồn chưa khai thác: syssec...pedro_icse25.pdf, arxiv 2509.20324.)
- **NL2SQL an toàn (Spider/BIRD) + guardrail chống đếm trùng/join sai** — rủi ro cốt lõi: LLM sinh SQL sai → số liệu sai *vẫn có "trích dẫn"*. (Nguồn chưa khai thác: arxiv 2505.01538, 2402.17840.)
- **Bộ nhớ agent (MemGPT) & human-in-the-loop** — (nguồn: arxiv 2310.08560 MemGPT.)
- **LLM/embedding/OCR TIẾNG VIỆT** (PhoGPT/Vistral/Qwen-2.5 trên tiếng Việt) — *hoàn toàn trống*, ảnh hưởng trực tiếp lựa chọn model cục bộ. (Nguồn: arxiv 2311.02945 PhoGPT, 2403.02715, 2507.21500, aclanthology 2025.acl-long.563.)

→ Đề xuất một track bổ sung **B2 — NL2SQL an toàn + LLM tiếng Việt + permission-aware RAG** (3 khoảng trống giá trị cao).

## 5. ⚠️ Cảnh báo độ tin cậy
- Tất cả benchmark dùng tài liệu tài chính **tiếng Anh** (SEC 10-K, US GAAP). BRAVO phục vụ VAS/tiếng Việt → kết quả chỉ là **chỉ báo định hướng**, KHÔNG đảm bảo chuyển giao. Phải tự xây benchmark tiếng Việt.
- Điểm số model (Claude 95.6%, Qwen-3-8B 30.6%) đúng tại 2025, sẽ dịch chuyển nhanh.
- Bị bác (không dùng): "TableRAG SOTA" (1-2); "một model 7B thay mọi hệ chuyên biệt" (0-3).

## 6. Hành động ưu tiên cho BRAVO (rút từ Track B)
1. **[KIẾN TRÚC] Cấm LLM tính số.** Thêm guardrail: số liệu tính ở SQL/ERP deterministic; LLM chỉ diễn giải + cite. Cập nhật VISION §2 nguyên tắc #3 + ARCHITECTURE + SECURITY. *(Quan trọng nhất.)*
2. **[INGEST] Pipeline bóc bảng hạng nhất** + retrieval schema+cell cho bảng lớn (TableRAG). Bám skill `/rag-ingest-design`.
3. **[EVAL] Dựng bộ eval** RAGAS (faithfulness) + Trust-Score + **benchmark masked-span tiếng Việt kiểu FAITH** — đưa vào GĐ0 ROADMAP.
4. **[MODEL] Cân nhắc lại kích thước Qwen.** Qwen-2.5 nhỏ rủi ro với suy luận số; nếu cần độ chính xác cao → Qwen 32B hoặc cloud opt-in cho *suy luận* (giữ dữ liệu nhạy on-prem). Quyết định qua ADR + benchmark tiếng Việt.
5. **[ALIGN] Căn chỉnh "từ chối khi thiếu căn cứ"** (Trust-Align) cho model cục bộ — biến nguyên tắc zero-hallucination thành hành vi đo được.
6. **[NGHIÊN CỨU] Chạy track bổ sung** NL2SQL an toàn + LLM tiếng Việt + permission-aware RAG (khoảng trống §4).

---
*Phương pháp: 5 góc → 25 nguồn → 120 claim → kiểm chứng 25 → 23 xác nhận / 2 bị bác → 10 sau tổng hợp.*
