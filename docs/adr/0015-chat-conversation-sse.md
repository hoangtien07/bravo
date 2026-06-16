# ADR-0015 — Tầng hội thoại (Conversation) + SSE streaming

- **Trạng thái:** Accepted
- **Ngày:** 2026-06-15
- **Liên quan:** ADR-0010 (agent loop), WP-G (DATA-frame memory), invariant #1/#3/#4.

## Bối cảnh
BRAVO có xương sống chat (ConversationMessage, MemoryStore, AgentSession.step(session_id))
nhưng multi-turn hỏng (loop không nạp lịch sử) và chưa có UI/API hội thoại/streaming. Xây
nền tảng chat (React SPA + backend) học pattern docsgpt/letta/arkon nhưng giữ on-prem +
anti-over-engineering.

## Quyết định
1. **`Conversation.id == session_id` (1:1)** — tái dùng key sẵn có, không remap. Conversation
   giữ chủ sở hữu (employee_id) + title + last_message_at + shared_token.
2. **RLS THEO NGƯỜI DÙNG** cho hội thoại (`conversation_scope_filter`: employee_id == me;
   admin = all) — khác RLS dept-scope của chunks. Non-owner → 404 (không lộ tồn tại).
   Ownership HARD-check khi post (chống forgery session_id).
3. **Multi-turn**: nạp `recall_recent_for_prompt` (đã DATA-frame, WP-G) vào prompt — lịch sử
   nằm TRƯỚC câu hỏi hiện tại; best-effort để unit-test (DB giả) không vỡ.
4. **SSE qua POST + fetch ReadableStream** (KHÔNG EventSource — vì bearer auth cần header).
   `step_stream()` async generator yield event {id, source, step, tool_call, tool_result,
   draft, answer, done, error, ping}.
5. **2 pha**: bước DECIDE không stream (JSON strict, Pydantic AI parse); chỉ câu trả lời cuối
   stream — **v1 chunk chuỗi `decision.answer`** (1 LLM call/step, tránh rủi ro thứ-tự
   egress-audit). True token-streaming = follow-up.
6. **Verify-gate (invariant #3)**: chạy trên answer ĐẦY ĐỦ TRƯỚC khi stream bản safe (đường
   có engine_values) — không lọt số chưa kiểm chứng qua các `answer` delta.
7. **Feedback = cột** trên ConversationMessage (không bảng riêng). **Chia sẻ** read-only qua
   shared_token (256-bit, tra trực tiếp, không lộ employee_id).
8. **Single-process generator** (1 DB session/stream) cho v1. KHÔNG message-events-journal /
   reconnect / compaction / Redis pub/sub (over-engineering của docsgpt) — đưa vào backlog.

## Hệ quả
- (+) Multi-turn hoạt động; chat có lịch sử theo người dùng + streaming + chia sẻ.
- (+) Tái dùng toàn bộ loop/draft/verify-gate/RLS — không phân tán logic.
- (−) SSE giữ 1 DB session suốt stream; multi-worker cần Redis pub/sub (future).
- (−) recall không compaction (limit 20) → chat dài cắt ngữ cảnh (chấp nhận v1).
- (−) Client ngắt giữa chừng có thể để AgentRun ở 'running' (chấp nhận; draft idempotent).
