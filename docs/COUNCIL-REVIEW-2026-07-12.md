# Council Review 2026-07-12 — "Chatbot hiểu phần mềm": đối chứng BravoGen & định hướng

> Bối cảnh: chủ dự án đối chứng bravo-local với chatbot production **chat.bravogen.io.vn**
> (LibreChat + Google Gemini, RAG trên cùng bộ tài liệu BRAVO 10) và kết luận câu trả lời của ta
> "không đáng xem, tự bịa, không hiểu phần mềm". Hội đồng rà soát nguyên nhân + định hướng.
> Thành viên: **rag-architect · erp-accounting-expert/end-user · product-strategist** (3 phiên
> độc lập). Bằng chứng kỹ thuật xác minh trực tiếp trên repo + DB pilot (3.141 chunks).

## 0. Sự thật đã xác minh (trước khi phán xét)

**Ca lỗi điển hình (câu đề-bài nhập chứng từ "0000096/AP-14L"):**
1. **Retrieval gãy với câu đề-bài dài**: embedding câu thô (đầy số liệu, tên hàng) kéo lệch sang
   Chapter17 (giá thành/xuất kho), không có Chapter08 "Phiếu nhập mua" trong top-12 — trong khi
   hỏi ngắn "cách tạo phiếu nhập mua" trả lời chuẩn. → thiếu bước cô đọng câu hỏi.
2. **Guardrail abstain bị lách**: model mở đầu "Không tìm thấy..." rồi **vẫn tự bịa các bước** từ
   kiến thức ngoài (menu không tồn tại trong BRAVO) — vi phạm zero-hallucination dạng tinh vi.
3. Cùng ngày (đã vá trước đó): tiếng Việt **không dấu** làm lexical trượt toàn bộ; server chạy
   code cũ khi người dùng test.

**Đã vá trong ngày (commit `bf4afcb…`, đã push `bravo-v0.1`):** core-memory persona/nghiệp vụ pin
vào prompt · prompt chi tiết + guided-abstain · top_n 6→12 · citation-hygiene · unaccent lexical ·
intent-boost technical_manual + keyword dev · parse DOCX kỹ thuật (0→153 chunk) · cô đọng câu
đề-bài dài (`_rephrase_query`) · `_clip_abstain` fail-closed · tool read-only `preview_journal_entry`
· fix `guided_json`/OpenAI · **theo council hôm nay:** `_is_abstain` prefix-match (hết nuốt oan câu
trả lời một-phần) · lexical OR-fallback bigram + `ts_rank_cd` (câu dài tự nhiên) · rerank snippet
280→700 head+tail + log skip-sensitive · từ điển viết tắt VN (`vn_terms.py`: CCDC/TSCĐ/CĐPS/…).

**Đo lại sau vá (cùng câu đề-bài):** trả hướng dẫn từng bước đúng dữ liệu đề + cite [1],[3] —
ngang BravoGen về cấu trúc; còn kém về độ "thuộc" cấu hình (chưa nêu Giao dịch 2103 — xem mục 3).

## 1. Phán quyết hội đồng — vì sao "kém hơn BravoGen"

Ba chuyên gia hội tụ về MỘT chẩn đoán ba tầng:

| Tầng | Tỷ trọng ước tính | Nội dung | Trạng thái |
|---|---|---|---|
| **Công nghệ** (retrieval/prompt) | ~30% | Khung đúng (hybrid+RRF+RLS+intent+version); thua ở "chi tiết vận hành": rerank bị bóp input, lexical chết câu dài, guard abstain quá tay, retrieval một-phát-duy-nhất | phần lớn **đã vá hôm nay**; còn mục 2 |
| **Dữ liệu** (corpus) | **~40% — lớn nhất** | BravoGen dùng CÙNG tài liệu nhưng Gemini **bù lỗ hổng corpus bằng world-knowledge**; và họ có **master data ta không có** (danh mục giao dịch). Với LLM local, mọi tri thức tình huống PHẢI nằm trong corpus | cần chủ dự án cấp dữ liệu (mục 3) |
| **Kỳ vọng sai vai** | ~30% | Người dùng chấm bravo như chatbot tra-cứu — trục mà Gemini cloud thắng theo cấu tạo; trục bravo độc quyền (số liệu + draft + maker-checker + on-prem) **chưa được chấm** vì luồng AP chưa vào nếp dùng | quyết định định vị (mục 4-5) |

**Cách biến ước tính thành số (2 tuần):** blind test 30 câu từ log pilot + ticket helpdesk, dán nhãn
fail: `retrieval-miss / corpus-miss / synthesis-poor / wrong-task-type`, chạy song song BravoGen.

## 2. RAG-architect — việc kỹ thuật còn lại (sau khi đã vá 4 mục hôm nay)

Còn theo thứ tự ảnh hưởng (chưa làm — cần lịch):
1. **[CAO] `kb_search` tool là noop + không multi-query**: retrieval đúng 1 phát/lượt; agent không
   tự tìm lại được với từ khóa khác. → wire `kb_search` thành retrieval thật (closure per-session);
   tách câu đa ý thành 2-3 sub-query trong cùng lời gọi rephrase, RRF merge. (effort vừa)
2. **[VỪA] Chunk "mù heading"**: DOCX/markdown embed body trần; PDF section cắt đôi mất tiêu đề.
   → prepend `heading_path` (số + TIÊU ĐỀ chữ) vào text lúc embed; cần re-ingest. (vừa)
3. **[VỪA] Quy trình dài bị cắt 900 token, không parent-document expansion** → sau rerank, gom
   chunk theo (source, heading), fetch đủ mảnh cùng section (cap ~2k token). (vừa)
4. **[VỪA] Eval lệch prod**: golden gate chạy `use_rerank=False` trong khi prod bật rerank llm;
   feedback like/dislike ĐÃ thu nhưng không ai tiêu thụ. → golden set 50-100 câu từ log thật +
   nightly đúng config prod + job export dislike → golden set. (vừa)
5. **[VỪA-THẤP] Bảng chữ trong PDF DLL bị pypdf ép phẳng** (heuristic chỉ bắt bảng số) → mở rộng
   heuristic/force docling cho nhóm DLL; re-ingest 11 file. (vừa)
6. **[THẤP] `retrieval_min_score=0.12` gắn model embedding cụ thể** → calibrate percentile trên
   golden set mỗi khi đổi model; khi fused rỗng trả kèm 2-3 chương gần nhất. (nhỏ)

## 3. ERP-expert / end-user — corpus & tri thức nghiệp vụ (data-gap 40%)

**Phát hiện chốt: "Giao dịch 2103" = 0 chunk, và KHÔNG có trong bất kỳ PDF gốc nào** (quét cả
text-layer 19 chương). BravoGen "thuộc" mã giao dịch vì có nguồn ta không có: **danh mục giao
dịch chuẩn (master/configuration data)** — sống trong DB demo BRAVO hoặc tài liệu đào tạo triển
khai, không trong user-guide. "mua hàng công nợ" (từ đời thường) cũng = 0 chunk.

**Coverage theo nhóm câu hỏi end-user:** nhập chứng từ = đủ BƯỚC hụt MÃ; lên báo cáo = mỏng
(Nhật ký chung 0); **xử lý sai lệch số liệu = thiếu nặng** (nhóm ticket nhiều nhất ngoài đời);
khóa sổ/kết chuyển = có khung thiếu thao tác; HĐĐT/thuế = mỏng; lỗi thường gặp dạng hỏi-đáp ≈ 0.
**Méo cấu trúc: KQPT (tài liệu BA) chiếm 41% corpus** — thường thắng retrieval làm câu trả lời
nghe "phân tích hệ thống" thay vì "hướng dẫn dùng". Playbook `support_helpdesk` trỏ vào
`support_ticket` = **0 chunk** (contract không có nhiên liệu).

**Tri thức cần bổ sung (xếp theo tác động — chủ dự án sở hữu nguồn):**
1. **Danh mục giao dịch chuẩn** (mã + tên + màn hình + cặp định khoản mặc định) → xuất từ DB demo
   BRAVO thành `file_system/bravo_transaction_catalog.yaml`, source_type mới `configuration_catalog`,
   pin tóm tắt vào playbook hint. *Vài ngày công, đổi hẳn chất câu trả lời.*
2. **Mapping "nghiệp vụ đời thường → màn hình/giao dịch"** (~100 dòng đầu, curate bởi triển khai/helpdesk).
3. **50–100 cặp Q&A ticket helpdesk thật** làm source_type `support_ticket` — lấp nhóm sai-lệch/lỗi.
4. **Tình huống mẫu/bài tập có lời giải** (giáo trình đào tạo nhân viên mới).
5. Cân lại tỷ trọng KQPT (demote cho intent end_user).

## 4. Product-strategist — định vị & roadmap

**Định vị:** (i) đua Q&A với BravoGen = **chết chắc** (Gemini cloud thắng fluency theo cấu tạo);
(ii) on-prem sovereignty = moat thật nhưng thu hoạch ở L4; (iii) **AP money-engine + draft-workflow
= thứ BravoGen KHÔNG THỂ làm** (PDPL chặn số liệu thật lên cloud; không verify-gate; không
maker-checker/RLS) → mũi khoan. **BravoGen không phải đối thủ — là tài sản**: log câu hỏi thật của
nó là mỏ vàng cho eval + corpus.

**Q&A không đua trần nhưng phải giữ SÀN:** citation ≥95%, first-token <3s, abstain-có-đường-thoát,
nút copy-kèm-nguồn. Vượt sàn → mọi đầu tư thêm vào Q&A là lãng phí so với agentic.

**Rủi ro chết dự án:** bị đo bằng thước của BravoGen → user churn trước khi chạm giá trị AP →
không có usage → sponsor cắt. Vệ tinh: dev bị hút vào đua Q&A; 70% hóa đơn thật là PDF scan;
critical-path phi kỹ thuật (template import + chứng từ thật phải xin từ kế toán).

**Roadmap 30/60/90 (chi tiết trong phiên council):**
- **30 ngày**: blind test 30 câu (đo 4 nhãn fail) · ≥50 hóa đơn thật E2E (đo % PDF scan) · duyệt-
  không-sửa ≥70% · fix refusal-style + copy-nguồn · xin template import + chứng từ thật (tuần 1).
- **60 ngày**: ≥1 kế toán dùng AP hàng tuần · đo phút/hóa đơn trước-sau (mục tiêu −40%) · +100-200
  Q&A tình huống từ ticket (corpus-miss giảm ≥50%) · Qwen local trên GPU + pass^k.
- **90 ngày (cổng L3)**: 1 phòng ban dùng hàng tuần + "tin số" · citation ≥95% · 0 rò RLS ·
  willingness-to-pay có con số · video demo air-gap. **Trượt → thu hẹp còn "AP tool thuần" hoặc dừng.**

## 5. Ba quyết định đề nghị chủ dự án chốt

1. **Phân vai 2 chatbot bằng văn bản 1 trang** *(khuyến nghị)*: BravoGen = tra cứu tài liệu chung
   (cloud-OK); bravo = số liệu + chứng từ + AP + mọi thứ có phân quyền/nhạy cảm. Dùng log BravoGen
   làm nguồn eval/corpus cho bravo. (Loại: thay thế BravoGen; hợp nhất frontend trước L3.)
2. **Nâng fluency bằng hybrid theo nhãn dữ liệu** *(khuyến nghị)*: cloud opt-in CHỈ cho lớp corpus
   không nhạy (user-guide — vốn đã lên Gemini qua BravoGen), số liệu/chứng từ ghim local. Đúng
   thiết kế sẵn của bất biến #4 + ADR-0003. (Loại: chờ GPU model lớn — đúng dài hạn nhưng chậm.)
3. **Chốt cổng L3 nghiêm + hạn 90 ngày (12/10)** *(khuyến nghị)*: tiêu chí thoả thuận trước với
   sponsor; trượt → thu hẹp "AP tool thuần" hoặc dừng — để dự án không chết vì cảm tính so sánh.

---
*Phụ lục: harness đối chứng + 34 câu hỏi + kết quả thô tại scratchpad phiên làm việc
(compare/questions.yaml, questions_tech.yaml, REPORT.md, comparison_merged.md).*
