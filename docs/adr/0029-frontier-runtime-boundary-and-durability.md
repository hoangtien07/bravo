# 0029. Thay lõi orchestration/durability, giữ BRAVO control plane

**Trạng thái:** Proposed

**Ngày:** 2026-07-13

**Supersedes khi Accepted:** phần lựa chọn runtime của ADR 0010 và ADR 0027 OpenAI migration;
không supersede các invariant domain/security

## Bối cảnh

BRAVO đang có hai đường chạy: legacy constrained loop và OpenAI Agents SDK canary text-only.
`AgentRun` lưu status/event/checkpoint nhưng chưa có worker lease/recovery/resume thật; approval hiện chỉ
đánh dấu run hoàn tất. Việc tiếp tục tự bổ sung queue, replay, lease, signal, versioning và duplicate
suppression sẽ biến ứng dụng thành một workflow engine tự xây.

Research ngày 2026-07-13 cho thấy agent SDK và durable workflow engine là hai lớp khác nhau. Không
nền tảng nào thay thế được RLS, egress policy, domain truth, financial verifier, KEDB curation và
maker-checker của BRAVO.

## Quyết định đề xuất

1. **Thay phần orchestration/durable-run tự viết**, không viết lại toàn bộ hệ thống.
2. BRAVO định nghĩa interface trung lập cho run/event/checkpoint/approval/cancel/tool-policy/session.
3. Agent harness là adapter có thể thay: incumbent là OpenAI Agents SDK; Pydantic AI và LangGraph là
   đối chứng bắt buộc.
4. Durable engine là thành phần chuẩn: spike DBOS/Postgres trước; Temporal là fallback scale-up;
   LangSmith Agent Server là buy option.
5. BRAVO control plane luôn sở hữu identity/RLS, tool policy, audit, egress, financial verifier,
   immutable draft intent, approval authority, KEDB và provenance.
6. Không tool nào truy cập DB/ERP ngoài BRAVO Policy Enforcement Point. External side effect phải có
   stable effect key, receipt và idempotency ở domain boundary.
7. Legacy loop chỉ còn rollback cho đến khi candidate qua parity/chaos gate; không thêm feature mới
   ngoài P0 containment.

## Trạng thái lựa chọn

ADR ở `Proposed` vì chưa chạy spike. Kiến trúc chỉ được `Accepted` khi một candidate vượt mọi hard
gate:

- zero RLS leak và zero approval bypass;
- zero duplicate write qua crash/retry/resume đồng thời;
- approval chờ dài hạn resume đúng một lần;
- reconnect/replay không mất semantic state;
- sensitive path self-host, không forced cloud trace/egress;
- license cho phép use/distribution;
- rollback về legacy cho new runs trong một release window.

Điểm nghiên cứu hiện tại: OpenAI Agents + DBOS 89; Pydantic AI + DBOS 86; Pydantic AI + Temporal 85;
LangGraph + self-host Agent Server 85. Điểm không bù được hard-gate failure.

## Hệ quả

### Tích cực

- Loại bỏ phần lớn code lease/retry/recovery/HITL resume tự viết.
- Provider/runtime thay được mà không chạm RLS, domain và UI protocol.
- Durable event/signal tạo nền cho long-running approval, cancellation và replay thật.
- KEDB/memory trở thành domain service có governance, không phụ thuộc framework memory.

### Chi phí và rủi ro

- Cần migration state/event schema và chaos test thực tế.
- DBOS distributed recovery phải được chứng minh; nếu không đạt sẽ chuyển Temporal.
- Pydantic v1→v2 và LangSmith commercial server tạo migration/license risk.
- Trong giai đoạn canary phải duy trì hai runtime nhưng tuyệt đối không dual-execute write effect.

## Điều kiện xem xét lại

- DBOS không đạt multi-worker recovery hoặc workflow versioning SLO.
- Temporal TCO thấp hơn custom operational burden ở quy mô thật.
- OpenAI harness không đạt local-provider/multimodal/tool parity.
- Pydantic AI/LangGraph chứng minh giảm ≥30% integration code và đạt mọi hard gate.
- Full GraphRAG chỉ xem xét riêng khi relation-heavy benchmark thắng metadata-routed hybrid retrieval.

## Tài liệu liên quan

- [Decision pack](../research/FRONTIER-AGENT-RUNTIME-DECISION-PACK-2026-07-13.md)
- [ADR 0010](0010-agent-loop-architecture.md)
- [ADR 0027 OpenAI migration](0027-openai-agents-runtime-migration.md)
- [ADR 0028 GraphRAG gate](0028-frontier-optional-surfaces-and-graphrag-gate.md)
