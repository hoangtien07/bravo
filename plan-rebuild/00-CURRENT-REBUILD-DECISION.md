# Quyết định rebuild hiện tại

## Vấn đề cần giải quyết

Chatbot hiện tại có thể lấy lại nội dung và tạo câu trả lời có vẻ đúng, nhưng thường dừng ở mức diễn đạt lại yêu cầu. Nó chưa ổn định trong việc nối tri thức nghiệp vụ kế toán/ERP, trình tự thao tác Bravo 10, điều kiện trước–sau, cấu hình kỹ thuật, rủi ro và bước kiểm thử thành một phương án tư vấn hữu ích.

Ví dụ điển hình: khi người dùng hỏi cách lên báo cáo tài chính, hệ thống không nên chỉ chỉ đường mở báo cáo. Nó phải nhận ra chuỗi điều kiện như ghi nhận chứng từ, kiểm tra hạch toán, đối chiếu, phân bổ/kết chuyển, khóa kỳ và kiểm tra sai lệch trước khi xem báo cáo.

## Câu hỏi quyết định

Đối với một solo developer, phương án nào cho chất lượng hội thoại và khả năng phát triển bền vững tốt hơn:

1. tiếp tục review/fix dự án hiện tại; hoặc
2. tạo một dự án sạch, dùng các OSS/runtime SDK trưởng thành làm nền, rồi port có chọn lọc tri thức, benchmark và guardrail đã chứng minh giá trị?

Đây không phải câu hỏi chọn LangGraph hay OpenAI Agents SDK. Framework phải là chi tiết thay thế được sau một adapter; câu hỏi chính là có nên giữ hay thay core hiện tại.

## Working recommendation after R0

R0 không đủ bằng chứng để phê duyệt một full clean project. Khuyến nghị hiện tại là **clean reasoning core theo strangler pattern**, dùng adapter để tái sử dụng auth, RLS, knowledge store, read tools, approval và audit của hệ thống hiện tại. Không tiếp tục thêm feature vào legacy/Consultant core trước khi có baseline chất lượng, nhưng cũng không viết lại toàn bộ platform.

Clean project không có nghĩa là viết lại mọi thứ hoặc đuổi theo feature parity. Nó phải:

- dùng OSS/runtime SDK cho orchestration, state, tool protocol, tracing và persistence ở nơi thích hợp;
- giữ framework sau adapter để tránh lock-in;
- lấy hệ thống hiện tại làm corpus, failure catalog, benchmark và đối chứng;
- chỉ port thành phần vượt acceptance test;
- xây một vertical slice nhỏ trước khi mở rộng.

## Những gì dự kiến kế thừa

- corpus và tài liệu Bravo đã có;
- benchmark prompt, raw output và failure cases;
- khái niệm RLS/authorization, schema grounding, KEDB, approval và audit;
- metadata, version/environment scope có chất lượng;
- các contract hoặc module độc lập vượt test.

## Những gì không port mặc định

- loop/orchestration legacy chỉ vì nó đang tồn tại;
- JSON-ReAct hoặc agent-step UI không chứng minh tác dụng;
- system prompt khổng lồ;
- heuristic intent/trigger matcher thiếu eval;
- memory hoặc consultant scaffolding chưa chứng minh chất lượng;
- mọi giả thuyết kiến trúc suy ra từ lời tự thuật của BravoGen.

## Vertical slice tối thiểu để ra quyết định

```text
input + image/file
  -> perception / TaskBrief
  -> goal and workflow model
  -> retrieval and read-only tools
  -> business/technical analysis
  -> critic / completeness check
  -> natural answer
  -> multi-turn correction and continuation
```

Vertical slice phải giải được các ca nối nhiều loại tri thức, không chỉ retrieval đơn lẻ.

## Trạng thái

`R0 COMPLETE — R1 PREPARATION` — thiết kế benchmark đã sẵn sàng nhưng execution chưa mở. Hoàn tất documentation cleanup, chụp baseline A/B bất biến và đóng fixture/SME gate trước; sau đó mới xây strangler slice C và quyết định bằng blind bake-off. Xem `02-R1-DECISION-BENCHMARK-PLAN.md`.

Implementation profile tạm chọn cho System C là Pydantic AI làm reasoning runtime trên các adapter/platform BRAVO hiện có. LangGraph là challenger có điều kiện; Kitaru chỉ là replay/durable micro-pilot; ZenML được hoãn cho outer loop offline. Đây là quyết định cho prototype R1, không phải production approval. Xem `03-OSS-CORE-DECISION-PYDANTIC-LANGGRAPH-ZENML-KITARU.md`.

Workspace council đã làm rõ đây là hai track độc lập trong cùng platform, không phải full rewrite hoặc microservice mới. **Conversation Core v2** chịu benchmark hội thoại với BravoGen; **Engineering Workbench** xử lý Layout/SQL/config qua canonical case, workspace cô lập, validator/build/test và handover. Hai track dùng chung foundation nhưng không dùng chung verdict chất lượng. Xem `04-WORKSPACE-REPO-COUNCIL-DECISION.md`, `05-BRAVO-ENGINEERING-WORKBENCH-CONTRACT.md`, `06-RESEARCH-AND-IMPLEMENTATION-ROUNDS.md` và `07-CONVERSATION-INTELLIGENCE-BRAVOGEN-BENCHMARK.md`.
