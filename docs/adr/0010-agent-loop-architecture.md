# 0010. Kiến trúc Agent loop: Constrained Agentic — single-agent, deterministic-backbone, control-flow-in-code

- **Trạng thái:** Accepted (Hội đồng 2026-06-11 xác nhận — [ADR-0013](0013-reuse-vs-rewrite-and-topology.md))
- **Ngày:** 2026-06-10 (Accepted 2026-06-11)
- **Người quyết định:** Đội dự án BRAVO AI Copilot (sau nghiên cứu agentic + 2 vòng Hội đồng)
- **Bổ sung (council 2026-06-11):** Agent runtime = Pydantic AI (structured-output lib thuần) + AgentRun durable tự xây trên Postgres lớp AI ở MVP; LangGraph-checkpointer-pattern/Temporal chỉ khi đo được `reliability_horizon` ở spike. Đây là BLOCKING cho demo agentic.
- **Liên quan:** [ADR-0004](0004-llm-never-computes-numbers.md), [ADR-0005](0005-no-free-form-sql.md), [ADR-0011](0011-egress-classification-audit.md), [ADR-0012](0012-verify-gate-number-integrity.md), [../AGENTIC-PLAN.md](../AGENTIC-PLAN.md), [../research/findings/K-agentic-architecture.md](../research/findings/K-agentic-architecture.md)

## Bối cảnh (Context)
[loop.py](../../app/agent/loop.py) hiện là **single-shot RAG** (1 lời gọi LLM/lượt, model chưa tự chọn tool). Để có năng lực agentic (Demo B: hỏi-đáp số đa-bước, suy luận liên-nguồn), cần một vòng lặp agent thật. Nghiên cứu agentic (8 luồng) + Hội đồng đồng thuận tuyệt đối: **độ tin cậy của agent đến từ kiến trúc rào chắn, không phải model thông minh + bag-of-tools + loop**. Rủi ro lớn: compounding error (0.95^20≈36%), model nhỏ cục bộ sụp ở multi-turn, multi-agent tốn ~15x token + cascading error. Phải chốt **hình dạng** vòng lặp trước khi code.

## Các phương án đã cân nhắc (Options)
1. **Autonomous agent (LLM sở hữu control flow, tự do tool-calling, heartbeat tự chạy như Letta).** Ưu: linh hoạt. Nhược: control flow do LLM → không deterministic, khó chèn HITL/RLS gate, compounding error, model cục bộ không kham nổi. **Bị loại** (phá invariant 2/3, rủi ro độ tin cậy).
2. **Multi-agent / group-chat tự điều phối (AutoGen/CrewAI).** Ưu: phân rã tác vụ rộng. Nhược: BRAVO là domain shared-context (cùng user/RLS/tập số) → anti-pattern theo cả Anthropic lẫn Cognition; ~15x token; cascading error; không ép RLS theo quyền end-user. **Bị loại.**
3. **Workflow có rào chắn + single-agent loop NGẮN, control-flow-in-code (LLM-in-the-slot).** Control flow (routing → chọn tool/metric → thực thi deterministic → verify → diễn giải) nằm trong code Python; LLM chỉ điền vào khe được phép. Loop ngắn + circuit breaker cứng. Ưu: deterministic, debuggable, chèn được HITL/RLS/verify ở mọi bước, hợp model cục bộ. Nhược: kém "tự hành" — nhưng đó là **đặc tính mong muốn** cho domain tài chính.

## Quyết định (Decision)
Chọn **Phương án 3 — Constrained Agentic**. Cụ thể:

1. **Control flow nằm trong code, KHÔNG để LLM sở hữu.** LLM chỉ: chọn tool/metric (trong whitelist), viết diễn giải tiếng Việt. Mọi quyết định bất khả hồi (ghi nháp, rời mạng) đi qua gate ở code.
2. **Single-agent.** Tối đa dùng sub-agent **read-only** trả summary cô đọng cho một orchestrator đơn-luồng; **không** nhiều agent ghi song song; mọi ghi qua **một** đường draft-queue tuần tự.
3. **Loop NGẮN + circuit breaker CỨNG.** `Budget(max_steps, max_tokens, deadline)` **enforce** — chặn lời gọi tiếp theo (không chỉ cảnh báo), kiểm trước mỗi tool-call/LLM-call. Ưu tiên 1-2 tool-call/nhiệm vụ; >3-4 bước → checkpoint người. `max_steps` ban đầu đặt theo `reliability_horizon` đo ở spike ([../AGENTIC-SPIKE-WS0.md](../AGENTIC-SPIKE-WS0.md)).
4. **Mỗi vòng đi qua các gate sẵn có:** retrieve RLS → LLM chọn tool (guided khi dùng Qwen cục bộ — backlog ADR) → `call_tool` (RLS-filter lần hai + `requires_approval` cho write) → **verify-gate** ([ADR-0012](0012-verify-gate-number-integrity.md)) → diễn giải.
5. **State externalize ra code/memory ngoài context** (chống self-conditioning); không giữ trạng thái trong context dài.
6. **HITL-as-tool:** `requires_approval` là thuộc tính **cứng** ở code (đã có [tools.py:18](../../app/agent/tools.py)); LLM không tự quyết khi nào cần duyệt.

## Hệ quả (Consequences)
- **Tích cực:** deterministic & auditable; chèn được RLS/verify/HITL ở mọi bước; chạy được trên model cục bộ yếu (loop ngắn); chống compounding/cascading error; là điểm bán "AI có kiểm soát".
- **Tiêu cực / nợ kỹ thuật:** kém linh hoạt hơn agent tự hành (chấp nhận — đúng domain); kỹ sư phải tự định nghĩa control flow cho mỗi loại tác vụ; cần `Budget`/circuit-breaker + đo `reliability_horizon`.
- **Ảnh hưởng 4 nguyên tắc:** **củng cố** #2 (HITL-as-tool, không tự ghi) và #3 (LLM không sở hữu quyết định số); tương thích #1 (RLS gate trong loop) và #4 (loop ngắn dễ chạy local).
- **Việc tiếp:** backlog ADR — guided decoding cho Qwen cục bộ; AgentRun durable (Postgres-native) khi tới Phase 3.

## Tham chiếu
Anthropic "Building effective agents" · Cognition "Don't Build Multi-Agents" · 12-factor agents (factor 7/8) · [../research/findings/K-agentic-architecture.md](../research/findings/K-agentic-architecture.md). Hội đồng: consensus #1 (deterministic backbone), pitfall #4/#6 (compounding/multi-agent).
