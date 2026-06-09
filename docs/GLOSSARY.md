# GLOSSARY — Thuật ngữ BRAVO AI Copilot

> Từ điển thuật ngữ chung để tài liệu, hội đồng, và code (sau này) nói cùng một ngôn ngữ.

## Khái niệm dự án
- **BRAVO AI Copilot** — sản phẩm: lớp AI ngôn ngữ tự nhiên, bảo mật, offline trên BRAVO ERP.
- **4 nguyên tắc bất biến** — RLS tầng dữ liệu · Không xâm lấn · Zero-hallucination số liệu · Chủ quyền dữ liệu (offline-capable, hybrid). Xem [VISION.md §2](VISION.md).
- **MVP** — Giai đoạn 1: cổng tri thức & vận hành (chưa chạm số liệu tài chính).
- **Anti-goal** — điều cố ý KHÔNG làm (VISION §6).

## Bảo mật & phân quyền
- **RLS (Row-Level Security)** — lọc dữ liệu theo từng dòng dựa trên identity, **trong câu SQL**.
- **RBAC** — phân quyền theo vai trò; ở đây dạng `{resource}:{action}:{scope}`.
- **Scope** — phạm vi: `own_dept` (phòng ban mình + global) hoặc `all`.
- **Global resource** — tài nguyên không gắn phòng ban ⇒ dùng chung.
- **Identity** — danh tính người yêu cầu (employee + department_ids + permissions).
- **Out-of-scope hint** — thông báo tài nguyên tồn tại ngoài quyền, chỉ lộ loại+số lượng.
- **Pepper** — khoá bí mật trộn khi hash token, đặt lúc deploy, không lưu DB.
- **PDPD** — Nghị định 13/2023/NĐ-CP về bảo vệ dữ liệu cá nhân.

## RAG & tri thức
- **RAG** — Retrieval-Augmented Generation: truy hồi chunk liên quan rồi để LLM trả lời dựa trên đó.
- **Ingestion** — luồng nạp tài liệu: parse → chunk → embed → lưu.
- **Docling** — thư viện parse tài liệu (PDF/Office) có nhận diện cấu trúc bảng + OCR lai, dùng trong docsgpt.
- **Chunk** — mẩu văn bản đơn vị để embed/truy hồi.
- **Provenance / Citation** — truy vết nguồn của chunk: tài liệu + **trang/sheet/ô** → dẫn chứng.
- **Embedding** — vector số biểu diễn ngữ nghĩa văn bản; ở đây tính bằng model cục bộ.
- **pgvector** — extension Postgres lưu & tìm vector.
- **MRP pipeline** — Map-Reduce-Refine-Verify-Commit: cách arkon biên soạn tài liệu thành wiki có trích dẫn được kiểm chứng.
- **Verify (grounding check)** — đối chiếu câu trả lời/trích dẫn với nguồn để chống ảo tưởng.
- **Table fidelity** — độ trung thực của bảng sau khi parse (không vỡ cấu trúc).

## Agent & ERP
- **Agent** — thực thể LLM có bộ nhớ & tool-calling, điều phối hội thoại (mô hình letta).
- **Core / Archival / Recall memory** — ba tầng bộ nhớ của letta: trong-context / lâu-dài-vector / lịch-sử-hội-thoại.
- **Tool-calling** — agent gọi hàm/công cụ (KB search, ERP read) theo nhu cầu.
- **Context window management** — đóng gói/nén bộ nhớ vừa context của LLM (quan trọng với model cục bộ context nhỏ).
- **Non-invasive integration** — AI chỉ đọc ERP một chiều; không ghi trực tiếp.
- **Read-only REST API** — cổng một chiều BRAVO ERP cung cấp để AI đọc.
- **Draft / Staging record** — bản ghi nháp AI tạo ra (định khoản/chứng từ) chờ người duyệt trên ERP.
- **`requires_approval`** — cờ (letta) đánh dấu hành động phải có người duyệt trước khi hiệu lực.
- **Draft Queue** — hàng đợi bản nháp chờ duyệt.
- **NL2SQL** — sinh truy vấn từ ngôn ngữ tự nhiên (ở đây hạn chế: ưu tiên view đã duyệt, không SQL tự do tới sổ cái).

## Hạ tầng & vận hành
- **Hybrid (chiến lược LLM)** — local mặc định + cloud opt-in có kiểm soát; sàn offline luôn được đảm bảo. Xem [ADR-0003](adr/0003-hybrid-llm-strategy.md).
- **Model Router / LLM Gateway** — thành phần điều phối mọi lời gọi LLM, chọn local-vs-cloud theo cấu hình + độ nhạy dữ liệu; **fail-closed** (không rõ ⇒ local).
- **Data-egress policy** — chính sách kiểm soát dữ liệu nào được phép rời mạng nội bộ tới LLM cloud. Xem [SECURITY-RLS §9](SECURITY-RLS.md).
- **Sensitivity classification (phân loại độ nhạy)** — gắn nhãn độ nhạy cho dữ liệu/tài liệu để router quyết định egress; mặc định NHẠY (local-only).
- **PII redaction** — khử thông tin nhận dạng cá nhân trước khi gửi prompt ra cloud (tuỳ chọn).
- **Fail-closed** — nguyên tắc an toàn: khi không chắc chắn thì chọn phương án an toàn nhất (ở đây: chạy local, không egress).
- **On-Premise / Air-gapped** — chạy hoàn toàn trong hạ tầng khách, không/không-được nối Internet.
- **LLM cục bộ** — model chạy tại chỗ (Qwen-2.5) qua **vLLM** (GPU) / **Ollama** / **llama.cpp** (GGUF, CPU/quantized).
- **vLLM / Ollama** — runtime phục vụ LLM cục bộ qua giao diện OpenAI-compatible.
- **MCP (Model Context Protocol)** — giao thức để Claude Desktop/Copilot gọi tool của hệ thống; ở đây scoped-by-token.
- **FastMCP** — thư viện dựng MCP server (dùng trong arkon).

## Kế toán (VN)
- **VAS** — Chuẩn mực kế toán Việt Nam.
- **Thông tư 200/2014, 133/2016** — chế độ kế toán doanh nghiệp VN. ⚠️ **Thông tư 99/2025/TT-BTC (ban hành 27/10/2025) THAY TT 200 từ 1/1/2026** — cải cách kế toán DN lớn nhất từ 2003 (tái cấu trúc hệ thống tài khoản). BRAVO cần roadmap TT 99. → [research/findings/G §4](research/findings/G-competitor-deep-dive.md).
- **Định khoản** — bút toán nợ/có vào tài khoản.
- **Kỳ kế toán / Đơn vị cơ sở** — chiều phân tích & phân quyền bổ sung cho số liệu ERP.
- **Khoá sổ** — kỳ đã chốt, không cho sửa chứng từ.
- **Drill-down** — đi từ số tổng hợp xuống chứng từ chi tiết nguồn.

## Quy trình làm việc (harness)
- **Council / Hội đồng** — 5 subagent thẩm định đa chiều (`.claude/agents/`).
- **ADR (Architecture Decision Record)** — bản ghi một quyết định kiến trúc (`docs/adr/`).
- **Skill** — quy trình đóng gói cho Claude (`/council-review`, `/rls-check`, `/rag-ingest-design`, `/adr-new`).
