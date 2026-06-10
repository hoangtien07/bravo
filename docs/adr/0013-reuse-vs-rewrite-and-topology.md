# 0013. Reuse-vs-rewrite & topology: BALANCED_REUSE — reuse library proven, hand-roll glue mang invariant, modular-monolith

- **Trạng thái:** Accepted
- **Ngày:** 2026-06-11
- **Người quyết định:** BRAVO (Hội đồng 6 lăng kính — **6/6 BALANCED_REUSE**)
- **Liên quan:** tinh chỉnh [ADR-0007](0007-code-strategy.md) & [ADR-0009](0009-local-model-stack.md); xác nhận [ADR-0008](0008-arkon-license-ownership.md); duyệt [ADR-0010](0010-agent-loop-architecture.md)/[0011](0011-egress-classification-audit.md)/[0012](0012-verify-gate-number-integrity.md). Căn cứ: [research/findings/K](../research/findings/K-agentic-architecture.md).

## Bối cảnh (Context)
Chủ dự án nêu lo ngại đúng: code thực tế đang **reimplement lean** (vd [parser.py](../../app/ingestion/parser.py) route mọi PDF sang pypdf; [memory.py](../../app/agent/memory.py) "NOT full Letta") thay vì tái dùng letta/docsgpt đã được cộng đồng kiểm chứng → "tái tạo bánh xe", sinh bug. Yêu cầu: hợp nhất điểm mạnh repo **nhưng tái dùng cả quá trình phát triển**, **tránh over-engineering**, sẵn sàng microservices/monolith/monorepo. Câu hỏi: reuse-vs-rewrite cho từng thành phần + topology.

## Quyết định (Decision)
**BALANCED_REUSE.** Công thức: **REUSE ở tầng LIBRARY in-process** cho "bánh xe thật" (self-host được + không cần RLS bám lõi); **HAND-ROLL/REWRITE-LEAN** cho mọi thành phần mang invariant hoặc coupling RLS. **Hai lằn ranh CỨNG (phủ quyết security + accounting):**
1. **TUYỆT ĐỐI KHÔNG chạy letta/docsgpt như service riêng** — tạo authorization plane thứ hai + RLS phân tán (phá invariant 1) + phá air-gapped (invariant 4). Giá trị của họ ở **library rời**, không ở app shell.
2. **TUYỆT ĐỐI KHÔNG dùng tool-sandbox kiểu letta** (E2B/Modal/venv+pip-lúc-chạy) — tool BRAVO là allowlist REST read-only + `create_draft` tĩnh; sandbox arbitrary-code = RCE + đường vòng qua RLS + phá air-gapped, **ZERO lợi ích** (fake-wheel cho BRAVO).

### Quyết định reuse-vs-rewrite từng thành phần
| Thành phần | Quyết định | Ghi chú |
|---|---|---|
| Parsing/ingestion bảng (PDF/DOCX/XLSX **digital**) | **REUSE Docling** (pip-dep chính, không vendor code) | PDF-có-bảng → Docling `do_table_structure=True`; pypdf chỉ fast-path cho PDF text-thuần (user-guide). `do_ocr=False`. |
| Provenance trang/sheet/**cell** | **Bóc từ Docling** `TableItem.prov` + glue BRAVO | Đóng TODO cell_range/sheet_name; không tự reimplement toạ độ ô. |
| Chunking heading-aware + table-whole | **REWRITE-LEAN (giữ)** | Domain-specific BRAVO 10; bug-risk thấp. |
| Agent loop + HITL + checkpointing | **REWRITE-LEAN control-flow + REUSE cơ chế** | Control-flow trong code; mượn Pydantic AI (structured-output) + AgentRun-Postgres; LangGraph/Temporal chỉ khi đo. |
| Agent memory (core/recall/archival) | **REWRITE-LEAN (giữ)** | RLS-on-vector trong SQL ([memory.py:87-98](../../app/agent/memory.py)) là glue letta **không** có. |
| Tool-sandbox/execution | **KHÔNG REUSE (cấm sandbox letta)** | calc.py safe-AST đã đủ; chỉ mượn pattern `return_char_limit`. |
| Embedding/vector/LLM abstraction | **REUSE library (đã đủ)** | sentence-transformers + pgvector + Model Router mỏng. **Không** LiteLLM 12-provider. |
| Rerank (ViRanker) | **REUSE model + glue mỏng** | Không service riêng ở MVP. |
| RLS/permission | **REWRITE (crown jewel)** | Invariant 1, ép IN-query tập trung 1 tầng SQL. |
| Semantic-layer/verify-gate/draft-queue | **REWRITE (độc quyền BRAVO)** | Nghiệp vụ TT99 — không repo nào có. |

### Topology
**GIỮ modular monolith** (xác nhận [ADR-0007](0007-code-strategy.md)) — **không** microservices, **không** run-as-service, **không** monorepo nhiều-package cho MVP (~2.3k LOC, YAGNI). **Phân biệt rõ (chống nguỵ biện):** *"tách PROCESS vì bản chất runtime"* (ĐÚNG, đã có: ① LLM server vLLM/Ollama, ② ingestion worker arq/redis — Docling ML nặng, ③ Postgres+pgvector, ④ Next.js frontend) **KHÁC** *microservices nghiệp vụ* (BÁC). Các infra-process **không tự quyết phân quyền**, nhận lệnh từ monolith **đã ép RLS**; LLM-server + worker **không** chạm DB ERP gốc. `semantic+calc+verify+metric-catalog` là **MỘT nguồn-sự-thật** trong monolith, không nhân bản qua service. Cài air-gapped = **1 docker-compose ~5 image, vài giờ**.

### Framework agent-loop
Control-flow-in-code (ADR-0010). **Bước 1 (MVP):** Pydantic AI làm **library thuần** cho structured tool-output `{metric_id, params, citations}` (validate cuối-run, fail→ABSTAIN) + tự xây **AgentRun/job resumable LEAN trên Postgres lớp AI** (lease + idempotency-key + advisory-lock). **Bước 2 (chỉ khi đo được run dài/HITL nhiều giờ ở spike):** thêm LangGraph-checkpointer-pattern (lấy pattern, **không** cài Platform — egress beacon) hoặc Temporal/Dapr self-host. **Guided/constrained decoding** (XGrammar/guided_json + guided_choice ép metric whitelist) trong vLLM local — điều kiện sống còn cho Qwen cục bộ (backlog ADR, chốt khi có GPU).

## Hệ quả (Consequences)
- **Tích cực:** hoà giải "đừng tái tạo bánh xe" (reuse Docling/lib proven) ⟷ "đừng over-engineer" (không fork app/microservices/sandbox cloud); RLS tập trung giữ nguyên; air-gapped đơn giản; bug-risk thấp ở phần khó (Docling), kiểm soát hoàn toàn phần invariant.
- **Tiêu cực/nợ:** vẫn tự viết glue invariant (đúng — phải thế); phụ thuộc Docling (pin version, test parse CI, bake model offline); cần đo `reliability_horizon` trước khi thêm durable-execution.
- **Ảnh hưởng 4 nguyên tắc:** củng cố #1 (RLS tập trung, không phân tán), #4 (air-gapped 1 compose, reuse chỉ library self-host).
- **Tinh chỉnh ADR:** [ADR-0007] — đọc "chuyển thể CODE docsgpt" = **REUSE Docling như thư viện** (không vendor/fork); thêm "tool-sandbox: không dùng"; thêm mục "Agent runtime". [ADR-0009] — bảng PDF/XLSX **digital** vẫn trong scope qua Docling; chỉ OCR bảng **scan** mới descope; thêm "đóng gói model offline". [ADR-0008] giữ nguyên. [ADR-0010/0011/0012] → **Accepted** (council xác nhận; hành động là IMPLEMENT, không viết ADR mới).

## Lằn ranh chống over-engineering (NON-NEGOTIABLE)
Không run-as-service · không sandbox letta · không LiteLLM 12-provider · không Temporal/Dapr khi chưa đo · không multi-agent · không monorepo/microservices cho MVP · không OCR full-page mặc định · guided-decoding ≠ "LLM tự verify số" · không vendor/fork code Docling · không ép JSON-mode cho cả câu trả lời (chỉ tool_call/metric/citation — CRANE).

## Tham chiếu
[research/findings/K](../research/findings/K-agentic-architecture.md) · Hội đồng 6 lăng kính (6/6 BALANCED_REUSE) · [../AGENTIC-PLAN.md](../AGENTIC-PLAN.md) · [../work-packages/](../work-packages/).
