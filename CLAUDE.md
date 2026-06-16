# CLAUDE.md — BRAVO AI Copilot

> File này được Claude đọc mỗi phiên làm việc. Giữ ngắn gọn, súc tích. Chi tiết nằm trong `docs/`.

## 1. Dự án là gì

**BRAVO AI Copilot — Enterprise Knowledge & Financial Analytics Hub.**
Biến hệ sinh thái **BRAVO ERP** (nền tảng .NET + SQL Server) từ hệ thống *ghi nhận dữ liệu* thành **hệ thống mở thông minh**: tra cứu tri thức nội bộ bằng ngôn ngữ tự nhiên, phân tích tài chính có dẫn chứng, và đề xuất nghiệp vụ ở dạng *bản nháp chờ duyệt* — tuyệt đối không can thiệp trực tiếp vào CSDL gốc.

Khách hàng: nội bộ BRAVO (helpdesk, cán bộ triển khai) ở giai đoạn MVP; bán add-on cho khách doanh nghiệp ở giai đoạn sau.

**Tài liệu nguồn của sự thật:** [docs/VISION.md](docs/VISION.md) (mục tiêu đã tinh chỉnh) và [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## 2. Bốn nguyên tắc bất biến (NON-NEGOTIABLE)

Mọi thiết kế, mọi dòng code sau này, mọi câu trả lời phải tôn trọng 4 ràng buộc này. Nếu một đề xuất vi phạm — dừng lại và nêu rõ.

1. **Phân quyền cưỡng chế ở tầng dữ liệu (Row-Level Security).** Nhân viên chỉ thấy tài liệu/dữ liệu thuộc phòng ban của mình hoặc tài liệu dùng chung. RLS được lọc trong **câu truy vấn SQL**, không lọc trong bộ nhớ ứng dụng. Kế thừa tư duy Arkon. Chi tiết: [docs/SECURITY-RLS.md](docs/SECURITY-RLS.md).
2. **Không xâm lấn (Non-invasive).** AI chỉ **đọc** ERP qua REST API một chiều (Read-Only). Mọi tác vụ ghi/sửa chỉ tạo **bản ghi nháp (Staging/Draft)** đưa vào hàng đợi chờ người duyệt thủ công trên giao diện ERP. Không bao giờ ghi thẳng vào SQL Server gốc.
3. **Triệt tiêu ảo tưởng số liệu (Zero hallucination on numbers).** Mọi câu trả lời có số liệu/dẫn chứng phải kèm **nguồn + số trang/sheet/ô**. Không có nguồn ⇒ nói "không tìm thấy", không suy đoán. Số liệu kế toán sai là rủi ro chết người của dự án.
4. **Chủ quyền dữ liệu — offline-capable, cloud opt-in có kiểm soát (Hybrid).** Hệ thống *bắt buộc* có đường chạy offline 100% được đảm bảo — đây là **mặc định** (Docker/K8s + LLM cục bộ như Qwen-2.5). Model cloud chỉ dùng khi khách **chủ động bật**, và **chỉ với lớp dữ liệu chính sách cho phép rời mạng**; dữ liệu nhạy cảm (kế toán, lương, HR, PII) **không bao giờ tự động gửi ra ngoài**. Mọi lựa chọn kỹ thuật phải giữ nguyên đường chạy không-cloud. Quyết định: [docs/adr/0003-hybrid-llm-strategy.md](docs/adr/0003-hybrid-llm-strategy.md).

## 3. Ba trụ cột — học gì từ ba repo tham chiếu

Dự án **không khởi tạo từ con số 0**. Nó tổng hợp ba hệ mã nguồn có sẵn trong workspace (chỉ để **học/tham chiếu**, không sửa code của chúng):

| Repo | Đường dẫn | Ta kế thừa cái gì | Ghi chú |
|------|-----------|-------------------|---------|
| **arkon** | `../arkon` | RLS/RBAC theo phòng ban ở tầng SQL; pipeline biên soạn wiki có trích dẫn (MRP); workflow nháp→duyệt; MCP server scoped-by-token | Khung xương an ninh & tri thức |
| **docsgpt** | `../docsgpt` | Nạp đa định dạng (PDF/DOCX/Excel) qua Docling; bóc tách **bảng biểu**; trừu tượng hoá LLM/vector-store đa nhà cung cấp; chạy offline (llama.cpp/FAISS/HF embeddings) | Lõi ingestion & RAG |
| **letta** | `../letta` | Bộ nhớ agent có trạng thái (core/archival/recall); tool/function-calling để gọi REST API ERP; cơ chế nháp chờ duyệt (`requires_approval`) | Lõi agent hội thoại |

Chi tiết chắt lọc: [docs/reference/arkon-notes.md](docs/reference/arkon-notes.md), [docs/reference/docsgpt-notes.md](docs/reference/docsgpt-notes.md), [docs/reference/letta-notes.md](docs/reference/letta-notes.md).

## 4. Cách làm việc trong repo này

- **Giai đoạn hiện tại = BUILD (Phase 1–2, đang chạy E2E).** 15 ADR. Lõi đã chạy: RAG+RLS, agent loop + verify-gate, eval pass^k, **money-engine AP** (hoá đơn XML→bút toán TT99, branch `feat/money-engine-ap`), **nền tảng chat** (React SPA + SSE streaming + multi-turn, branch `feat/chat-platform`). Stack: FastAPI + async SQLAlchemy + PostgreSQL/pgvector, modular monolith ([ADR-0007](docs/adr/0007-code-strategy.md)). Chạy/cấu trúc: [README.md](README.md), [README-DEV.md](README-DEV.md). **arkon = viết lại từ pattern** (không copy code — PolyForm); docsgpt/letta = chuyển thể (MIT/Apache).
- **Tái dùng trước khi xây mới:** xương sống đã có (loop·draft+maker-checker·verify-gate·RLS·memory·conversations·accounting). Đọc code thật, giữ 4 bất biến, anti-over-engineering.
- **Tiếng Việt** cho tài liệu nghiệp vụ/chiến lược; thuật ngữ kỹ thuật giữ tiếng Anh.
- Mọi quyết định kiến trúc lớn → ghi thành **ADR** trong [docs/adr/](docs/adr/) (dùng skill `/adr-new`).
- Tham chiếu file theo `path:line` để bấm được.
- Không sửa file trong `../arkon`, `../docsgpt`, `../letta` — chúng là tài liệu tham khảo.

## 5. Council & Skills (harness)

**Hội đồng cố vấn (`.claude/agents/`)** — gọi qua skill `/council-review` hoặc Task tool để thẩm định một thiết kế từ nhiều góc độ:

| Thành viên | Vai trò |
|------------|---------|
| `security-rls-auditor` | An ninh, RLS, quyền riêng tư, tuân thủ PDPD Việt Nam |
| `erp-accounting-expert` | Nghiệp vụ ERP/kế toán BRAVO, tính đúng đắn số liệu |
| `rag-architect` | Ingestion, RAG, trích dẫn, đánh giá chất lượng |
| `onprem-deployment-engineer` | Docker/K8s, LLM cục bộ, hạ tầng offline |
| `product-strategist` | Giá trị kinh doanh, định vị thị trường, MVP scope |

**Skills (`.claude/skills/`):**

| Skill | Khi nào dùng |
|-------|--------------|
| `/council-review` | Thẩm định một thiết kế/quyết định lớn qua hội đồng |
| `/rls-check` | Kiểm tra một tính năng có rò rỉ phân quyền không |
| `/rag-ingest-design` | Thiết kế/đánh giá luồng nạp một loại tài liệu mới |
| `/adr-new` | Tạo một Architecture Decision Record mới |

## 6. Stack (đã chốt — xem ADR)

Backend Python (FastAPI, async SQLAlchemy) · PostgreSQL + pgvector · Docling/pypdf (ingestion) · `defusedxml` (hoá đơn XML) · **Model Router** điều phối LLM local (vLLM/Ollama, Qwen-2.5) mặc định + cloud opt-in (OpenAI-compatible, audit-then-egress) · FastMCP · **Frontend: React 18 + Vite + TypeScript + Tailwind** (design tokens brand, primitives kiểu shadcn) tại `frontend-react/`, streaming qua SSE (POST+fetch). **Mọi lựa chọn giữ nguyên đường chạy offline (sàn bắt buộc).** ADR: [docs/adr/](docs/adr/) (0001–0015).
