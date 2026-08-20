# Architecture Decision Records (ADR)

> **Numbering note:** two accepted decisions were historically created with prefix `0027`.
> This index assigns stable aliases `0027a` (feedback) and `0027b` (OpenAI runtime migration).
> Do not infer that they are the same ADR. Renumbering/moving accepted ADRs requires a separate
> owner decision because existing documents reference both filenames.

Mỗi ADR ghi lại **một** quyết định kiến trúc quan trọng tại thời điểm đưa ra: bối cảnh, các phương án, lựa chọn và hệ quả. ADR là *bất biến* sau khi `Accepted` — muốn đổi thì viết ADR mới thay thế.

Tạo ADR mới: dùng skill **`/adr-new`** (tự đánh số, theo mẫu, cập nhật index này).

## Index

| # | Tiêu đề | Trạng thái | Ngày |
|---|---------|-----------|------|
| [0001](0001-record-architecture-decisions.md) | Dùng ADR để ghi quyết định kiến trúc | Accepted | 2026-06-08 |
| [0002](0002-architecture-as-synthesis-of-three-repos.md) | Kiến trúc = tổng hợp pattern từ arkon + docsgpt + letta (mượn, không fork) | Accepted | 2026-06-08 |
| [0003](0003-hybrid-llm-strategy.md) | Chiến lược LLM Hybrid: local mặc định + cloud opt-in có kiểm soát theo độ nhạy | Accepted | 2026-06-08 |
| [0004](0004-llm-never-computes-numbers.md) | LLM không bao giờ tự tính số liệu — tầng tính toán deterministic | Accepted | 2026-06-08 |
| [0005](0005-no-free-form-sql.md) | Không sinh SQL tự do trên ERP — semantic layer / view kế toán đã duyệt | Accepted | 2026-06-08 |
| [0006](0006-market-positioning.md) | Định vị thị trường: "AI tài chính có chủ quyền & không bịa số" | Accepted | 2026-06-08 |
| [0007](0007-code-strategy.md) | Chiến lược code: lõi greenfield hợp nhất, modular-monolith; mượn pattern/chuyển thể | Accepted | 2026-06-08 |
| [0008](0008-arkon-license-ownership.md) | arkon = chỉ học pattern, **VIẾT LẠI** — không tái dùng code (gỡ rủi ro PolyForm) | Accepted | 2026-06-09 |
| [0009](0009-local-model-stack.md) | Bộ model cục bộ: Qwen2.5-32B + bge-m3 + VietOCR | Accepted | 2026-06-08 |
| [0010](0010-agent-loop-architecture.md) | Agent loop: Constrained Agentic — single-agent, deterministic-backbone, control-flow-in-code | Accepted | 2026-06-11 |
| [0011](0011-egress-classification-audit.md) | Phân loại độ nhạy tự động & audit-then-egress cho Model Router | Accepted | 2026-06-11 |
| [0012](0012-verify-gate-number-integrity.md) | Verify-gate value-object & toàn vẹn số liệu (nối gate vào loop, đơn vị, Decimal) | Accepted | 2026-06-11 |
| [0013](0013-reuse-vs-rewrite-and-topology.md) | Reuse-vs-rewrite & topology: BALANCED_REUSE (reuse library proven, hand-roll glue invariant, modular-monolith) | Accepted | 2026-06-11 |
| [0014](0014-journal-entry-validator.md) | Journal-entry validator: Nợ=Có là invariant cứng (deterministic) | Accepted | 2026-06-15 |
| [0015](0015-chat-conversation-sse.md) | Tầng hội thoại (Conversation) + SSE streaming | Accepted | 2026-06-15 |
| [0016](0016-pivot-standalone-ap-vertical.md) | Mũi nhọn đầu = "Copilot AP" độc lập (ship trên chứng từ upload, không phụ thuộc ERP API) | **Accepted** | 2026-07-05 |
| [0017](0017-internal-demo-feature-package.md) | Gói tính năng DEMO NỘI BỘ: Knowledge Graph + AP đầy đủ + agent trên mock (nới tạm freeze 0016) | Accepted | 2026-06-29 |
| [0018](0018-agentic-packaging-knowledge-as-data.md) | Đóng gói agentic: knowledge/rule-as-data + config-as-boot (single-tenant); cổng L3 cho multi-tenant/DSL; mốc chuyển-local trước dữ liệu thật | Accepted (hẹp) | 2026-07-09 |
| [0019](0019-cloud-only-llm-strategy.md) | Chiến lược LLM **CLOUD-ONLY** v2.0 (nghỉ hưu local mặc định) — supersedes 0003/0009 | **Accepted** | 2026-07-12 |
| [0020](0020-positioning-v2-cloud.md) | Định vị v2.0 — moat = nghiệp vụ BRAVO + kỷ luật số (không phải chủ quyền) — supersedes 0006 | **Accepted** | 2026-07-12 |
| [0021](0021-labeled-world-knowledge-mode.md) | Chế độ trả lời "kiến thức chung" có nhãn (thay hard-abstain); số vẫn gated | **Accepted** | 2026-07-12 |
| [0022](0022-egress-guard-to-audit.md) | Egress GUARD → AUDIT (giữ code phân loại, đổi vai trò dưới cloud-only) — amends 0011 | **Accepted** | 2026-07-12 |
| [0024](0024-sse-protocol-v2.md) | SSE protocol v2 cho frontier chat | Accepted | 2026-07-13 |
| [0025](0025-attachment-turn-binding.md) | Gắn attachment theo lượt hội thoại | Accepted | 2026-07-13 |
| [0026](0026-linear-edit-regenerate.md) | Edit/regenerate tuyến tính có audit | Accepted | 2026-07-13 |
| [0027a](0027-feedback-report-to-it.md) | Feedback và báo cáo sang IT | Accepted | 2026-07-13 |
| [0027b](0027-openai-agents-runtime-migration.md) | Di trú runtime sang OpenAI Agents SDK theo canary | Accepted | 2026-07-13 |
| [0028](0028-frontier-optional-surfaces-and-graphrag-gate.md) | Optional frontier surfaces và cổng GraphRAG | Accepted | 2026-07-13 |
| [0029](0029-frontier-runtime-boundary-and-durability.md) | Thay lõi orchestration/durability, giữ BRAVO control plane | **Proposed** | 2026-07-13 |
| [0031](0031-first-pilot-ap-vertical-gate.md) | Pilot đóng cổng = U2 (Copilot AP) đơn lẻ; U1 tri thức là tiện ích nền | Superseded before acceptance by 0032 | 2026-07-20 |
| [0032](0032-first-v2-demonstrator-reconciliation-exception.md) | Demonstrator sâu đầu tiên của V2 = Reconciliation & Exception Investigator | **Accepted** | 2026-07-31 |
| [0033](0033-three-case-demo-and-owner-package.md) | Demo ba case + owner package về data/topology/egress/integration/release gate | **Accepted** | 2026-07-31 |
| [0034](0034-conversation-v2-contract-boundary.md) | Ranh giới contract Knowledge Chat Conversation Core V2 | **Accepted — design-only** | 2026-08-18 |
| [0035](0035-standalone-file-evidence-and-artifact-workspace.md) | FigmaMake-only, file evidence và bounded Artifact Workspace | **Accepted** | 2026-08-19 |

> ADR 0010-0013 được **Hội đồng (2 vòng) xác nhận**. 0012 (verify-gate) **đã implement** — nối vào agent loop (`app/agent/loop.py`, gate `verify_numbers` tại `_finish_answer`), có test (`tests/test_grounding.py`). Trạng thái triển khai chi tiết: **nguồn sự thật = [../work-packages/STATUS.md](../work-packages/STATUS.md)**. Đánh giá tổng thể mức độ trưởng thành: [../COUNCIL-REVIEW-2026-07.md](../COUNCIL-REVIEW-2026-07.md).

## Quyết định đang chờ (backlog — sẽ thành ADR khi chốt)
Tham chiếu [../ARCHITECTURE.md §5](../ARCHITECTURE.md) và [../VISION.md §8](../VISION.md):
- Vector store: pgvector vs Qdrant/Milvus.
- ~~Model LLM cục bộ~~ → **đã chốt [0009](0009-local-model-stack.md)** (Qwen2.5-32B + bge-m3 + VietOCR). Còn mở: vLLM vs Ollama; danh sách nhà cung cấp cloud.
- ~~Reranker cục bộ có/không~~ → **CÓ** (rerank là đòn bẩy chất lượng #1 — [findings/J](../research/findings/J-rag-agent-eval.md)); ViRanker/Cohere.
- Semantic layer: Cube vs dbt MetricFlow ([findings/H](../research/findings/H-data-layer-techniques.md) nghiêng Cube — MCP + finance).
- Lược đồ phân loại độ nhạy (sensitivity classification) & cơ chế cấu hình policy egress theo khách; có/không lớp redaction PII.
- Mức dùng pipeline biên soạn (MRP) vs RAG trực tiếp theo loại nội dung.
- Cơ chế tích hợp ERP: đồng bộ phòng ban/quyền với ERP vs tự quản trị; danh mục view/API đọc được duyệt.
- Reranker cục bộ: có/không.

### Backlog ADR cho agentic (theo [../AGENTIC-PLAN.md](../AGENTIC-PLAN.md))
- Guided/constrained decoding (XGrammar/CRANE) cho Qwen cục bộ — chốt khi triển khai LLM local (có GPU).
- AgentRun durable (Postgres-native, lease/idempotency) — chốt khi tới Phase 3.
- Journal-entry validator contract (ΣNợ=ΣCó/kỳ khoá sổ) — điều kiện khởi động Phase 3.
- Semantic-layer RLS scope-binding bắt buộc (bổ sung [0005](0005-no-free-form-sql.md)).
- Chuẩn mực kế toán áp dụng (TT99/2025 mặc định) + năm tài chính per-metric/draft.
- Eval pass^k governance (k≥8, HARD-FAIL set) — mở rộng cổng ra ROADMAP.
- Revision [0009](0009-local-model-stack.md): VRAM theo tải agentic (trọng số + KV-cache + headroom); pilot 14B-AWQ.
