# Master execution plan

## Nguyên tắc

- Chất lượng câu trả lời hữu ích là mục tiêu chính; citation là công cụ kiểm chứng và debug, không phải lý do để hệ thống từ chối mọi suy luận nghiệp vụ.
- Phân biệt tri thức trực tiếp, suy luận có kiểm soát và điều chưa biết.
- Không dùng BravoGen làm oracle tuyệt đối. BravoGen là một hệ thống đối chứng hành vi.
- Không chốt framework trước khi chốt contract, state model, eval và vertical slice.
- Mỗi phase phải tạo artifact tái sử dụng được và có exit criteria.

## Phase R0 — BravoGen black-box research (`COMPLETE`)

Mục tiêu: làm rõ BravoGen có những năng lực hành vi nào qua ba mode và tạo benchmark sản phẩm.

Thực hiện P0-A đến P0-G trong `bravogen-p0/`. Chưa áp dụng kiến trúc vào BRAVO trong phase này.

Exit criteria:

- đủ ba mode;
- ít nhất 30 test độc lập;
- ít nhất 10 test cross-mode;
- ít nhất 5 fabricated-entity test;
- ít nhất 5 citation audit;
- ít nhất 3 graph traversal test;
- ít nhất 3 context-memory sequence;
- các test quan trọng có tối thiểu 2 phiên độc lập;
- mọi finding có nhãn bằng chứng.

Closure evidence: `bravogen-p0/P0-21-r0c-strict-closure-raw.json` records five anchors × three modes (15/15) plus two completed independent Insight repeats, with no missing records. The formal gate is recorded in `bravogen-p0/P0-20-exit-criteria-audit.md`.

## Phase R1 — Decision benchmark

Chỉ bắt đầu sau R0.

Execution contract: `02-R1-DECISION-BENCHMARK-PLAN.md`.

1. Chọn 15–25 ca đại diện cho chất lượng tư vấn thật: nghiệp vụ nhiều bước, ảnh + yêu cầu kỹ thuật, troubleshooting, schema grounding, issue tương tự và hội thoại sửa điều kiện.
2. Định nghĩa expected outcome theo rubric, không dùng nguyên văn BravoGen làm đáp án vàng.
3. Chạy blind bake-off giữa hệ thống hiện tại, BravoGen và prototype sạch.
4. Đo task completeness, business coherence, factual correctness, assumption control, clarification quality, safety và conversational usefulness.

R1 ở đây chỉ quyết định **Conversation Intelligence Core**. Nó không dùng kết quả build/test của Engineering Workbench để cộng điểm hội thoại. Bộ đầy đủ là 24 trajectory bao phủ 66 lượt; 6 anchor chỉ là development smoke suite.

## Parallel engineering track — BRAVO Engineering Workbench

Track này có gate độc lập và có thể chạy song song sau contract feasibility spike:

- yêu cầu/ảnh/XML → canonical technical case;
- tạo diff trong workspace cô lập;
- parser/schema/lint/compiler/build/test;
- tùy chọn browser test qua adapter;
- developer review và handover;
- không tự sửa customer/production environment.

IDE chỉ là adapter trình bày diff, Task và test result sau khi headless runner hoạt động; không phải execution core. Xem `05-BRAVO-ENGINEERING-WORKBENCH-CONTRACT.md`.

## Phase R2 — Clean vertical-slice prototype

Chỉ thực hiện nếu decision gate cho phép. Dùng OSS/runtime SDK sau adapter và không port feature hàng loạt.

Deliverables:

- conversation API và state rõ ràng;
- input text/image/file;
- TaskBrief có version/module/environment/constraints/unknowns;
- coordinator có workflow state, không chỉ intent label;
- retrieval/schema tools read-only;
- business/technical synthesis;
- critic kiểm tra thiếu bước, giả định và rủi ro;
- trace phục vụ eval;
- multi-turn correction/stop/resume.

## Phase R3 — Architecture decision

So sánh ba lựa chọn:

- tiếp tục legacy;
- clean project dựa trên OSS;
- strangler/hybrid chuyển dần.

Tiêu chí: chất lượng benchmark, độ phức tạp solo-dev, khả năng debug, observability, portability, security, chi phí vận hành và tốc độ thêm nghiệp vụ mới.

## Phase R4 — Knowledge and action expansion

Sau khi core thắng benchmark:

- metadata/version/environment-aware retrieval;
- schema grounding và KEDB/verified resolutions;
- workflow tool với approval;
- durable execution;
- feedback curation có human review;
- action policy và audit.

## Phase R5 — Cutover

- port có chọn lọc auth/RLS/approval/audit;
- shadow traffic và regression suite;
- feature-by-feature cutover;
- archive legacy sau khi rollback window kết thúc.

## Stop conditions

Dừng và xem lại nếu prototype sạch:

- không thắng legacy rõ ràng trên benchmark cốt lõi;
- cần port phần lớn legacy trước khi tạo giá trị;
- framework bắt đầu quyết định domain model;
- chất lượng chỉ tăng do model mạnh hơn nhưng pipeline không debug được;
- không thể truy nguyên lỗi về perception, retrieval, planning, reasoning hay answer synthesis.
