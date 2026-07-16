# P0-09 — Behavioral architecture hypotheses

Status: `COMPLETE AS BEHAVIORAL HYPOTHESES — no implementation claims`

Các giả thuyết được phép so sánh sau khi có dữ liệu:

- một model với nhiều policy/prompt profile;
- nhiều agent dùng chung retriever;
- router và agent/tool chuyên môn;
- semantic RAG tạo graph-like synthesis;
- hybrid retrieval kết hợp dữ liệu quan hệ có cấu trúc.

| Hypothesis | Supporting evidence | Contradicting evidence | Distinguishing next test | Confidence |
|---|---|---|---|---|
| Mode/profile policy bundle affects routing and output contract | Cross-mode Layout XML boundary; mode-specific refusal and response shapes | Same underlying corpus could be filtered by prompt only | Neutral same-intent prompt with identical context and independently captured source/tool traces | Medium |
| Retrieval includes structured relationship or graph-like synthesis | T06.1–T06.3 direct/inferred edges, traversal depth, event IDs; T13.3 `knowledge_graph` label | No auditable graph payload; T06.4 no-result layer unknown | Repeat traversal with fixed fixtures and compare stable node/edge/provenance output | Medium |
| Context-slot tracking drives follow-up questions and updates | T13.1–T13.4 preserve version/environment/goal and mutate platform only | Durable persistence and storage are unknown | New conversation, branch/stop/continue and correction probes with slot-level assertions | Medium-high |
| Safety policy gate precedes risky action | T11.1/T11.2/T12.1 refuse payroll structure/SQL and route to approval | No authorization/tool trace; prompts explicitly requested refusal | Neutral risky prompt with tool telemetry and controlled permission fixtures | Medium-high |
| Citation generation is separable from claim verification | T04.3 valid quote; T01.6 partial page support; T05.2 detects malformed links | Only a small live sample was audited | Claim-level citation benchmark over known pages and negative/fake sources | High |

Không ghi tên model, provider, graph DB hoặc framework nếu không có bằng chứng công khai độc lập.
