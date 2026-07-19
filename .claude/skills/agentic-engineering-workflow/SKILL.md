---
name: agentic-engineering-workflow
description: "Turn ambiguous features, complex bugs, remediation work, and architectural changes into an aligned, vertically sliced, test-driven implementation workflow with explicit verification and independent review. Use when asked to plan or implement substantial multi-file work, convert a PRD or audit finding into executable tasks, remediate pilot blockers, or organize autonomous AI coding work. Do not trigger for trivial, isolated edits or simple factual questions. Triggers: feature lớn, thay đổi kiến trúc, remediation, pilot blocker, phân rã công việc, vertical slice, PRD, grill me, alignment, quy trình triển khai."
---

# agentic-engineering-workflow

Biến một yêu cầu còn mơ hồ (feature mới, bug phức tạp, remediation item, thay đổi kiến trúc) thành quy trình có kiểm soát:

> Yêu cầu → Làm rõ & đồng bộ nhận thức → Decision brief/PRD → Vertical slices → Triển khai TDD → Kiểm tra tự động → Review độc lập → QA & đóng công việc.

Mục tiêu: làm việc có kỷ luật, không "vibe coding", không nhận một yêu cầu lớn rồi tự suy đoán và sửa hàng loạt.

**Progressive disclosure:** file này chứa workflow và quy tắc cốt lõi. Template chi tiết nằm trong `references/` — chỉ đọc khi bước tương ứng thực sự cần.

## Bước 0 — Phân loại nhiệm vụ

KHÔNG ép mọi nhiệm vụ trải qua quy trình dài. Phân loại trước:

### Loại A — Nhỏ và rõ ràng
Sửa typo, đổi nhãn UI, sửa lỗi cục bộ đã rõ nguyên nhân, chỉnh config đơn giản.
- Không tạo PRD. Không phỏng vấn dài.
- Xác nhận phạm vi trong 1–2 câu, triển khai và kiểm tra trực tiếp.

### Loại B — Vừa, còn vài điểm chưa rõ
- Khảo sát codebase trước, nêu giả định.
- Chỉ hỏi những câu **có khả năng thay đổi implementation** (thường 3–10 câu quan trọng).
- Hỏi từng câu một nếu quyết định sau phụ thuộc câu trả lời trước.
- Đầu ra: decision brief ngắn (có thể chỉ là một đoạn trong reply), rồi triển khai.

### Loại C — Feature lớn, kiến trúc, bảo mật, remediation phức tạp
- Chạy đầy đủ: Alignment (Grill Me) → PRD/remediation brief → vertical slices → dependency graph → TDD → review độc lập.
- **Chưa triển khai** nếu còn quyết định quan trọng chưa được giải quyết.

Dừng phỏng vấn khi đã đủ thông tin để triển khai an toàn — không phải khi đạt một số lượng câu hỏi tùy ý.

## Bước 1 — Alignment / "Grill Me" (Loại B, C)

1. Khảo sát code và tài liệu liên quan **trước khi hỏi**. Không hỏi lại thông tin xác định được từ workspace.
2. Lập cây quyết định nội bộ về: mục tiêu · actor · luồng nghiệp vụ · dữ liệu · phân quyền · bảo mật · migration/backward compatibility · failure modes · observability · kiểm thử · rollback · out-of-scope.
3. Với mỗi câu hỏi: giải thích ngắn tác động, đưa phương án khuyến nghị, nêu trade-off nếu cần. Dùng AskUserQuestion khi phù hợp. Không hỏi câu hình thức.
4. Ghi lại quyết định đã xác nhận. Phân biệt rõ 4 loại thông tin:
   - **Fact** — lấy từ code/tài liệu (kèm `path:line`).
   - **Decision** — người dùng đã chốt.
   - **Assumption** — giả định của agent, phải nêu công khai.
   - **Unknown** — chưa đủ bằng chứng.
5. KHÔNG tự quyết thay người dùng đối với: thay đổi kiến trúc lớn, quy tắc nghiệp vụ, bảo mật, xóa/migration dữ liệu, public API, chi phí vận hành đáng kể.

Đầu ra của alignment là một **shared design concept**, không phải danh sách câu hỏi.

## Bước 2 — Destination document

Chọn tài liệu **nhỏ nhất** phù hợp:
- Loại A: không tạo tài liệu.
- Loại B: decision brief ngắn.
- Loại C feature: PRD — đọc `references/prd-template.md`.
- Loại C audit finding / pilot blocker: remediation brief (dùng cùng template, nhấn mạnh evidence và exit criteria).

PRD mô tả **đích đến và ràng buộc đã xác nhận** — không phải nhật ký hội thoại.

## Bước 3 — Phân rã bằng vertical slices

KHÔNG mặc định chia theo tầng ngang (toàn bộ DB → toàn bộ backend → toàn bộ frontend).

Mỗi issue là một **vertical slice**: hành vi nhỏ nhưng hoàn chỉnh, quan sát được, kiểm thử độc lập được.

Một slice tốt: có giá trị/hành vi quan sát được · đi qua đúng những tầng cần thiết · phạm vi nhỏ · acceptance criteria rõ · có test/verification tương ứng · review độc lập được · vừa một context làm việc tập trung · không phụ thuộc ngầm vào issue khác.

- Tốt: "Sau khi người dùng upload hoá đơn hợp lệ, hệ thống tạo đúng một bản ghi nháp cân Nợ=Có, lưu audit record và hiển thị trong drafts queue."
- Không tốt: "Xây toàn bộ database cho module X."

Khi viết issue, đọc `references/issue-template.md`. Mỗi issue phải có: ID/tiêu đề · outcome quan sát được · scope/out-of-scope · dependencies · files dự kiến · acceptance criteria · test plan · verification commands · security/data considerations · completion evidence · trạng thái (ready/blocked/in progress/completed) · execution mode (human-in-loop hay AFK-safe).

## Bước 4 — Dependency graph & song song hoá

1. Xác định quan hệ phụ thuộc giữa các issue; đánh dấu foundation / blocked / AFK-safe / cần con người.
2. Chỉ đánh dấu song song khi các issue **thực sự độc lập**. Không cho nhiều agent cùng sửa một module trung tâm nếu chưa có chiến lược tích hợp (dùng worktree isolation nếu bắt buộc).
3. Không song song hoá chỉ để tăng tốc nếu tăng rủi ro merge hoặc phân mảnh kiến trúc.
4. Không tự spawn sub-agent trừ khi người dùng hoặc chỉ dẫn workspace cho phép.

## Bước 5 — Triển khai từng issue

1. Bắt đầu từ trạng thái repo hiện tại; kiểm tra working tree, bảo vệ thay đổi có sẵn của người dùng.
2. Đọc đúng phần code liên quan; xác nhận issue không còn blocked.
3. Ưu tiên **TDD**:
   - Viết test phản ánh hành vi mong muốn.
   - Xác nhận test **thất bại vì đúng lý do**.
   - Viết code tối thiểu để pass. Refactor khi test vẫn xanh.
4. KHÔNG viết test chỉ để khớp implementation hiện tại. KHÔNG làm yếu test, bỏ test, hay hạ acceptance criteria để đạt pass.
5. Chạy các feedback loop phù hợp với repo: unit tests · integration tests · type check · lint · format check · security checks · migration checks · build.
6. Không tuyên bố hoàn thành nếu chưa có bằng chứng. Nếu không chạy được một kiểm tra nào đó, nói rõ: kiểm tra nào chưa chạy, vì sao, rủi ro còn lại.

### Kiến trúc deep-module
- Ưu tiên module có interface nhỏ đóng gói logic đáng kể; tránh rải hàng loạt helper/file nhỏ chỉ vì "single responsibility".
- Không refactor kiến trúc ngoài phạm vi issue. Phát hiện shallow-module cluster → ghi thành issue riêng, trừ khi sửa là điều kiện bắt buộc của feature hiện tại.
- Giữ theo convention của codebase; không áp dụng "deep module" máy móc.

### Frontend/UI
- Build thành công KHÔNG phải bằng chứng UI đúng.
- Kiểm tra loading/empty/error/success states; responsive nếu liên quan; chạy component/E2E test khi có.
- Yêu cầu human visual QA khi không có công cụ kiểm tra trực quan đáng tin cậy. Không tuyên bố UI "đẹp"/"đúng thiết kế" nếu chưa quan sát.

## Bước 6 — Review độc lập

1. Ưu tiên review bằng context sạch (sub-agent reviewer hoặc `/code-review`) nếu môi trường cho phép; nếu không, self-review có cấu trúc và **công khai giới hạn này**.
2. Reviewer chỉ nhận: yêu cầu đã xác nhận · acceptance criteria · diff · test evidence · phần code liên quan. Không bắt reviewer lặp lại hành trình triển khai.
3. **Review test trước implementation**: test kiểm tra đúng hành vi không? có thất bại trước khi sửa không? có sót negative/boundary case không?
4. Sau đó review theo `references/review-checklist.md`. Phân loại finding theo severity và evidence.

## Bước 7 — Handoff & context hygiene

Khi một issue hoàn thành hoặc context quá lớn / chất lượng suy luận giảm:
- Ghi handoff ngắn theo `references/handoff-template.md`: mục tiêu · quyết định đã chốt · thay đổi đã làm · test evidence · vấn đề còn lại · issue tiếp theo · file cần đọc.
- Không sao chép lịch sử hội thoại. Ngưỡng token chỉ là heuristic, không phải quy luật cứng.

## Bước 8 — Documentation hygiene & đóng công việc

- Xác định source of truth; cập nhật tài liệu vận hành nếu hành vi đã thay đổi.
- Đánh dấu tài liệu kế hoạch là completed/superseded/archived — không để PRD cũ trông như tài liệu hiện hành.
- Không xóa artifact có giá trị kiểm toán khi chưa được phép.
- QA finding chưa xử lý → tạo issue mới. Không che giấu unresolved risks.

## Quy tắc riêng khi workspace là dự án BRAVO (áp dụng có điều kiện)

Nếu repo hiện tại là BRAVO AI Copilot (có `CLAUDE.md` với 4 nguyên tắc bất biến):

- Mọi slice phải tôn trọng 4 bất biến: RLS lọc ở tầng SQL · non-invasive (chỉ draft, không ghi thẳng ERP) · zero hallucination số liệu (có nguồn mới nói) · offline-capable mặc định.
- Chuyển audit finding thành remediation task với phân loại rõ: **Confirmed finding** / **Need more evidence** / **Downgraded-rejected** / **Pilot blocker**.
- Yêu cầu **evidence trước khi đóng blocker**. Với database isolation / tenant / RLS, kiểm tra ĐỦ các entry point: HTTP request · agent execution · MCP · background worker · connection pool/session reuse. Không đánh dấu blocker đã đóng chỉ vì sửa một code path.
- Thay đổi chạm phân quyền → chạy `/rls-check`; quyết định kiến trúc lớn → ghi ADR (`/adr-new`); thẩm định đa chiều → `/council-review`.
- Tài liệu nghiệp vụ viết tiếng Việt, thuật ngữ kỹ thuật giữ tiếng Anh.

Nếu workspace không phải BRAVO, bỏ qua mục này và giữ nguyên phần workflow chung.
