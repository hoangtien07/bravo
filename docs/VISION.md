# VISION — BRAVO AI Copilot
### Enterprise Knowledge & Financial Analytics Hub

> Tài liệu này tinh chỉnh và hoàn thiện mục tiêu dự án sau khi nghiên cứu ba hệ mã nguồn tham chiếu (arkon, docsgpt, letta). Nó là **nguồn sự thật** về *vì sao* và *cái gì* của dự án. *Như thế nào* nằm ở [ARCHITECTURE.md](ARCHITECTURE.md).

---

## 0. Một câu định vị

> **BRAVO AI Copilot là lớp trí tuệ ngôn ngữ tự nhiên, bảo mật và chạy offline, đặt trên hệ ERP BRAVO — cho phép mỗi nhân viên tra cứu tri thức và hỏi đáp số liệu tài chính trong đúng phạm vi quyền của mình, với mọi câu trả lời đều có dẫn chứng nguồn, và mọi đề xuất nghiệp vụ đều ở dạng nháp chờ người duyệt.**

Nếu phải cắt xuống một dòng để bảo vệ trước Ban lãnh đạo: *"Hỏi ERP bằng tiếng Việt, nhận câu trả lời có dẫn chứng, không lo rò dữ liệu, không lo sai số, và không buộc phải đưa dữ liệu lên cloud — chạy hoàn toàn trong nhà bạn nếu muốn."*

---

## 1. Luận đề tổng hợp: ba repo, ba bộ phận của một cơ thể

Phát hiện cốt lõi sau khi đọc code: **ba dự án tham chiếu không cạnh tranh — chúng bổ trợ.** Mỗi repo đã giải quyết xuất sắc một phần bài toán mà BRAVO AI Copilot cần. Dự án này là **sự tổng hợp có chủ đích** ba phần đó, cộng với lớp tích hợp ERP đặc thù BRAVO.

| Bộ phận | Repo nguồn | Vai trò trong BRAVO AI Copilot |
|---------|-----------|-------------------------------|
| 🦴 **Bộ xương an ninh** | **arkon** | RLS/RBAC cấp phòng ban ép buộc ở tầng SQL; workflow nháp→duyệt; MCP scoped-by-token; biên soạn tri thức có trích dẫn |
| 🫁 **Cơ quan tiêu hoá (nạp dữ liệu)** | **docsgpt** | Nạp PDF/DOCX/Excel qua Docling; bóc tách bảng biểu; trừu tượng hoá LLM & vector-store; đường chạy offline (llama.cpp/FAISS/HF) |
| 🧠 **Bộ não agent** | **letta** | Bộ nhớ có trạng thái (core/archival/recall); tool/function-calling gọi REST API ERP; cơ chế `requires_approval` cho hành động cần duyệt |
| ❤️ **Trái tim ERP** | *(mới — BRAVO xây)* | Lớp tích hợp đọc-một-chiều với BRAVO ERP; ngữ nghĩa kế toán VN; hàng đợi bản ghi nháp đẩy về giao diện ERP |

**Hệ quả thiết kế:** ta không "chọn một trong ba" rồi mở rộng. Ta **mượn pattern** (không fork nguyên khối): mô hình RLS của arkon, pipeline ingestion của docsgpt, mô hình memory+tool của letta — và hợp nhất dưới một kiến trúc duy nhất, bảo mật là mặc định. Chi tiết ánh xạ: [reference/](reference/).

---

## 2. Bốn nguyên tắc bất biến (lặp lại — chúng chi phối mọi thứ)

1. **RLS ép buộc ở tầng dữ liệu.** Lọc phân quyền trong câu SQL, không trong RAM. → §3, [SECURITY-RLS.md](SECURITY-RLS.md).
2. **Không xâm lấn.** Đọc ERP một chiều; ghi/sửa chỉ tạo bản nháp chờ duyệt; không chạm SQL Server gốc.
3. **Zero hallucination số liệu.** Mọi số/khẳng định kèm nguồn (trang/sheet/ô/bản ghi). Không nguồn ⇒ "không tìm thấy". **LLM bị cấm tự tính số** — số liệu tính ở tầng deterministic (SQL/ERP), LLM chỉ diễn giải + trích dẫn. → [ADR-0004](adr/0004-llm-never-computes-numbers.md), [ADR-0005](adr/0005-no-free-form-sql.md). *(Bằng chứng: LLM nhỏ bịa số khi tính toán — [research/findings/B](research/findings/B-academic-technical.md).)*
4. **Chủ quyền dữ liệu (Hybrid).** Sàn bắt buộc: chạy được air-gapped 100% với LLM cục bộ (mặc định). Cloud chỉ opt-in có kiểm soát; dữ liệu nhạy cảm không bao giờ tự động rời mạng. → [ADR-0003](adr/0003-hybrid-llm-strategy.md).

Đây không phải "tính năng" — chúng là **điều kiện để sản phẩm tồn tại được** trong thị trường tài chính Việt Nam.

---

## 3. Mục tiêu Chiến lược (tinh chỉnh)

### 3.1 Lợi thế phòng thủ được (the moat)
Câu hỏi sống còn: *vì sao khách không chỉ dùng ChatGPT Enterprise / Microsoft Copilot, hoặc tự build?* Năm lớp hào:

> ✅ **Đã kiểm chứng (deep research 2026-06-08):** cả 3 ông lớn ERP-AI (Oracle NetSuite Next, M365 Copilot Finance, SAP Joule) **và** đối thủ VN trực tiếp **MISA AVA** đều **cloud-only**; không cái nào có on-prem sovereignty + RLS tầng dữ liệu + trích dẫn nguồn kế toán. Bản đồ cạnh tranh đầy đủ: [research/findings/SUMMARY §3](research/findings/SUMMARY.md). Định vị chính thức: [ADR-0006](adr/0006-market-positioning.md).

1. **Ngữ nghĩa ERP BRAVO bẩm sinh.** Hiểu schema, định khoản, quy trình nghiệp vụ BRAVO — generic AI không có. Đây là tài sản độc quyền của BRAVO.
2. **RLS cấp phòng ban.** Generic chatbot không phân biệt được "kế toán được xem lương, nhân viên thì không". BRAVO AI Copilot ép buộc điều này ở tầng dữ liệu.
3. **Chủ quyền dữ liệu (sàn offline được đảm bảo).** Lưu dữ liệu cá nhân **khách hàng/đối tác** (công dân VN) trên cloud **nước ngoài** bị coi là *chuyển dữ liệu xuyên biên giới* → nghĩa vụ CTIA (hồ sơ + nộp Cục An ninh mạng trong 60 ngày; phạt tới 3 tỷ/5% doanh thu — Điều 20 Luật BVDLCN 91/2025, hiệu lực 1/1/2026). On-prem/lưu-trong-nước **né được lớp này** — điều các ông lớn cloud không có nổi tại chỗ. Với khách chấp nhận cloud, vẫn hỗ trợ **hybrid opt-in có kiểm soát**. → [ADR-0003](adr/0003-hybrid-llm-strategy.md). ⚠️ *Bán bằng **chủ quyền & tuân thủ** (không bán bằng "rẻ hơn" — break-even 5–9 năm). Đòn bẩy này **chỉ cho dữ liệu khách hàng/nghiệp vụ** — dữ liệu HR/lương của chính nhân viên được MIỄN khi lên cloud (Khoản 6 Điều 20), KHÔNG dùng cho HR. Đã re-verify từ văn bản gốc; số điều mẫu cần luật sư xác nhận — [research/findings/F](research/findings/F-reverification.md).*
4. **Dẫn chứng kế toán.** Trả lời số liệu kèm chứng từ nguồn — điều kiện để kế toán/CFO dám tin và dùng.
5. **Go-to-market có sẵn.** Bán-thêm vào tệp khách BRAVO hiện hữu: chi phí thu hút khách ≈ 0, kênh phân phối đã có.

> **Định vị (ADR-0006):** *"AI tài chính có chủ quyền & không bịa số"* — không phải "một con chatbot nữa", mà là *bộ não phân tích an toàn cho dữ liệu ERP của riêng bạn, đặt trong nhà bạn, không bao giờ bịa số.*

### 3.2 Ba dòng giá trị (giữ nguyên, làm rõ người hưởng lợi)
- **Nâng năng lực cạnh tranh hệ sinh thái BRAVO** → giữ chân + nâng cấp khách hiện hữu, tạo điểm khác biệt khi đấu thầu ERP mới.
- **Tối ưu chi phí vận hành nội bộ BRAVO** → giảm tải helpdesk & rút ngắn bàn giao triển khai (đo bằng giờ helpdesk/ticket và số ngày bàn giao).
- **Dòng doanh thu mới (add-on)** → module đóng gói bán theo site/user, biên lợi nhuận cao vì chi phí biên thấp.

---

## 4. Mục tiêu Kỹ thuật (tinh chỉnh theo phát hiện từ code)

### 4.1 Lõi RAG bảo mật & chính xác — *cụ thể hoá*
- **Nạp đa định dạng:** dùng **Docling** (đã được docsgpt tích hợp) cho PDF/DOCX/PPTX/XLSX với *table structure recognition* + OCR lai (chỉ OCR vùng ảnh, nhanh hơn full-page). Hỗ trợ tài liệu scan và tiếng Việt.
- **Khoảng trống phải lấp (phát hiện quan trọng):** docsgpt **không track số trang** ở tầng parser. Để đạt nguyên tắc Zero-hallucination, ta **mở rộng schema chunk** để mang `page_number`, `sheet_name`, `cell_range`, `table_id`, `heading_path` — trích từ page-bounds của Docling. *Đây là điều kiện kỹ thuật của lời hứa "dẫn chứng minh bạch".*
- **Biên soạn có kiểm chứng:** học pipeline **MRP** của arkon (Map→Reduce→Refine→Verify→Commit) — đặc biệt bước **Verify** đối chiếu từng trích dẫn `[^N]` với nguồn. Áp dụng có chọn lọc cho tri thức quan trọng; với hỏi-đáp nhanh dùng RAG truy hồi trực tiếp.
- **Bảng tài chính:** tách bảng thành chunk riêng, giữ header, không cắt giữa bảng — vì bảng vỡ = số liệu vô nghĩa.

### 4.2 Cưỡng chế phân quyền — *kế thừa nguyên mẫu Arkon*
- Áp dụng **dual-realm RBAC** của arkon: quyền theo phòng ban (`{resource}:{action}:{scope}` với scope `own_dept`/`all`) + (tuỳ chọn) quyền theo workspace/dự án.
- **Filter ở tầng SQL** qua pattern `build_*_filter` / `apply_scope_filter`. Tài liệu không gắn phòng ban = dùng chung.
- **Token MCP hash bằng HMAC + pepper**, không lưu plaintext. "Out-of-scope" chỉ lộ loại+số lượng, không lộ tiêu đề.
- Chi tiết: [SECURITY-RLS.md](SECURITY-RLS.md).

### 4.3 Triển khai hybrid — *sàn offline + cloud opt-in có kiểm soát* ([ADR-0003](adr/0003-hybrid-llm-strategy.md))
- **LLM cục bộ (mặc định):** Qwen-2.5 (7B/14B/32B tuỳ tài nguyên) qua **vLLM** (GPU) hoặc **Ollama/llama.cpp GGUF** (CPU/quantized). Tham chiếu `letta/docker-compose-vllm.yaml`.
- **Model Router + chính sách data-egress:** mọi lời gọi LLM qua một router; router chọn local-vs-cloud theo cấu hình + **độ nhạy dữ liệu** (tái dùng nhãn phòng ban/loại tri thức từ RLS). Cloud mặc định TẮT; dữ liệu nhạy cảm (kế toán/lương/HR/PII) **ghim cứng ở local**; mọi lời gọi cloud được audit. Fail-closed: không xác định được độ nhạy ⇒ chạy local. Chi tiết: [SECURITY-RLS.md §9](SECURITY-RLS.md).
- **Embedding cục bộ:** sentence-transformers đa ngữ hỗ trợ tiếng Việt (embedding của nội dung nhạy cảm cũng không rời mạng).
- **Stack offline (sàn bắt buộc):** Postgres+pgvector (vector store, có ACID, hợp khách air-gapped hơn FAISS rời rạc), MinIO/đĩa local (storage), Docker Compose (cài nhỏ) / Helm (cài lớn).
- **Kiểm soát phụ thuộc Internet ngầm** (telemetry, model download runtime) — air-gapped checklist. Xem agent `onprem-deployment-engineer`.

### 4.4 Tích hợp không xâm lấn — *làm rõ ranh giới*
- AI đọc ERP **chỉ qua REST API Read-Only** đã được BRAVO cung cấp; ưu tiên đọc qua **view/API đã chuẩn hoá & duyệt bởi kế toán** thay vì SQL tự do (giảm rủi ro sai ngữ nghĩa).
- Mọi tác vụ ghi → **bản ghi nháp (Staging/Draft)** vào hàng đợi, người dùng duyệt thủ công trên giao diện ERP. Cơ chế `requires_approval` học từ letta; workflow duyệt học từ arkon (advisory-lock chống race khi duyệt).

---

## 5. Mục tiêu Nghiệp vụ — MVP và lộ trình giá trị

### 5.1 Giai đoạn 1 — MVP: Tri thức & Vận hành (rủi ro thấp, giá trị nhanh)
*Vì sao trước:* không chạm số liệu tài chính ⇒ rủi ro sai thấp ⇒ xây niềm tin trước khi tiến vào vùng nhạy cảm.

- **Cổng tri thức nội bộ:** tra cứu quy chế, quy trình kế toán, **sổ tay định khoản**, chính sách HR/pháp lý — *trong đúng phạm vi phòng ban*.
- **Trợ lý kỹ thuật triển khai:** cẩm nang triển khai BRAVO ERP, xử lý **mã lỗi phần mềm**, tham số cấu hình → giảm tải helpdesk, rút ngắn bàn giao.
- Mọi câu trả lời kèm trích dẫn nguồn (tên tài liệu + trang).

**Metric thành công Giai đoạn 1:**
- ≥ X% câu hỏi helpdesk được tự phục vụ không cần người (mục tiêu khởi điểm: 30–40%).
- Giảm Y% thời gian trung bình xử lý ticket tra cứu.
- Giảm Z ngày thời gian bàn giao một dự án triển khai.
- Citation accuracy ≥ 95% trên bộ eval nội bộ.

### 5.2 Giai đoạn 2 — NÂNG CAO: Phân tích Tài chính & Agent chủ động (phần user yêu cầu phân tích thêm)

> Đây là nơi "giá trị thật sự trên thị trường" của BRAVO AI được thiết lập. Đề xuất **năm năng lực**, xếp theo tỷ lệ giá-trị/rủi-ro. Tất cả đều tuân thủ 4 nguyên tắc bất biến.

**(A) Hỏi-đáp số liệu tài chính bằng ngôn ngữ tự nhiên (NL → insight có guardrail).**
Ví dụ: *"Doanh thu thuần quý 2 so với quý 1?"*, *"Top 10 khách hàng công nợ quá hạn"*, *"Chi phí nào tăng bất thường tháng này?"*.
- *Giá trị:* lãnh đạo/quản lý tự phục vụ báo cáo, không chờ kế toán dựng report → quyết định nhanh hơn.
- *Guardrail:* chỉ đọc qua **view/API kế toán đã duyệt** (không SQL tự do tới sổ cái), **luôn trích nguồn** tới chứng từ, cho **drill-down** tới bản ghi gốc, gắn nhãn *"cần kế toán xác nhận trước khi ra quyết định"*. Bộ nhớ ngữ cảnh (letta) nhớ kỳ kế toán/đơn vị đang xét.
- *Đây là tính năng "đinh" để demo trước Ban lãnh đạo.*

**(B) Phát hiện bất thường & kiểm soát rủi ro (proactive monitoring).**
Tự động soi: bút toán bất thường, chi vượt định mức, công nợ rủi ro, hoá đơn trùng, số tròn đáng ngờ, lệch tổng-chi tiết.
- *Giá trị:* kiểm soát nội bộ / phòng gian lận / hỗ trợ kiểm toán — **giá trị rất cao cho CFO & ban kiểm soát**, khó tìm ở công cụ generic.
- *Cơ chế:* agent có bộ nhớ (letta) chạy nền theo lịch, phát cảnh báo có dẫn chứng; không tự sửa gì — chỉ nêu cờ đỏ kèm bản ghi nguồn.

**(C) Soạn nháp chứng từ/định khoản từ tài liệu (draft automation).**
Đọc hoá đơn/hợp đồng (đã nạp qua RAG) → đề xuất **định khoản nháp** đẩy vào hàng đợi ERP.
- *Giá trị:* giảm nhập liệu thủ công lặp lại của kế toán.
- *An toàn:* hoàn toàn theo nguyên tắc non-invasive — chỉ tạo draft cân nợ-có, kế toán duyệt mới hạch toán; tôn trọng kỳ đã khoá sổ.

**(D) Báo cáo quản trị ngôn ngữ tự nhiên (NL executive reporting).**
Sinh bản tóm tắt điều hành định kỳ (tháng/quý) có dẫn chứng + diễn giải xu hướng.
- *Giá trị:* tiết kiệm thời gian dựng báo cáo quản trị; chuẩn hoá narrative.

**(E) Suy luận liên-tài-liệu (cross-source reasoning).**
Nối tài liệu (điều khoản hợp đồng) với dữ liệu ERP (công nợ thực tế) để trả lời câu hỏi liên hệ: *"Khách nào đang vi phạm hạn mức công nợ so với hợp đồng?"*.
- *Giá trị:* trả lời được câu hỏi mà cả "tra tài liệu" lẫn "query ERP" đơn lẻ không làm được — biểu diễn rõ nhất sức mạnh tổng hợp RAG + ERP + agent.

> **Thứ tự đề xuất triển khai Giai đoạn 2:** A → B → C → D → E (tăng dần độ phức tạp & rủi ro). A và B nên là trọng tâm vì tỷ lệ giá-trị/rủi-ro tốt nhất.

**Metric thành công Giai đoạn 2:** thời gian từ câu hỏi → insight (giây vs giờ), số báo cáo tự phục vụ/tháng, số cờ rủi ro hợp lệ được phát hiện sớm, % nháp chứng từ được duyệt không sửa.

---

## 6. Phản-mục-tiêu (Anti-goals) — để không đi chệch hướng

Nêu rõ những gì dự án **cố ý KHÔNG làm** — quan trọng ngang mục tiêu:

- ❌ **Không** thay thế kế toán/kiểm toán. AI là copilot, con người quyết định và chịu trách nhiệm.
- ❌ **Không** tự động hạch toán/ghi sổ. Mọi thứ là nháp chờ duyệt.
- ❌ **Không** cho SQL tự do tới CSDL ERP gốc. Đọc qua API/view đã duyệt.
- ❌ **Không** là chatbot vạn năng. Phạm vi = tri thức nội bộ + dữ liệu ERP của chính khách, trong quyền của người hỏi.
- ❌ **Không** phụ thuộc cloud trong đường chạy sản phẩm.
- ❌ **Không** trả lời số liệu không có nguồn. Thà nói "không biết".

---

## 7. Rủi ro lớn & cách thiết kế đã phòng vệ

| Rủi ro | Hệ quả | Phòng vệ (đã gắn vào thiết kế) |
|--------|--------|-------------------------------|
| Rò dữ liệu giữa phòng ban | Mất niềm tin, vi phạm pháp lý | RLS ở tầng SQL (arkon), skill `/rls-check`, agent `security-rls-auditor` |
| AI trả số liệu sai/bịa | Quyết định tài chính sai, sụp đổ niềm tin | Bắt buộc trích nguồn, đọc qua view đã duyệt, verifier đối chiếu, nhãn "cần xác nhận" |
| Bảng tài chính bị parse vỡ | Số liệu vô nghĩa khi truy hồi | Docling table-structure, chunk bảng riêng, eval table-fidelity |
| Phụ thuộc Internet ngầm | Khách air-gapped không cài được | Air-gapped checklist, agent `onprem-deployment-engineer` |
| Hybrid: dữ liệu nhạy rò ra cloud | Vi phạm chủ quyền/pháp lý | Model Router fail-closed, ghim cứng dữ liệu nhạy ở local, audit egress, agent `security-rls-auditor` |
| AI ghi nhầm vào ERP | Hỏng dữ liệu nghiệp vụ | Read-only tuyệt đối + chỉ tạo draft, advisory-lock khi duyệt |
| Làm quá nhiều, MVP chậm | Mất động lực, khó chứng minh ROI | MVP tri thức trước, agent `product-strategist` gác cổng phạm vi |
| Tiếng Việt: OCR/embedding kém | Chất lượng truy hồi thấp | Chọn model OCR/embedding hỗ trợ tiếng Việt, eval bằng corpus VN |

---

## 8. Câu hỏi mở cần BRAVO trả lời (để hoàn thiện hướng đi)

Những điều thiết kế đang giả định, cần đội BRAVO xác nhận:
1. BRAVO ERP **đã có REST API Read-Only** chưa, độ phủ tới đâu? Có cơ chế **hàng đợi staging/draft** sẵn trên giao diện ERP để AI đẩy bản nháp vào? → **Tài liệu yêu cầu chi tiết (gửi đội BRAVO ERP): [ERP-INTEGRATION-REQUEST.md](ERP-INTEGRATION-REQUEST.md).** *(Cập nhật 2026-06: chưa có API read-only — đang xin.)*
2. Mô hình **phòng ban & phân quyền** hiện hữu trong BRAVO ERP tổ chức thế nào — ta đồng bộ hay tự quản trị trong Copilot?
3. Phần cứng khách hàng điển hình: có **GPU** không? Quy mô người dùng đồng thời?
4. Bộ **tài liệu mẫu** (quy chế, sổ tay định khoản, cẩm nang triển khai) để xây bộ eval và pilot?
5. Tiêu chí mua của khách: tính theo **user/site/tính năng**? Ai là người ký (CFO/CIO/IT)?

→ Các quyết định phát sinh từ đây sẽ được ghi thành ADR trong [adr/](adr/).

---

## 9. Tiêu chí "đi đúng hướng" (định nghĩa thành công của chính tài liệu này)

Dự án đi đúng hướng khi, tại mỗi mốc, trả lời "có" cho:
- [ ] Mọi tính năng tôn trọng đủ 4 nguyên tắc bất biến?
- [ ] MVP chứng minh được giá trị đo lường được trước khi mở rộng?
- [ ] Mọi câu trả lời số liệu đều truy vết được tới nguồn?
- [ ] Hệ thống cài và chạy được trong môi trường air-gapped?
- [ ] Có lợi thế phòng thủ rõ so với generic AI (§3.1)?
- [ ] Phạm vi được hội đồng (`/council-review`) thông qua, không có ❌ Critical chưa xử lý?
