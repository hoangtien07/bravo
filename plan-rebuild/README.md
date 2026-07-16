# BRAVO AI Copilot Rebuild Research Workspace

Thư mục này là nguồn sự thật cho quyết định rebuild BRAVO AI Copilot và toàn bộ nghiên cứu tạo ra trước quyết định đó.

## Phạm vi hiện tại

1. Khảo sát BravoGen bằng phương pháp black-box được phép qua ba mode: Bravo User Guide, Bravo Insight và ISMS Advisor.
2. Ghi nhận hành vi quan sát được; không tìm cách lấy system prompt, credential, dữ liệu riêng hay bí mật triển khai.
3. Không mặc định BravoGen dùng GraphRAG, graph database, tool calling, multi-agent, model hoặc framework cụ thể.
4. Chưa áp dụng P1/P2 từ tài liệu đính kèm vào codebase hiện tại. P1/P2 chỉ được xem xét lại sau khi P0 có đủ bằng chứng và decision gate được mở.
5. Tất cả kết luận phải mang nhãn `OBSERVED`, `INFERRED` hoặc `UNVERIFIED`.

## Cấu trúc

- `08-V2-CONVERSATION-REBUILD-HANDOFF.md`: quyết định của chủ dự án chuyển sang
  Conversation Core V2, council blockers, implementation sequence, acceptance gates và read order
  để tiếp tục an toàn trong một luồng hội thoại khác.

- `04-WORKSPACE-REPO-COUNCIL-DECISION.md`: council decision về các repo trong workspace, nguyên tắc kiến trúc, ranh giới strangler và complexity budget.
- `05-BRAVO-ENGINEERING-WORKBENCH-CONTRACT.md`: pipeline kỹ thuật kiểu Atlas cho canonical case, workspace/diff, validator, build/test và adapter IDE/web.
- `06-RESEARCH-AND-IMPLEMENTATION-ROUNDS.md`: chia scope thành foundation chung rồi hai track Conversation Intelligence và Engineering Workbench có gate độc lập.
- `07-CONVERSATION-INTELLIGENCE-BRAVOGEN-BENCHMARK.md`: kiến trúc reasoning hội thoại, chẩn đoán model/retrieval/code và benchmark riêng với BravoGen.

- `00-CURRENT-REBUILD-DECISION.md`: quyết định và giả thuyết rebuild hiện tại.
- `01-MASTER-EXECUTION-PLAN.md`: kế hoạch tổng thể, gates và thứ tự thực hiện.
- `02-R1-DECISION-BENCHMARK-PLAN.md`: kế hoạch bake-off để tách ảnh hưởng model, retrieval và reasoning core.
- `03-OSS-CORE-DECISION-PYDANTIC-LANGGRAPH-ZENML-KITARU.md`: đánh giá Deep Research và quyết định implementation profile cho System C; phân vai Pydantic AI, LangGraph, Kitaru và ZenML.
- `bravogen-p0/`: kế hoạch, raw log và báo cáo khảo sát BravoGen.

## Quy tắc dữ liệu

- Không lưu bearer token, cookie hoặc thông tin xác thực trong thư mục này.
- Chỉ gửi test case không chứa dữ liệu khách hàng và nằm trong phạm vi đã được người dùng cho phép.
- Raw output phải được lưu nguyên văn; phân tích không được thay thế raw output.
- Tự thuật của chatbot về tool/graph/router chỉ là `UNVERIFIED` cho tới khi có kiểm thử hành vi hỗ trợ.

## Current gate status

The permitted black-box collection and formal R0 gate are complete. `P0-20-exit-criteria-audit.md` records 34+ prior independent cases plus the P0-21 strict closure set: five identical anchors across all three modes (15/15 valid observations) and two completed independent Insight repeats. Fabricated-entity, citation, graph and memory coverage are present with historical quota/error attempts preserved separately. This authorizes the rebuild-design decision phase; it does not prove BravoGen's internal GraphRAG, workflow engine, self-learning or authorization implementation.

Post-processing in `P0-22-r0-quality-scoring.json` and `P0-23-r0-post-analysis.md` separates behavioral usefulness from evidence quality. R1 is **design-ready but not execution-ready**: documentation cleanup, an immutable A/B baseline, and fixture/SME ownership must be closed before the matched-model bake-off. New feature expansion remains frozen until that bake-off produces a core decision.

## Decision gate

Không bắt đầu xây dự án mới hoặc sửa sâu dự án cũ từ kết quả tự thuật của BravoGen. Decision gate chỉ mở sau khi:

- P0 đạt điều kiện hoàn thành;
- có baseline chất lượng của hệ thống hiện tại và BravoGen;
- có vertical-slice acceptance criteria;
- có so sánh chi phí/rủi ro giữa clean project dựa trên OSS và tiếp tục sửa legacy.
