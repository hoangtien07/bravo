# Current state và failure analysis

## 1. Kết luận audit

Chatbot hiện tại chủ yếu thực hiện tốt chuỗi:

`nhận câu hỏi → route corpus → retrieve đoạn văn → tạo câu trả lời có kiểm soát`.

Bài toán người dùng cần lại là:

`hiểu kết quả cần đạt → dựng trạng thái nghiệp vụ → lập workflow → tra từng điểm chưa biết → hướng dẫn/điều phối đến kết quả`.

Khoảng cách giữa hai chuỗi này giải thích tại sao tăng tài liệu hoặc đổi prompt không đủ.

## 2. Những gì repo đã có và nên giữ

- `app/rag/knowledge_router.py` định tuyến playbook/source/module trước retrieval, giảm cạnh tranh sai
  miền tri thức.
- `file_system/bravo_lifecycle_playbooks.yaml` có profile, source preference và output contract.
- `app/agent/loop.py` có structured decision, budget, tool boundary, financial verification và
  các guardrail về grounded/un-grounded content.
- `app/eval/golden.py` đã đặt nền trajectory/tool/citation/security evaluation.
- `app/eval/bravo_lifecycle.py` kiểm tra source/module routing.
- `docs/CORPUS-OPS.md` đã có vòng lặp zero-hit, dislike, abstain và triage corpus.
- Runtime/control-plane decisions trong pack 2026-07-13 vẫn cần giữ.

Các tài sản này là nền tốt. Vấn đề là chúng bảo vệ và vận hành một answer pipeline, chưa mô hình hóa
công việc của tư vấn viên.

## 3. Root-cause tree

### RC-1 — Không có biểu diễn mục tiêu nghiệp vụ

Intent hiện tại thường là nhãn route như `end_user_guidance` hoặc `technical_impact`. Nhãn này nói
**nên tìm ở đâu**, không nói **người dùng muốn trạng thái cuối nào**.

“Lên BCTC”, “số dư không đúng”, “hóa đơn chưa vào công nợ” có thể cùng chạm phân hệ kế toán nhưng
có goal, prerequisite, evidence và next action hoàn toàn khác. Khi không có `GoalFrame`, model dễ
bám từ khóa nổi bật và trả thao tác bề mặt.

### RC-2 — Tri thức là nội dung, chưa là mô hình thực hiện công việc

Tài liệu hướng dẫn tối ưu cho người đã biết nghiệp vụ và muốn tìm menu. Nó thường không biểu diễn:

- precondition/postcondition;
- nhánh theo loại chứng từ, kỳ, version, cấu hình;
- dependency giữa phân hệ;
- checkpoint đối chiếu;
- triệu chứng → giả thuyết → evidence → resolution;
- bước nào chỉ tư vấn, bước nào có thể đọc hệ thống, bước nào cần approval.

RAG tìm được đoạn “Mở Báo cáo tài chính” không thể tự đảm bảo model suy ra đầy đủ quy trình khóa sổ.

### RC-3 — Query planning thiên về câu chữ

Query rephrase/decomposition hiện tại hữu ích cho recall nhưng chưa sinh ra một `business plan`.
Không có node “kiểm tra chứng từ chưa ghi sổ”, “đối chiếu tài khoản”, “kết chuyển” để retrieval phục
vụ theo node. Vì thế retrieval có thể rất liên quan về ngữ nghĩa nhưng thiếu prerequisite quyết định.

### RC-4 — Transcript bị dùng thay cho task state

Lịch sử hội thoại lưu câu chữ, nhưng chưa có ledger chuẩn cho:

- facts đã xác nhận;
- assumption đang dùng;
- constraint bị thay đổi;
- câu hỏi còn mở;
- plan node đã hoàn tất;
- contradiction và fact bị supersede.

Test nhiều lượt hiện mới chứng minh text cũ xuất hiện trong context; chưa chứng minh agent giữ đúng
ý định sau correction hoặc thay đổi kế hoạch.

### RC-5 — Abstention policy tối ưu evidence hơn helpfulness

Guardrail “không có grounded context thì từ chối” ngăn bịa dữ liệu nội bộ, nhưng gom ba tình huống
khác nhau thành một:

1. model biết quy trình nghiệp vụ phổ quát và có thể giúp;
2. model chưa biết tên menu BRAVO chính xác nhưng có thể đưa kế hoạch và hỏi version;
3. fact chỉ tồn tại trong schema/môi trường khách hàng và thực sự không được đoán.

Hậu quả là hệ thống hoặc từ chối quá sớm, hoặc khi cố hữu ích lại có nguy cơ specificity không nguồn.

### RC-6 — Eval đo component, chưa đo kết quả tư vấn

Routing đúng source, gọi đúng tool, có citation và không vi phạm policy là điều kiện cần. Chúng không
phát hiện câu trả lời “mở báo cáo” đã bỏ qua toàn bộ chuẩn bị dữ liệu. Thiếu:

- goal state/milestone kỳ vọng;
- prerequisite bắt buộc và forbidden premature actions;
- simulated user có thể sửa facts hoặc thực hiện action;
- chấm plan repair và coordination;
- error attribution riêng cho planner, retrieval, memory và composer.

### RC-7 — Feedback loop chưa tạo domain artifacts

Zero-hit/dislike hiện dẫn đến bổ sung tài liệu. Nhưng nhiều gap không phải “thiếu đoạn văn”; đó là
thiếu workflow relation, diagnostic split hoặc action mapping. Ingest thêm tài liệu mà không chuyển
thành artifact phù hợp sẽ lặp lại lỗi.

## 4. Failure taxonomy dùng cho Phase 0

| Mã | Failure | Ví dụ | Owner chính |
|---|---|---|---|
| F-GOAL | Hiểu sai/mất mục tiêu | coi “lên BCTC” là mở màn hình | planner/product |
| F-PREQ | Bỏ prerequisite | không kiểm tra hạch toán/kết chuyển | domain knowledge |
| F-BRANCH | Chọn nhánh khi thiếu discriminator | hướng dẫn một loại hóa đơn khi chưa hỏi loại | planner |
| F-ACTION | Mapping nghiệp vụ → BRAVO sai | menu/config/version sai | ActionMap/corpus |
| F-RETRIEVE | Context cần thiết không được lấy | thiếu tài liệu close period | retrieval |
| F-CONTEXT | Context có nhưng model bỏ qua | fact nằm giữa context dài | context compiler |
| F-STATE | Quên correction/constraint | tiếp tục dùng kỳ cũ | task state |
| F-DIAG | Nhảy từ triệu chứng tới resolution | chưa kiểm tra log/version | KEDB/diagnostic |
| F-SPEC | Khẳng định cụ thể không có bằng chứng | bịa bảng/field/case ID | composer/critic |
| F-CLARIFY | Hỏi quá nhiều/không phân biệt nhánh | hỏi version dù không ảnh hưởng | policy |
| F-REFUSE | Từ chối dù có thể giúp | không citation nên dừng | answer policy |
| F-TOOL | Gọi tool sai/thừa | query DB khi chỉ cần giải thích | capability router |
| F-SAFETY | Hành động vượt authority | đưa script chạy production | control plane |
| F-COORD | Không thích nghi với user action | user đã sửa nhưng agent lặp bước | interaction loop |

Mỗi failure record phải gắn `turn_id`, `goal_id`, `plan_node_id`, input context, retrieved artifacts,
tool trace, output, rubric label và người duyệt. Không chỉ lưu thumbs-down.

## 5. Hai case chuẩn để kiểm tra kiến trúc

### Case A — Lập báo cáo tài chính

Một plan tối thiểu phải cân nhắc, không nhất thiết hỏi hết ngay:

1. công ty/kỳ/đơn vị/cơ sở lập và version/config BRAVO;
2. chứng từ các phân hệ đã hoàn tất và ghi sổ chưa;
3. các bút toán định kỳ: phân bổ, khấu hao, chênh lệch tỷ giá, dự phòng/giá thành nếu áp dụng;
4. đối chiếu tiền, công nợ, tồn kho, tài sản, thuế và sổ cái;
5. bút toán kết chuyển/khóa kỳ theo chính sách doanh nghiệp;
6. mapping/chỉ tiêu/công thức báo cáo;
7. lập báo cáo, kiểm tra cân đối và drill-down chênh lệch.

Agent không nên trình bày toàn bộ checklist nếu người dùng chỉ hỏi một bước, nhưng `TaskState` phải
biết người dùng đang ở milestone nào. Tên bước/màn hình BRAVO cụ thể phải được tra theo version.

### Case B — Hóa đơn đầu vào chưa lên công nợ/BCTC

Agent phải tách ít nhất: hóa đơn đã nhập chưa; chứng từ có ghi sổ không; tài khoản/đối tượng/thuế có
mapping đúng không; kỳ/ngày hạch toán; trạng thái duyệt; nguồn e-invoice/integration; báo cáo đang
lọc theo đơn vị/chi nhánh nào. “Nhập lại hóa đơn” hoặc “refresh báo cáo” trước khi phân biệt các nhánh
là resolution prematurity.

## 6. Những cách sửa không đủ

- **Đổi model:** có thể tăng reasoning chung nhưng không tạo environment facts hay workflow chuẩn.
- **Prompt dài hơn:** làm tăng context competition và khó quan sát; không thay domain state.
- **Ingest nhiều PDF hơn:** tăng recall nội dung, không đảm bảo dependency/prerequisite.
- **GraphRAG ngay:** graph retrieval không tự tạo đúng ontology/workflow hoặc task policy.
- **Multi-agent mặc định:** thêm coordination/context/cost; task ERP nhiều bước phụ thuộc trạng thái.
- **Fine-tune transcript BravoGen:** mang theo hallucination, thiếu provenance và behavior không kiểm soát.
- **Fallback âm thầm sang BravoGen:** che gap, tạo dependency và biến output bên ngoài thành truth.

## 7. Giả thuyết cần kiểm chứng

H1. Typed goal/workflow artifacts tăng prerequisite recall nhiều hơn tăng top-k hoặc prompt length.  
H2. Context compiler + task state tăng correction retention hơn raw-history window.  
H3. Two-pass retrieval tăng task success dù số chunk tổng thấp hơn.  
H4. Specialist-as-tools tốt hơn multi-agent handoff cho workflow phụ thuộc trạng thái.  
H5. External expert có lift ở gap thật, nhưng lift ròng chỉ dương khi redaction, review và latency được
tính đầy đủ.  
H6. Citation nhẹ ở UX nhưng provenance đầy đủ ở trace đạt cân bằng helpfulness/safety tốt hơn policy
abstain cứng.

Mọi phase bên dưới được thiết kế để bác bỏ hoặc xác nhận các giả thuyết này, không mặc định chúng đúng.

