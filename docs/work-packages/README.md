# Work Packages — gói việc song song để code BRAVO agentic (demo)

> Mục đích: chia việc thành các **gói tự-chứa** để mở **nhiều Claude chat làm đồng thời**. Mỗi gói = một spec cho một chat. Viết để **Opus 4.8 hiểu & implement** mà **không over-engineer**.
> **Trạng thái: CHƯA CODE.** Đây là spec. Hướng kiến trúc: [ADR-0013 BALANCED_REUSE](../adr/0013-reuse-vs-rewrite-and-topology.md). Scope demo: [AGENTIC-PLAN.md](../AGENTIC-PLAN.md).

## Luật cho MỖI Claude chat (đọc trước khi code)
1. **Đọc [CONTRACTS.md](CONTRACTS.md) TRƯỚC** — nó định nghĩa mọi interface dùng chung. Code đúng theo hợp đồng → các gói ghép được mà không cần biết nội bộ của nhau.
2. **Chỉ sửa file trong "Scope" của gói mình.** Đụng file của gói khác → chỉ qua interface ở CONTRACTS, không sửa nội bộ.
3. **Tôn trọng 4 nguyên tắc bất biến** ([CLAUDE.md](../../CLAUDE.md)) + **lằn ranh chống over-engineering** (CONTRACTS §5). Mỗi gói có checklist invariant riêng.
4. **Reuse theo [ADR-0013](../adr/0013-reuse-vs-rewrite-and-topology.md):** dùng library proven cho "bánh xe thật" (Docling, Pydantic AI, sentence-transformers); **không** fork app, **không** sandbox letta, **không** microservices.
5. **Acceptance = test.** Mỗi gói "xong" khi test ở mục Acceptance xanh. Viết test cùng code.
6. **Phạm vi demo:** cloud LLM (máy yếu) + mock financial data (TT99) + KB. **Không** ERP thật, **không** local Qwen, **không** Phase 3 push-to-ERP.

## Danh sách gói & đồ thị phụ thuộc

| Gói | Tên | Module chính | Phụ thuộc (qua interface) |
|---|---|---|---|
| [WP-A](WP-A-ingestion-docling.md) | Ingestion Docling + provenance (page/sheet/cell) + nạp corpus Demo A | `app/ingestion` | — |
| [WP-B](WP-B-verify-gate.md) | Verify-gate: value-object + Decimal + nối gate vào loop | `app/data_layer` | CONTRACTS (MetricResult) |
| [WP-C](WP-C-egress-router.md) | Egress classify + audit-then-egress | `app/llm`, `app/security` | — |
| [WP-D](WP-D-agent-loop.md) | Agent loop (Pydantic AI) + tool schema + RLS-filter + circuit breaker | `app/agent` | WP-B, WP-C, WP-E (interface) |
| [WP-E](WP-E-agentrun-draft.md) | AgentRun durable + draft-queue hardening (HITL) | `app/database`, `app/erp` | CONTRACTS (AgentRun, Draft) |
| [WP-F](WP-F-mock-semantic.md) | Mock DataSource + semantic-RLS + catalog TT99 + variants | `app/data_layer` | WP-B (MetricResult) |
| [WP-G](WP-G-rls-memory-hardening.md) | RLS agentic hardening + memory provenance/untrusted | `app/security`, `app/agent` | — |
| [WP-H](WP-H-eval-passk.md) | Golden-trajectory + pass^k harness (CI hard gate) | `app/eval` | tất cả (chạy E2E) — viết stub-tolerant |

## Sóng làm song song (gợi ý)
- **Sóng 1 (độc lập, chạy ngay đồng thời):** WP-A · WP-B · WP-C · WP-E · WP-G · WP-H(khung).
- **Sóng 2 (sau khi interface Sóng 1 ổn):** WP-D (lắp loop dùng B/C/E) · WP-F (mock dùng B).
- **Sóng 3:** WP-H điền golden trajectory đầy đủ + bật CI gate; nạp corpus Demo A (WP-A) chạy thật.

> Mỗi gói tự-chứa: một chat có thể làm WP-X chỉ với CONTRACTS + spec WP-X, dùng **stub** cho interface của gói chưa xong (CONTRACTS cung cấp stub mẫu).

## Việc KHÔNG thuộc demo (để sau, đừng làm bây giờ — chống over-engineer)
ERP `erp/client` thật · local Qwen + guided decoding + air-gapped packaging · Phase 3 journal-validator + push-to-ERP staging · Temporal/Dapr durable-execution · LangGraph Platform. Xem [AGENTIC-PLAN §Deferred](../AGENTIC-PLAN.md).

## Việc cần BRAVO (không phải code)
Xác nhận **ngữ nghĩa metric** (gross/net, VAT, accrual/cash, kỳ khoá sổ) theo **TT99** trước khi nối DataSource thật; ngành demo (mặc định Thép xây dựng); ngày giao ERP API.
