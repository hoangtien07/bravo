# WP-D — Agent loop (Pydantic AI) + tool schema + RLS-filter + circuit breaker

> Module: `app/agent`. **Đọc [CONTRACTS.md](CONTRACTS.md) trước.** Hiện thực [ADR-0010](../adr/0010-agent-loop-architecture.md). Phụ thuộc (qua interface): WP-B, WP-C, WP-E.

## Mục tiêu
Thay [loop.py] single-shot bằng **single-agent ReAct loop NGẮN, control-flow trong code**: LLM chọn tool (structured-output), engine thực thi, verify-gate, diễn giải. Đây là lõi Demo B.

## Reuse (ADR-0013) — quan trọng
- **REUSE Pydantic AI** làm library thuần cho **structured tool-output** `{tool, args}`/`{metric_id, params, citations}` (validate cuối-run, fail→ABSTAIN). **Không** tự viết parser tool-call.
- **Control-flow vẫn ở code Python** — Pydantic AI chỉ ép cấu trúc output, KHÔNG sở hữu vòng lặp (để chèn RLS/verify/HITL gate, chống reward-hacking).
- **Không** LangGraph/Temporal ở MVP (chỉ thêm khi spike đo run dài — [ADR-0013]).

## Scope IN / OUT
**IN:** vòng lặp `<= Budget` (CONTRACTS §2.7) enforce cứng; tool schema (CONTRACTS §2.2 — thêm `json_schema/read_only/required_permission`); `filter_tools_by_permission` (tool thiếu quyền không vào prompt) + chặn lần 2 ở `call_tool`; gọi `grounding.verify_numbers` (WP-B) trước khi trả; gọi `router.chat(context=...)` (WP-C); write tool → `draft_queue.create_draft` (WP-E); `clarify` khi mơ hồ (hỏi lại, không đoán).
**OUT (đừng làm):** multi-agent/sub-agent tự hành; heartbeat tự chạy không giới hạn; LLM sở hữu control-flow; guided-decoding (backlog — cloud function-calling đã đủ cho demo); để LLM tự verify số.

## Files
`app/agent/loop.py` (viết lại ReAct loop) · `tools.py` (mở rộng Tool + `filter_tools_by_permission` + `call_tool`).

## Việc cụ thể
1. `Tool` mở rộng theo CONTRACTS §2.2; `REGISTRY` đăng ký `kb_search` (đã có) + (WP-F) `metric_*` tools.
2. `filter_tools_by_permission(registry, identity)` → loại tool `required_permission` mà identity không có.
3. Loop: `retrieve → llm_structured(tools) → call_tool → observe → (lặp <= max_steps) → answer → verify_numbers → safe_answer`. Mỗi vòng kiểm `Budget` trước (vượt → dừng + `AuditLog`).
4. `call_tool`: kiểm quyền **lần 2** (defense-in-depth); `read_only=False` → `create_draft` (không execute); trả `isError` thay vì raise (giữ loop sống).
5. `clarify`: nếu structured-output báo thiếu tham số/mơ hồ → trả câu hỏi lại.

## Acceptance (test)
- Trajectory 2-bước trên KB chạy được; `max_steps` vượt → dừng + audit.
- Tool `read_only=False` → tạo draft, KHÔNG execute (đếm: 0 lần ghi trực tiếp).
- User thiếu quyền → tool không trong danh sách gửi LLM VÀ `call_tool` trả `isError`.
- answer có số → đi qua `verify_numbers`; số không khớp → mask (nối WP-B).
- p95 loop 2-bước ≤ 8s (đo, không hard-fail demo).

## Invariant
#1 (RLS-filter tool 2 lớp) · #2 (write→draft) · #3 (verify-gate trong loop, không sinh số) · #4 (router.chat egress).

## Phụ thuộc
WP-B (`verify_numbers`, MetricResult) · WP-C (`router.chat(context=)`) · WP-E (`create_draft`, AgentRun). Build song song dùng **stub** các hàm này (chữ ký ở CONTRACTS §3.1).
