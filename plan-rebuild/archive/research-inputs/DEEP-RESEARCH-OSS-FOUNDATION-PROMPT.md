# Prompt Deep Research — OSS foundation cho BRAVO AI Copilot

> **Status: ARCHIVED RESEARCH INPUT.** Excluded from default AI context. The synthesized outcome
> is preserved in the active decision documents listed by `../../README.md`.

## Cách hiểu lại bài toán

Không giả định tồn tại một repository hoàn chỉnh có thể fork rồi biến thành BRAVO AI Copilot. Hãy nghiên cứu cả:

- repository/framework có thể làm nền;
- các component OSS có thể ghép thành stack;
- reference architecture và pattern đã được kiểm chứng;
- phần nên kế thừa từ dự án BRAVO hiện tại;
- phần cần thiết kế lại vì đang làm giảm chất lượng hội thoại.

BravoGen chỉ là đối chứng hành vi hữu ích, không phải oracle và không được suy đoán kiến trúc nội bộ.

---

## Prompt có thể sao chép vào GPT Deep Research

Tôi đang nghiên cứu hướng xây dựng hoặc tái cấu trúc **BRAVO AI Copilot**, một trợ lý AI cho phần mềm ERP BRAVO 10 và các nghiệp vụ liên quan. Hãy thực hiện một nghiên cứu rộng, có dẫn nguồn, để xác định những nền tảng open-source, repository, reference architecture và pattern phù hợp nhất làm nền cho core/runtime của hệ thống.

### Bối cảnh

Chatbot hiện tại đã có retrieval, API hội thoại, authorization/RLS, một số workflow card, task state, approval, durable checkpoint, schema/KEDB contract và evaluation scaffolding. Tuy nhiên, chất lượng hội thoại chưa đạt yêu cầu: câu trả lời thường diễn đạt lại nội dung tìm được, thiếu khả năng nối mục tiêu người dùng với điều kiện tiên quyết, quy trình nghiệp vụ ERP/kế toán, thao tác BRAVO 10, phân tích ảnh/yêu cầu kỹ thuật, troubleshooting, schema/version và lịch sử issue đã xác minh.

Một hệ thống đối chứng là BravoGen cho thấy một số hành vi đáng học hỏi: phân miền hỗ trợ, liên kết prerequisite nghiệp vụ, hỏi dữ kiện chẩn đoán có giá trị, phân biệt quan hệ trực tiếp/suy luận, giữ context nhiều lượt, từ chối entity không tìm thấy và định tuyến tác vụ rủi ro. Tuy nhiên, BravoGen cũng có câu trả lời thiếu căn cứ hoặc khẳng định schema khi chưa đủ dữ liệu. Không được suy luận rằng BravoGen dùng GraphRAG, multi-agent, workflow engine, tự học từ ticket hay bất kỳ framework cụ thể nào nếu không có bằng chứng công khai.

Đây **không phải** bài toán chọn giữa LangGraph và OpenAI Agents SDK, cũng không mặc định phải dùng multi-agent, GraphRAG hoặc viết lại toàn bộ dự án. Tôi là solo developer nên chi phí tích hợp, khả năng debug, vận hành và phát triển dần rất quan trọng.

### Mục tiêu nghiên cứu

1. Khảo sát landscape hiện tại của các OSS repository/framework/runtime có thể hỗ trợ xây dựng trợ lý domain chuyên sâu, bao gồm nhưng không giới hạn ở orchestration, typed state, durable workflow, retrieval, multimodal input, memory, tool policy/approval, tracing/evaluation, schema grounding và support/KEDB intelligence.
2. Tìm các dự án hoặc pattern giải quyết tốt bài toán **tư vấn theo mục tiêu và quy trình**, thay vì chỉ RAG hỏi–đáp hoặc agent loop chung chung.
3. Phân tích bài học từ các nền tảng/agent frontier và các hệ thống production tương tự: điều gì thực sự cải thiện task completion, điều gì thường tạo complexity nhưng không tăng chất lượng, và các failure mode phổ biến.
4. Đánh giá liệu nên:
   - tiếp tục cải tiến core hiện tại;
   - xây reasoning core mới theo strangler pattern và tái sử dụng platform hiện tại;
   - hay tạo một clean project riêng.
5. Xác định phần nên kế thừa từ dự án BRAVO hiện tại, phần nên thay thế, và phần chưa đủ bằng chứng để giữ hoặc bỏ.
6. Đề xuất một số candidate stack có thể ghép từ nhiều OSS component; không bắt buộc tìm một framework duy nhất làm mọi việc.

### Yêu cầu phương pháp

- Ưu tiên nguồn sơ cấp: repository chính thức, documentation, release notes, issue/discussion quan trọng, engineering blog của đơn vị phát triển và paper gốc.
- Dùng thông tin cập nhật tại thời điểm nghiên cứu; ghi rõ ngày/release được đánh giá.
- Phân biệt rõ: fact quan sát được, suy luận của người nghiên cứu và khuyến nghị.
- Không dùng số sao GitHub làm bằng chứng duy nhất. Xem xét release cadence, maintainer/governance, contributor concentration, issue health, license, backward compatibility, observability, testability và dấu hiệu production adoption.
- Không loại bỏ một dự án chỉ vì nó không phải “agent framework”; workflow engine, retrieval/eval platform, state machine, policy engine hoặc domain-modeling library đều có thể là thành phần phù hợp.
- Cảnh báo rõ các repository demo, benchmark marketing, dự án ít bảo trì hoặc kiến trúc tạo lock-in cao.
- Không đề xuất live fallback/token rotation sang BravoGen hoặc tự động ingest câu trả lời ngoài vào knowledge base. Nếu nghiên cứu external expert/knowledge acquisition, phải đặt nó sau privacy, provenance và human verification gate.

### Những năng lực sản phẩm cần làm tiêu chí tham chiếu

Danh sách này nhằm định hướng, không giới hạn phạm vi khám phá:

- hiểu mục tiêu và trạng thái công việc của người dùng;
- nối prerequisite nghiệp vụ với thao tác ERP cụ thể;
- phân tích text, ảnh và file thành task brief;
- hỏi làm rõ theo giá trị thông tin;
- retrieval có metadata/version/environment và schema grounding;
- tìm issue tương tự nhưng phân biệt version/nguyên nhân/resolution;
- phân biệt fact, inference và unknown mà vẫn trả lời hữu ích;
- tool execution có draft, approval, audit và resume;
- hội thoại sửa điều kiện, dừng/tiếp tục và không trộn task;
- trace/evaluation đủ để biết lỗi nằm ở perception, retrieval, planning, reasoning, tool hay answer synthesis.

### Kết quả mong muốn

Hãy trả về một decision pack bằng tiếng Việt gồm:

1. **Executive recommendation**: hướng kiến trúc đáng thử nhất và lý do.
2. **Landscape map**: các nhóm giải pháp và repository nổi bật; không chỉ liệt kê agent framework.
3. **Shortlist có chiều sâu**: một số repo/component hoặc candidate stack phù hợp nhất, kèm điểm mạnh, giới hạn, license, độ trưởng thành, rủi ro và vai trò dự kiến trong BRAVO.
4. **Salvage/replace map**: phần nào của hệ thống hiện tại nên reuse, wrap qua adapter, viết lại hoặc loại bỏ; nêu điều kiện bằng chứng trước khi quyết định.
5. **So sánh ba chiến lược**: continue/fix, strangler reasoning core và full clean project trong bối cảnh solo developer.
6. **Failure modes và anti-patterns** từ các hệ thống frontier/production mà dự án nên tránh.
7. **Đề xuất thử nghiệm nhỏ để ra quyết định**: cách so sánh current system với candidate core bằng cùng model, cùng evidence và benchmark hội thoại; không cần lập kế hoạch triển khai sản phẩm đầy đủ.
8. **Open questions**: các thông tin còn thiếu có thể làm thay đổi khuyến nghị.

Mỗi khuyến nghị quan trọng phải có link nguồn trực tiếp. Nếu không có đủ bằng chứng về production maturity hoặc tác động chất lượng, hãy nói rõ là chưa xác minh. Mục tiêu cuối cùng không phải chọn framework nổi tiếng nhất, mà là tìm kiến trúc có khả năng tạo câu trả lời thực sự hiểu BRAVO/ERP, dễ debug và khả thi cho một solo developer phát triển dần.

---

## Tài liệu nội bộ nên đính kèm nếu Deep Research hỗ trợ upload

Không bắt buộc đính kèm toàn bộ repository. Ưu tiên:

1. `00-CURRENT-REBUILD-DECISION.md`;
2. `02-R1-DECISION-BENCHMARK-PLAN.md`;
3. `bravogen-p0/P0-23-r0-post-analysis.md`;
4. `docs/CONSULTANT-INTELLIGENCE-IMPLEMENTATION.md`;
5. một sơ đồ module hoặc danh sách component hiện tại;
6. 3–6 benchmark anchor tiêu biểu thay vì toàn bộ raw conversation.

Một upload pack tự chứa đã được chuẩn bị tại `DEEP-RESEARCH-UPLOAD-PACK.md`; file này gộp sơ đồ module, component inventory, reuse hypothesis và sáu benchmark anchor, nên có thể dùng thay cho việc upload nhiều file kỹ thuật ở vòng đầu.

Nếu không thể upload file, phần “Bối cảnh” trong prompt đã đủ để bắt đầu nghiên cứu; có thể bổ sung code/repo ở vòng research thứ hai sau khi shortlist ban đầu xuất hiện.
