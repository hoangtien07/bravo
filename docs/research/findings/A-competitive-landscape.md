# Findings A — Bản đồ cạnh tranh (Deep Research)

> Kết quả deep research (kiểm chứng đối kháng 3 phiếu). Chạy 2026-06-08. Run ID `wf_c3d46c6d-174`.
> **Độ phủ: MỘT PHẦN.** Chỉ 4 đối thủ được kiểm chứng sâu (Oracle NetSuite Next, Finance in M365 Copilot, SAP Joule, Onyx). 10/25 khẳng định qua được kiểm chứng; nhiều khẳng định khác bị giết **do agent kiểm chứng không chạy được vì rate-limit (phiếu trắng), KHÔNG phải vì sai** — xem §4.

> 🔄 **CẬP NHẬT:** các casualty rate-limit của báo cáo này (Daloopa 94% grounded, Supabase RLS-on-vector, Onyx self-host+ACL, Glean on-prem Dell, Sage leak) đã được **xác minh lại từ nguồn gốc — tất cả XÁC NHẬN** trong [findings/F §2](F-reverification.md).

## 1. Phát hiện cốt lõi (đã kiểm chứng, độ tin cậy cao)

> **Cả ba "ông lớn" ERP đang hội tụ về đúng hai điểm khác biệt của BRAVO (permission-aware retrieval + trả lời có trích dẫn/audit) — NHƯNG tất cả đều cloud-only, không có on-prem/air-gapped/LLM cục bộ.** Đây là khoảng trống phòng thủ rõ nhất của BRAVO.

| Đối thủ | Nhóm | Triển khai | Permission-aware | Trích dẫn/audit | On-prem/LLM cục bộ |
|---------|------|-----------|------------------|-----------------|--------------------|
| **Oracle NetSuite Next / "Ask Oracle"** (công bố 07/10/2025) | ERP-embedded | **Cloud-only (OCI)** | ✅ (kế thừa role NetSuite) | ✅ cite nguồn + giải thích "how/why" | ❌ |
| **Finance in M365 Copilot** (GA 20/10/2025) | ERP-embedded | **Cloud-only (M365 tenant)** | ⚠️ kế thừa quyền tenant (gồm cả cấu hình sai) | ✅ role-based audit | ❌ (bắt buộc Exchange Online + Entra ID) |
| **SAP Joule** (14 agent mới, SAP Connect 10/2025) | ERP-embedded | **Cloud-only (BTP, RISE/GROW)** | ✅ | ✅ grounded qua Knowledge Graph | ❌ ("on-premise không được hỗ trợ") |
| **Onyx (Danswer)** | Horizontal RAG (OSS) | **On-prem / air-gapped / bare-metal / VPC** | ⚠️ chưa kiểm chứng được độ sâu | — | ✅ self-host + LLM cục bộ |

**Hệ quả cho BRAVO:** tổ hợp **on-prem/offline (Qwen-2.5) + RLS thật ở tầng SQL + bóc bảng tài chính + tiếng Việt + tích hợp sâu BRAVO ERP** không bị bất kỳ đối thủ *đã kiểm chứng* nào sánh được. Onyx chiếm ô on-prem nhưng là RAG ngang (không native ERP/tài chính, không hỗ trợ tiếng Việt, độ sâu phân quyền chưa rõ).

## 2. Điểm yếu đối thủ BRAVO khai thác được (đã kiểm chứng)

- **M365 Copilot "permission-aware" chỉ KẾ THỪA quyền sẵn có của tenant** — gồm cả cấu hình sai/over-sharing. Nguồn dẫn (Concentric AI; blueprint chống over-share của chính Microsoft): *"Copilot tăng tốc truy cập; nó không kiểm tra việc truy cập đó có chủ đích không"*; ~16% dữ liệu nghiệp vụ quan trọng bị over-share trung bình.
  → **RLS ép buộc ở tầng SQL của BRAVO mạnh hơn về bản chất** (cách ly hàng thật, không kế thừa quyền lỏng). Đây là luận điểm bán hàng & kỹ thuật then chốt.
- Nhiều năng lực của Oracle/SAP là **roadmap 2026 (safe-harbor)** — "đã công bố" ≠ "đã chạy production". BRAVO có cửa sổ thời gian.

## 3. Nguồn chính đã kiểm chứng (≤24 tháng)
- Oracle NetSuite Next: oracle.com (07/10/2025), netsuite.com/portal/products/netsuite-next, docs.oracle.com (AI Connector — *"queries respect your NetSuite role's permissions"*).
- M365 Copilot Finance: microsoft.com/dynamics-365/blog (20/10/2025), learn.microsoft.com (architecture, minimum-requirements).
- SAP Joule: news.sap.com (09/10/2025).
- Onyx: onyx.app/solutions/secure-ai, docs.onyx.app, github.com/onyx-dot-app/onyx (MIT, ~29k sao).

## 4. ⚠️ CẢNH BÁO ĐỌC HIỂU — "refuted" ≠ "sai"

Do rate-limit, nhiều agent kiểm chứng trả phiếu trắng (abstain) → harness tự giết khẳng định vì không đủ 2 phiếu thuận. **Những mục sau bị giết do KHÔNG kiểm chứng được, không phải bị bác bỏ** — thực tế phần lớn ĐÚNG theo nguồn gốc, cần xác minh lại:
- Onyx hỗ trợ LLM cục bộ (Ollama/vLLM/LiteLLM) — *gần như chắc đúng* (có trong docs Onyx).
- **Postgres RLS lọc cả truy vấn vector ở tầng SQL** (mẫu Supabase "RAG with permissions") — *tiền lệ kỹ thuật trực tiếp cho thiết kế RLS của BRAVO*, cần đọc kỹ: supabase.com/docs/guides/ai/rag-with-permissions.
- Glean ra mắt on-prem qua Dell AI Factory (20/05/2025) — chưa xác minh.
- Benchmark Daloopa: LLM trần đạt 11–64% exact-match khi trích số tài chính; **gắn retrieval có cấu trúc → 94.2%** — *bằng chứng mạnh cho luận điểm "grounding chống ảo tưởng số liệu" của BRAVO* nhưng CHƯA kiểm chứng, đừng trích dẫn vội: daloopa.com/benchmark.
- Sự cố Sage Copilot rò dữ liệu chéo khách hàng (The Register, 01/2025) — chưa xác minh, đừng dùng làm "điểm yếu đối thủ" cho tới khi xác minh.

**Bị bác bỏ THẬT (có phiếu refute):** các con số giá MISA AMIS (2.95–8.15 triệu) và MISA SME (6.15–19.95 triệu) — **sai/không xác thực được, KHÔNG dùng**.

## 5. Khoảng trống nghiêm trọng — chưa nghiên cứu được

- **MISA (đối thủ VN trực tiếp nhất): TRỐNG.** Mọi khẳng định về MISA AVA/AMIS (giá, định vị AI) đều bị bác/không xác thực. **Đây là ưu tiên #1 phải chạy lại riêng** trước khi chốt định vị.
- **Toàn bộ phân khúc VN chưa có phát hiện kiểm chứng:** FPT.AI, Viettel AI, VNPT AI, VinAI, Zalo AI, Base.vn, KiotViet, Bizzi.
- Nhiều đối thủ bắt buộc trong brief CHƯA phủ: Glean, Dust, Sana, Writer, ChatGPT Enterprise, Google Agentspace, Hebbia, Zoho Zia, Sage Copilot.
- Không có bằng chứng review G2/Reddit nào qua kiểm chứng (trừ rủi ro over-share của M365 Copilot).

## 6. Câu hỏi mở (ưu tiên giảm dần)
1. **MISA AVA/AMIS thực sự làm gì hôm nay** — giá công bố, mô hình triển khai (cloud/on-prem), có permission-aware/trích dẫn/LLM cục bộ không? (Chạy lại riêng.)
2. Phân khúc VN rộng: có đối thủ nào hỗ trợ on-prem/offline LLM + RAG bảng tài chính tiếng Việt + ERP permission-aware làm xói mòn khác biệt của BRAVO?
3. Độ sâu phân quyền: có đối thủ nào ép buộc cách ly hàng thật ở tầng dữ liệu (vs kế thừa quyền lỏng như M365)? RLS-SQL của BRAVO phòng thủ được tới đâu trước từng đối thủ?
4. Bằng chứng độ chính xác số tài chính (kiểu Daloopa) để chứng thực luận điểm "zero-hallucination + trích dẫn".

## 7. Hành động ưu tiên cho BRAVO (rút từ Track A)
1. **Định vị quanh chủ quyền dữ liệu on-prem/offline** — đây là khoảng trống đã kiểm chứng so với cả 3 ông lớn ERP. Thông điệp: *"Sức mạnh AI của ERP lớn, nhưng chạy trong nhà bạn."*
2. **Biến RLS-SQL thành luận điểm kỹ thuật bán hàng** — đối lập với "permission-aware lỏng" (kế thừa over-share) của M365 Copilot. Cần chứng minh bằng demo cách ly hàng thật.
3. **Sao chép ngôn ngữ "grounded + cite source + giải thích how/why"** của Oracle/SAP — nay là chuẩn ngành, khách sẽ kỳ vọng.
4. **Chạy lại nghiên cứu MISA riêng** (ưu tiên #1) trước khi chốt định vị ở thị trường VN.
5. **Xác minh tiền lệ Supabase RLS-on-vector + benchmark Daloopa** để củng cố cả thiết kế lẫn thông điệp tiếp thị.

---
*Phương pháp: 6 góc tìm kiếm → 27 nguồn → 133 khẳng định → kiểm chứng 25 → 10 xác nhận / 15 bị giết (nhiều do rate-limit) → 5 sau tổng hợp. Phần lớn nguồn primary trong cửa sổ Oct 2025–May 2026.*
